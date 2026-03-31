from django import forms
from .models import Task, TaskComment, TaskAttachment
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import os

class TaskForm(forms.ModelForm):
    CHANGE_REQUEST_CHOICES = [
        ('', '--- Select Type ---'),
        ('MAJOR', 'MAJOR'),
        ('MINOR', 'MINOR'),
    ]

    # We can define the field explicitly to ensure it's a ChoiceField (dropdown)
    change_request_type = forms.ChoiceField(
        choices=CHANGE_REQUEST_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    days = forms.DecimalField(
                    max_digits=5, 
                    decimal_places=2, 
                    widget=forms.NumberInput(attrs={'step': '0.1', 'min': '0.1','class':'form-control'})
                )
    
    filter_projects = forms.ModelMultipleChoiceField(
        queryset=Task.objects.none(), 
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select select2', 'placeholder': 'Filter by Projects'})
    )
    
    class Meta:
        model = Task
        fields = ['title', 'change_request_no','dependencies', 'dependency_remark','change_request_type','description','days' ,'project', 'assigned_to', 'status', 'priority', 'progress', 'due_date', 'estimated_hours', 'actual_hours', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title',
                'required': True
            }),
            # 3. Widget for Change Request Type (Dropdown)
            'change_request_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            # 2. Added widget for Change Request No
            'change_request_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., KUTOUR-001'
            }),
            
            'dependencies': forms.SelectMultiple(attrs={
                'class': 'form-select select2',
                'id': 'id_dependencies'
            }),

            'dependency_remark': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Explain why this task is waiting...'
            }),
            
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task description (optional)',
                'rows': 4
            }),
            'project': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select',
                'required': False
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'progress': forms.NumberInput(attrs={
                'class': 'form-range beautiful-range',
                'type': 'range',
                'min': '0',
                'max': '100',
                'oninput': 'this.nextElementSibling.value = this.value + "%"',
                # 'value': '0',
                # 'placeholder': 'Progress %',
                'step': '5'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hours (optional)',
                'step': '0.5'
            }),
            'actual_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hours spent (optional)',
                'step': '0.5'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Comma-separated tags (optional)'
            }),
        }

    def clean_dependencies(self):
        dependencies = self.cleaned_data.get('dependencies')
        if self.instance.pk and dependencies:
            if self.instance in dependencies:
                raise forms.ValidationError("A task cannot depend on itself.")
            
            # Simple Circular Check: B depends on A, so A cannot depend on B.
            for dep in dependencies:
                if dep.dependencies.filter(pk=self.instance.pk).exists():
                    raise forms.ValidationError(
                        f"Circular dependency: '{dep.title}' already depends on this task."
                    )
        return dependencies
    
    def clean_days(self):
        days = self.cleaned_data.get('days')
        if days is None:
            raise forms.ValidationError("Please enter the number of days.")
        if days < 0.1:
            raise forms.ValidationError("Days must be at least 0.1 (approx. 1 hour).")
        return days

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        from projects.models import Project  # This must be here!
        from django.contrib.auth.models import User
        
        # 1. Initialize Filter Projects field based on user access
        # if self.user:
        #     if self.user.is_superuser or self.user.profile.role in ['admin', 'manager', 'observer']:
        #         self.fields['filter_projects'].queryset = Project.objects.all().order_by('title')
        #         self.fields['project'].queryset = Project.objects.all().order_by('title')
        #     else:
        #         self.fields['filter_projects'].queryset = Project.objects.filter(team_members=self.user).order_by('title')
        #         self.fields['project'].queryset = Project.objects.filter(team_members=self.user).order_by('title')

        if self.user:
            is_privileged = self.user.is_superuser or self.user.profile.role in ['admin', 'manager', 'observer']
            
            if is_privileged:
                # Observers see ALL projects, just like Admins
                project_qs = Project.objects.all().order_by('title')
            else:
                # Developers only see projects they are assigned to
                project_qs = Project.objects.filter(team_members=self.user).order_by('title')
            
            self.fields['filter_projects'].queryset = project_qs
            self.fields['project'].queryset = project_qs
                

        # 2. Logic for Dependencies Queryset
        # If we are submitting data (POST), use the filter_projects selection
        if self.data.getlist('dependencies'):
            # Allow the specific IDs submitted to pass validation
            dep_ids = self.data.getlist('dependencies')
            self.fields['dependencies'].queryset = Task.objects.filter(id__in=dep_ids)
        
        # Else if we have filter_projects selected (AJAX context or re-render)
        elif self.data.getlist('filter_projects'):
            p_ids = self.data.getlist('filter_projects')
            self.fields['dependencies'].queryset = Task.objects.filter(project_id__in=p_ids)
            
        # Else if we are editing an existing task
        elif self.instance.pk:
            linked_project_ids = self.instance.dependencies.values_list('project_id', flat=True).distinct()
            self.initial['filter_projects'] = list(linked_project_ids)

            self.fields['dependencies'].queryset = Task.objects.filter(
                project=self.instance.project
            ).exclude(pk=self.instance.pk)
        
        else:
            self.fields['dependencies'].queryset = Task.objects.none()
            

        # 3. Logic for Project and Assigned To (Role Based)
        instance_project = None
        if self.instance.pk:
            try:
                instance_project = self.instance.project
            except ObjectDoesNotExist:
                instance_project = None

        project_id = (
            self.data.get('project') or 
            self.initial.get('project') or 
            (instance_project.id if instance_project else None)
        )

        if project_id:
            # Handle both object and ID cases
            project_obj = Project.objects.filter(pk=project_id).first() if isinstance(project_id, (int, str)) else project_id
            
            if project_obj:
                # Visual lock for project field
                self.fields['project'].widget.attrs.update({
                    'readonly': 'readonly',
                    'style': 'pointer-events: none; background-color: #e9ecef;',
                    'tabindex': '-1'
                })
                
                # Filter team members
                team_member_ids = list(project_obj.team_members.values_list('id', flat=True))
                allowed_user_ids = set(team_member_ids)

                if self.user and self.user.profile.role not in ['admin', 'manager']:
                    superusers = User.objects.filter(is_superuser=True).values_list('id', flat=True)
                    allowed_user_ids = allowed_user_ids - set(superusers)

                if self.instance.pk and self.instance.assigned_to:
                    allowed_user_ids.add(self.instance.assigned_to.pk)

                self.fields['assigned_to'].queryset = User.objects.filter(id__in=allowed_user_ids).order_by('username')
        else:
            self.fields['assigned_to'].queryset = User.objects.none()
            self.fields['assigned_to'].help_text = "Select a project first."


    # ## 9-3-2026 MONDAY
    # def __init__(self, *args, **kwargs):
    #     # 1. Capture the requesting user passed from the view
    #     self.user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)
        
    #     # Capture Project ID safely
    #     instance_project = None
    #     self.fields['dependencies'].queryset = Task.objects.all()
    #     if self.instance.pk:
    #         self.fields['dependencies'].queryset = Task.objects.exclude(pk=self.instance.pk)
    #         try:
    #             instance_project = self.instance.project
    #         except ObjectDoesNotExist:
    #             instance_project = None

    #     project_id = (
    #         self.data.get('project') or 
    #         self.initial.get('project') or 
    #         (instance_project.id if instance_project else None)
    #     )

    #     if project_id:
    #         from projects.models import Project
    #         # Ensure we have a project object
    #         project_obj = Project.objects.filter(pk=project_id).first() if isinstance(project_id, (int, str)) else project_id

    #         if project_obj:
    #             self.fields['project'].widget.attrs.update({
    #                 'readonly': 'readonly',
    #                 'style': 'pointer-events: none; background-color: #e9ecef;',
    #                 'tabindex': '-1'
    #             })
                
    #             # --- FIXING THE ROLE-BASED FILTERING ---
    #             # Get the IDs of the team members
    #             team_member_ids = list(project_obj.team_members.values_list('id', flat=True))
                
    #             # Start building the final list of allowed IDs
    #             allowed_user_ids = set(team_member_ids)

    #             if self.user:
    #                 is_privileged = self.user.profile.role in ['admin', 'manager']
    #                 if not is_privileged:
    #                     # Find superusers to exclude
    #                     superusers = User.objects.filter(is_superuser=True).values_list('id', flat=True)
    #                     allowed_user_ids = allowed_user_ids - set(superusers)

    #             # Safety Net: ALWAYS include the currently assigned user to avoid wiping them out
    #             if self.instance.pk and self.instance.assigned_to:
    #                 allowed_user_ids.add(self.instance.assigned_to.pk)

    #             # Set the queryset using the combined list of IDs
    #             self.fields['assigned_to'].queryset = User.objects.filter(id__in=allowed_user_ids).order_by('username')
    #             self.fields['assigned_to'].help_text = "Only project members can be assigned."
    #     else:
    #         self.fields['assigned_to'].queryset = User.objects.none()
    #         self.fields['assigned_to'].help_text = "Select a project first."

    #     from projects.models import Project  # Safe local import
        
    #     if self.user and self.user.is_superuser:
    #         self.fields['filter_projects'].queryset = Project.objects.all()
    #     elif self.user:
    #         # Show only projects the user is a member of
    #         self.fields['filter_projects'].queryset = Project.objects.filter(team_members=self.user)
    #     else:
    #         self.fields['filter_projects'].queryset = Project.objects.none()
        

    # ------this one at 7:06 2 march
    # def __init__(self, *args, **kwargs):
    #     # 1. Capture the requesting user passed from the view
    #     self.user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)
        
    #     # Capture Project ID safely (Existing code)
    #     instance_project = None
    #     if self.instance.pk:
    #         try:
    #             instance_project = self.instance.project
    #         except ObjectDoesNotExist:
    #             instance_project = None

    #     project_id = (
    #         self.data.get('project') or 
    #         self.initial.get('project') or 
    #         (instance_project.id if instance_project else None)
    #     )

    #     if project_id:
    #         from projects.models import Project
    #         project_obj = Project.objects.filter(pk=project_id).first() if isinstance(project_id, (int, str)) else project_id

    #         if project_obj:
    #             # Visually lock the project field
    #             self.fields['project'].widget.attrs.update({
    #                 'readonly': 'readonly',
    #                 'style': 'pointer-events: none; background-color: #e9ecef;',
    #                 'tabindex': '-1'
    #             })
                
    #             # --- START NEW ROLE-BASED FILTERING ---
                
    #             # Base queryset: everyone in the project
    #             assignee_qs = project_obj.team_members.all().distinct()

    #             if self.user:
    #                 # Rule: If user is NOT a Manager/Admin, hide Superusers from the project list
    #                 is_privileged = self.user.profile.role in ['admin', 'manager']
                    
    #                 if not is_privileged:
    #                     assignee_qs = assignee_qs.exclude(is_superuser=True)

    #             # Safety Net: If the task is already assigned to an Admin, 
    #             # we MUST keep them in the list so the current user doesn't wipe them out.
    #             if self.instance.pk and self.instance.assigned_to:
    #                 assignee_qs = (assignee_qs | User.objects.filter(pk=self.instance.assigned_to.pk)).distinct()

    #             self.fields['assigned_to'].queryset = assignee_qs.order_by('username')
    #             self.fields['assigned_to'].help_text = f"Only project members can be assigned. (Admin hidden for non-managers)"
                
    #             # --- END NEW ROLE-BASED FILTERING ---
    #     else:
    #         self.fields['assigned_to'].queryset = User.objects.none()
    #         self.fields['assigned_to'].help_text = "Select a project first to see available team members."









    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        
    #     # 1. Capture Project ID safely from POST data, initial (URL), or existing instance
    #     # We use getattr to avoid RelatedObjectDoesNotExist on new instances
    #     instance_project = None
    #     if self.instance.pk: # Only check instance if it's an existing record (UpdateView)
    #         try:
    #             instance_project = self.instance.project
    #         except (ObjectDoesNotExist):
    #             instance_project = None

    #     project_id = (
    #         self.data.get('project') or 
    #         self.initial.get('project') or 
    #         (instance_project.id if instance_project else None)
    #     )

    #     if project_id:
    #         from projects.models import Project
    #         if isinstance(project_id, (int, str)):
    #             project_obj = Project.objects.filter(pk=project_id).first()
    #         else:
    #             project_obj = project_id

    #         if project_obj:
    #             # Visually lock the project field
    #             self.fields['project'].widget.attrs.update({
    #                 'readonly': 'readonly',
    #                 'style': 'pointer-events: none; background-color: #e9ecef;',
    #                 'tabindex': '-1'
    #             })
                
    #             self.fields['assigned_to'].queryset = project_obj.team_members.all().distinct()
    #             self.fields['assigned_to'].help_text = f"Only members of '{project_obj.title}' can be assigned."
    #     else:
    #         self.fields['assigned_to'].queryset = User.objects.none()
    #         self.fields['assigned_to'].help_text = "Select a project first to see available team members."
    











    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Add required field indicators
    #     self.fields['title'].required = True
    #     self.fields['project'].required = True
    #     self.fields['status'].required = True
    #     self.fields['priority'].required = True
    #     self.fields['assigned_to'].required = False
    #     self.fields['due_date'].required = False
    #     self.fields['estimated_hours'].required = False
    #     self.fields['actual_hours'].required = False
    #     self.fields['tags'].required = False

    #     project = getattr(self.instance, 'project', None) or self.initial.get('project')

       
        # 2. If the project is just an ID (integer), fetch the actual object
        # if isinstance(project, int):
        #     from projects.models import Project
        #     project = Project.objects.filter(pk=project).first()

        # if project:
        #     # Now 'project' is guaranteed to be an object (or None)
        #     self.fields['project'].disabled = True
            
        #     # Filter the assignees based on the project members
        #     self.fields['assigned_to'].queryset = project.team_members.all().distinct()
        #     self.fields['assigned_to'].help_text = f"Only members of '{project.title}' can be assigned."
        # else:
        #     # Fallback for general creation without a pre-selected project
        #     # self.fields['assigned_to'].queryset = User.objects.all().exclude(is_staff=True)
        #     self.fields['assigned_to'].queryset = User.objects.none()
        #     self.fields['assigned_to'].help_text = "Select a project first to see available team members."
            
        # Filter the queryset to exclude 'admin' and 'manager'
        
        # self.fields['assigned_to'].queryset = User.objects.exclude(
        #     username__in=['admin','manager']
        # )

    def clean_actual_hours(self):
        actual_hours = self.cleaned_data.get('actual_hours')
        
        if actual_hours is not None and actual_hours < 0:
            raise forms.ValidationError("Actual hours cannot be negative. Time travel isn't supported yet!")
        return actual_hours

class ProgressUpdateForm(forms.ModelForm):
    """Quick form to update progress"""
    progress = forms.IntegerField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'range',
            'min': '0',
            'max': '100',
            'step': '5',
            'style': 'width: 100%;'
        })
    )
    
    class Meta:
        model = Task
        fields = ['progress']


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Add a comment...',
                'rows': 3
            })
        }

class TaskAttachmentForm(forms.ModelForm):
    class Meta:
        model = TaskAttachment
        fields = ['file', 'file_name']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'File name'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            # Explicitly allow Excel extensions
            valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png', '.xlsx', '.xls', '.csv']
            if ext not in valid_extensions:
                raise forms.ValidationError(f"File type {ext} is not supported.")
        return file


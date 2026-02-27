from django import forms
from .models import Task, TaskComment, TaskAttachment
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assigned_to', 'status', 'priority', 'progress', 'due_date', 'estimated_hours', 'actual_hours', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title',
                'required': True
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

    
    def __init__(self, *args, **kwargs):
        # 1. Capture the requesting user passed from the view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Capture Project ID safely (Existing code)
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
            from projects.models import Project
            project_obj = Project.objects.filter(pk=project_id).first() if isinstance(project_id, (int, str)) else project_id

            if project_obj:
                # Visually lock the project field
                self.fields['project'].widget.attrs.update({
                    'readonly': 'readonly',
                    'style': 'pointer-events: none; background-color: #e9ecef;',
                    'tabindex': '-1'
                })
                
                # --- START NEW ROLE-BASED FILTERING ---
                
                # Base queryset: everyone in the project
                assignee_qs = project_obj.team_members.all().distinct()

                if self.user:
                    # Rule: If user is NOT a Manager/Admin, hide Superusers from the project list
                    is_privileged = self.user.profile.role in ['admin', 'manager']
                    
                    if not is_privileged:
                        assignee_qs = assignee_qs.exclude(is_superuser=True)

                # Safety Net: If the task is already assigned to an Admin, 
                # we MUST keep them in the list so the current user doesn't wipe them out.
                if self.instance.pk and self.instance.assigned_to:
                    assignee_qs = (assignee_qs | User.objects.filter(pk=self.instance.assigned_to.pk)).distinct()

                self.fields['assigned_to'].queryset = assignee_qs.order_by('username')
                self.fields['assigned_to'].help_text = f"Only project members can be assigned. (Admin hidden for non-managers)"
                
                # --- END NEW ROLE-BASED FILTERING ---
        else:
            self.fields['assigned_to'].queryset = User.objects.none()
            self.fields['assigned_to'].help_text = "Select a project first to see available team members."









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


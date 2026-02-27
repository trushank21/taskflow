from django import forms
from .models import Project
from django.contrib.auth.models import User

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'status', 'team_lead', 'team_members', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Project description',
                'rows': 4
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'team_lead': forms.Select(attrs={'class': 'form-select'}),
            'team_members': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before start date.")
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # This call below triggers the m2m_changed signal!
            self.save_m2m() 
        return instance
    
    # def __init__(self, *args, **kwargs):
    #     # We catch the 'user' passed from the view's get_form_kwargs
    #     self.user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)

    #     if self.user:
            
    #         # 1. Identify users to exclude (like the 'admin' superuser)
    #         # But we must NOT exclude the current user if they are the Team Lead
            
    #         excluded_usernames = ['admin']

    #         # 2. THE FIX:
    #         # We only exclude the current user if they are NOT a manager 
    #         # AND they are NOT already the assigned team lead
    #         is_manager = self.user.profile.role == 'manager'
    #         is_current_lead = self.instance.pk and self.instance.team_lead == self.user

    #         if not is_manager and not is_current_lead:
    #             excluded_usernames.append(self.user.username)
            
    #         # Fetch the users to exclude
    #         excluded_ids = User.objects.filter(username__in=excluded_usernames).values_list('id', flat=True)
            
    #         # Filter the dropdowns
    #         base_qs = User.objects.exclude(id__in=excluded_ids).order_by('username')

    #         if self.instance.pk and self.instance.team_lead:
    #             base_qs = base_qs | User.objects.filter(pk=self.instance.team_lead.pk)
            
    #         self.fields['team_members'].queryset = base_qs
    #         self.fields['team_lead'].queryset = base_qs

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            # 1. Determine the Role-Based Queryset
            user_qs = User.objects.all()
            
            # Define roles for clarity
            is_manager_or_admin = self.user.profile.role in ['manager', 'admin']
            
            # 2. Apply Visibility Rules
            if not is_manager_or_admin:
                # Rule: Non-Managers cannot see Superusers (Admins)
                user_qs = user_qs.exclude(is_superuser=True)
                
                # Rule: Non-Managers shouldn't necessarily be assigning themselves 
                # as Lead unless they are already the lead (handles the "self-lead" case)
                is_current_lead = self.instance.pk and self.instance.team_lead == self.user
                if not is_current_lead:
                    user_qs = user_qs.exclude(id=self.user.id)

            # 3. The "Existing Data" Safety Net
            # If the project already has a Lead who would be excluded by the rules above 
            # (e.g., a Manager assigned an Admin), we must include that user in the queryset
            # so the field doesn't appear empty or break on save.
            if self.instance.pk and self.instance.team_lead:
                user_qs = (user_qs | User.objects.filter(pk=self.instance.team_lead.pk)).distinct()

            # 4. Final Assignment
            ordered_qs = user_qs.order_by('username')
            self.fields['team_lead'].queryset = ordered_qs
            self.fields['team_members'].queryset = ordered_qs
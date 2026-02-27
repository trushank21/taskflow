from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import UserProfile
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from .tasks import send_password_reset_email

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Unified styling for all fields
        self.fields['password1'].help_text = (
            "Password must be at least 8 characters, "
            "not too common, and not similar to your username."
        )
        for field_name, field in self.fields.items():
            if field_name == 'first_name':
                field.widget.attrs.update({'placeholder':'First Name'})
            elif field_name == 'last_name':
                field.widget.attrs.update({'placeholder':'Last Name'})
            elif field_name == 'email':
                field.widget.attrs.update({'placeholder':'Email'})
            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.label
                })

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

class UserProfileForm(forms.ModelForm):
    """Used during registration to capture initial profile data"""
    ROLE_CHOICES = [('developer', 'Developer'), ('manager', 'Manager')]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))

    class Meta:
        model = UserProfile
        fields = ('role', 'department', 'phone', 'bio')
    
    # def save(self, user, commit=True):
    #     """
    #     Custom save method that accepts the user object 
    #     and links the profile data to it.
    #     """
    #     # Get the profile (created by signals) or create a new one as backup
    #     # profile, created = UserProfile.objects.get_or_create(user=user)
    #     profile = user.profile
    #     # Assign the cleaned data from the form to the profile object
    #     profile.role = self.cleaned_data.get('role')
    #     profile.department = self.cleaned_data.get('department')
    #     profile.phone = self.cleaned_data.get('phone')
    #     profile.bio = self.cleaned_data.get('bio')
        
    #     if commit:
    #         profile.save()
    #     return profile

    def save(self, user, commit=True):
        # Use the safety net here too!
        profile = getattr(user, 'profile', None)
        if profile is None:
            profile = UserProfile(user=user)

        # Bulk update attributes from cleaned_data
        for field, value in self.cleaned_data.items():
            setattr(profile, field, value)
        
        if commit:
            profile.save()
        return profile

class UserProfileUpdateForm(forms.ModelForm):
    # fields for the User model
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['avatar', 'department', 'phone', 'bio']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill User data
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

        # APPLY STYLES: This injects 'form-control' into every field automatically
        for field_name, field in self.fields.items():
            if field_name != 'avatar':
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': f'Enter {field.label}'
                })

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        # If the email exists on ANY user EXCEPT the one currently being edited
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already in use by another account.')
        return email
    
    def save(self, commit=True):
        # 1. Get/Create the profile safely
        profile = getattr(self.user, 'profile', None)
        if profile is None:
            profile = UserProfile(user=self.user)

        # 2. Update Profile fields manually to avoid conflicts with User fields
        # This only pulls fields defined in Meta.fields
        for field in self._meta.fields:
            if field in self.cleaned_data:
                setattr(profile, field, self.cleaned_data[field])

        # 3. Save User fields (first name, email)
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name')
            self.user.last_name = self.cleaned_data.get('last_name')
            self.user.email = self.cleaned_data.get('email')
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        return profile

    # def save(self, commit=True):
    #     # Save Profile fields (bio, phone, etc)
    #     profile = super().save(commit=False)
        
    #     # Save User fields (first name, email)
    #     if self.user:
    #         self.user.first_name = self.cleaned_data['first_name']
    #         self.user.last_name = self.cleaned_data['last_name']
    #         self.user.email = self.cleaned_data['email']
    #         if commit:
    #             self.user.save()
        
    #     if commit:
    #         profile.save()
    #     return profile

class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': f'Enter {field.label.lower()}'
            })


# accounts/forms.py
class CeleryPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email__iexact=email).exists():
            raise ValidationError("No account found with this email address.")
        return email
    
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        
        # Use the HTML template specifically
        target_template = html_email_template_name or 'accounts/password_reset_email.html'

        serializable_context = {
            'email': context['email'],
            'domain': context['domain'],
            'uid': context['uid'],
            'user': context['user'].pk, # Changed to ID
            'token': context['token'],
            'protocol': context['protocol'],
        }

        send_password_reset_email.delay(
            subject="TaskFlow Password Reset",
            email_template_name=target_template, # Force the correct path
            context=serializable_context,
            to_email=to_email
        )
from django.urls import path, reverse_lazy
from . import views
from accounts.forms import CeleryPasswordResetForm
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password-change/', views.UserPasswordChangeView.as_view(), name='password_change'),
    path('resource-dashboard/', views.admin_resource_dashboard, name='resource_dashboard'),
    
    
    path('password-reset/', 
     auth_views.PasswordResetView.as_view(
         form_class=CeleryPasswordResetForm,
         template_name='accounts/password_reset.html',
         html_email_template_name='accounts/password_reset_email.html',
         success_url=reverse_lazy('accounts:password_reset_done') # ADD THIS LINE
     ), name='password_reset'),

    # 2. Success Page (Where they go after clicking "Submit")
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), name='password_reset_done'),

    # 3. The Actual Link from the Email
    path('password-reset-confirm/<uidb64>/<token>/', 
     auth_views.PasswordResetConfirmView.as_view(
         template_name='registration/password_reset_confirm.html',
         success_url=reverse_lazy('accounts:password_reset_complete') # ADD THIS LINE
     ), name='password_reset_confirm'),

    # 4. Final Success Page
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), name='password_reset_complete'),
]


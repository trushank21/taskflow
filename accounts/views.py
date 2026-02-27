from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import UserProfile
from .forms import StyledPasswordChangeForm, UserRegistrationForm, UserProfileForm, UserProfileUpdateForm
from django.db.models import Count, Q,Value
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.functions import Coalesce
from tasks.models import Task
from django.http import JsonResponse
from django.contrib.auth.views import PasswordResetView
from .tasks import send_password_reset_email
from django.contrib.auth.forms import PasswordResetForm
from .decorators import role_required
from accounts.forms import CeleryPasswordResetForm
from django.db.models import OuterRef, Subquery, IntegerField


def register_view(request):
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save()


                    # Signal creates profile here automatically
                    # profile = user.profile 
                    # profile.role = profile_form.cleaned_data['role']
                    # profile.department = profile_form.cleaned_data.get('department')
                    # profile.phone = profile_form.cleaned_data.get('phone')
                    # profile.bio = profile_form.cleaned_data.get('bio')
                    # profile.save()

                    profile_form.save(user=user)

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success', 
                        'message': 'Account created!', 
                        'redirect_url': reverse('login')
                    })
                return redirect('login')

            except Exception as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': {**user_form.errors, **profile_form.errors}}, status=400)
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()

    return render(request, 'accounts/register.html', {
        'user_form': user_form, 
        'profile_form': profile_form
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'You have been logged in successfully!')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success', 
                    'redirect_url': reverse('tasks:dashboard') # This fixes your 404
                })
            return redirect('tasks:dashboard')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Invalid username or password!'}, status=400)
            messages.error(request, 'Invalid username or password!')
        
    return render(request, 'accounts/login.html')

@require_http_methods(["POST"])
def logout_view(request):
    """User logout view - requires POST request"""
    logout(request)
    # messages.success(request, 'You have been logged out successfully!')
    return redirect('login')

@login_required
def profile_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    view_mode = request.GET.get('view', 'personal')
    allowed_roles = ['admin', 'manager', 'developer','observer']

    if view_mode == 'team':
        if profile.role in ['admin', 'observer']:
            base_qs = Task.objects.all()

    if view_mode == 'team' and profile.role not in allowed_roles:
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Return JSON so the frontend can show a specific alert or disable the button
            return JsonResponse({
                'status': 'error', 
                'message': 'Team stats are restricted to Managers.'
            }, status=403)
        
        messages.error(request, "You do not have permission to view team stats.")
        return redirect('accounts:profile')
    
    

    if not profile:
        messages.info(request, "Please complete your profile details.")
        return redirect('accounts:profile_edit')
    
    if view_mode == 'team':
        if profile.role in ['admin', 'observer']:
            base_qs = Task.objects.all() # Global View
        else:
            base_qs = Task.objects.filter(
                Q(assigned_to=user) | Q(assigned_by=user) | Q(project__team_members=user)
            ).distinct()
    else:
        base_qs = Task.objects.filter(assigned_to=user)
    
    
    # # 1. Base Queryset Definition
    # if view_mode == 'team':
    #     base_qs = Task.objects.filter(
    #         Q(assigned_to=user) | 
    #         Q(assigned_by=user) | 
    #         Q(project__team_members=user)
    #     ).distinct()
    # else:
    #     base_qs = Task.objects.filter(assigned_to=user)

    # 2. Strict Stats Calculation
    # Active Work: MUST be in an Active Project AND not completed/blocked.
    # stats = base_qs.aggregate(
    #     active_work=Coalesce(
    #         Count('id', filter=Q(
    #             project__status='active', 
    #             status__in=['todo', 'in_progress', 'in_review']
    #         )), 
    #         Value(0)
    #     ),
    #     completed=Coalesce(Count('id', filter=Q(status='completed')), Value(0)),
    #     blocked=Coalesce(Count('id', filter=Q(status='blocked')), Value(0))
    # )

    # ... inside profile_view ...
    # 2. Strict Stats Calculation
    stats = base_qs.aggregate(
        active_work=Count('id', filter=Q(
            project__status='active', 
            status__in=['todo', 'in_progress', 'in_review']
        ), distinct=True), # Added distinct=True
        completed=Count('id', filter=Q(status='completed'), distinct=True),
        blocked=Count('id', filter=Q(status='blocked'), distinct=True)
    )

    context = {
        'profile': profile,
        'view_mode': view_mode,
        'total_tasks_count': base_qs.count(), 
        'in_progress_tasks_count': stats['active_work'],
        'completed_tasks_count': stats['completed'],
        'blocked_tasks_count': stats['blocked'],
    }

    # 3. AJAX Handler: Return JSON for seamless UI updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'total': context['total_tasks_count'],
            'active': context['in_progress_tasks_count'],
            'completed': context['completed_tasks_count'],
            'blocked': context['blocked_tasks_count'],
            'header_text': "Team Activity Overview" if view_mode == 'team' else "Personal Performance"
        })

    return render(request, 'accounts/profile.html', context)

@transaction.atomic
@login_required
def profile_edit_view(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Profile updated successfully!'})
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        form = UserProfileUpdateForm(instance=profile, user=request.user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})


class UserPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')
    success_message = "Your password was successfully updated!"


def get_task_count_subquery(status):
    """
    Returns a subquery that counts tasks for a specific user and status.
    Uses .values('assigned_to') and .annotate() to generate a GROUP BY 
    compatible with Subquery requirements.
    """
    # Create the base subquery
    sq = Task.objects.filter(
        assigned_to=OuterRef('pk'),
        status=status
    ).values('assigned_to').annotate(cnt=Count('pk')).values('cnt')
    
    # Wrap in Coalesce so it returns 0 instead of None
    return Coalesce(Subquery(sq, output_field=IntegerField()), 0)


@login_required
@role_required(['admin', 'manager', 'observer'])
def admin_resource_dashboard(request):
    # if request.user.profile.role not in ['admin', 'manager','observer']:
    #     messages.error(request, "Access denied.")
    #     return redirect('accounts:profile')

    # # We use distinct=True to avoid double-counting due to ManyToMany joins
    # users_report = User.objects.select_related('profile').annotate(
    #     todo_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='todo'), distinct=True),
    #     in_progress_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='in_progress'), distinct=True),
    #     completed_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed'), distinct=True),
    #     # Helper to calculate workload: Todo + In Progress
    #     total_active=Count('assigned_tasks', filter=Q(assigned_tasks__status__in=['todo', 'in_progress']), distinct=True)
    # ).order_by('profile__role', 'username')

    users_report = User.objects.select_related('profile').annotate(
        todo_count=get_task_count_subquery('todo'),
        in_progress_count=get_task_count_subquery('in_progress'),
        completed_count=get_task_count_subquery('completed'),
        blocked_count=get_task_count_subquery('blocked'),
        # Custom logic for total active (In Progress + In Review)
        # Note: You can add these two subqueries together!
        total_active=(
            get_task_count_subquery('in_progress') + 
            get_task_count_subquery('in_review')
        )
    ).order_by('profile__role', 'username')



    # users_report = User.objects.select_related('profile').annotate(
    #     todo_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='todo'), distinct=True),
    #     in_progress_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='in_progress'), distinct=True),
    #     completed_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed'), distinct=True),
    #     # Added 'in_review' to match profile_view logic
    #     total_active=Count('assigned_tasks', filter=Q(
    #         assigned_tasks__status__in=['todo', 'in_progress', 'in_review']
    #     ), distinct=True)
    # ).order_by('profile__role', 'username')

    return render(request, 'accounts/resource_dashboard.html', {
        'users_report': users_report
    })



class CustomPasswordResetView(PasswordResetView):
    form_class=CeleryPasswordResetForm
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('registration:password_reset_done')
    def form_valid(self, form):
        # We still want the normal behavior (generating tokens, etc.)
        # but we trigger our Celery task instead of the default mailer.
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        
        # This is where we hook in our Celery task
        # Note: You might need to adjust your task to handle the 
        # complex User object or tokens depending on your setup.
        form.save(**opts) 
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get email from session (stored during form_valid in ResetView)
        context['user_email'] = self.request.session.get('reset_email')
        context['cooldown_period'] = 60  # seconds
        if not context.get('validlink'):
            context['error_title'] = "Link Expired or Invalid"
            context['error_message'] = "This password reset link is no longer valid. Links expire after 3 days or can only be used once."
        return context
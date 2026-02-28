from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.tasks import task
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count,Avg
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django_filters.views import FilterView
from django.db import transaction
from projects.models import Project
from .models import Task, TaskComment, TaskAttachment, TaskHistory
from .filters import TaskFilter
from .forms import TaskAttachmentForm, TaskForm, TaskCommentForm, ProgressUpdateForm
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.utils.timesince import timesince
from django.utils import timezone
from cloudinary.utils import cloudinary_url
from django.http import HttpResponse
import os
import cloudinary


cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET'),
    secure = True
)

from django.template.loader import render_to_string
from django.http import JsonResponse




@login_required
def dashboard(request):
    user = request.user
    view_mode = request.GET.get('view', 'personal')
    search_query = request.GET.get('q', '').strip()

    if user.profile.role in ['admin', 'manager']:
        project_pool = Project.objects.all()
    else:
        # Projects where user is Lead or a Member
        project_pool = Project.objects.filter(
            Q(team_lead=user) | Q(team_members=user)
        ).distinct()

    proj_stats = project_pool.aggregate(
        active_projs=Count('id', filter=Q(status='active')),
        on_hold_projs=Count('id', filter=Q(status='on_hold')),
        inactive_projs=Count('id', filter=Q(status='inactive')),
    )

    # 1. ORCHESTRATE THE TASK POOL
    if user.profile.role in ['admin', 'manager']:
        tasks_qs = Task.objects.all()
    else:
        # Get projects where user is the designated Lead
        led_projects = Project.objects.filter(team_lead=user)
        
        if view_mode == 'team':
            # Team view: Tasks from projects you lead OR projects you are a member of
            tasks_qs = Task.objects.filter(
                Q(project__in=led_projects) | Q(project__team_members=user)
            ).distinct()
        else:
            # Personal view: Only things explicitly assigned to you
            tasks_qs = Task.objects.filter(assigned_to=user)

    # Apply Dashboard Search
    if search_query:
        tasks_qs = tasks_qs.filter(
            Q(title__icontains=search_query) | 
            Q(project__title__icontains=search_query)
        )

    # 2. HIGH-PERFORMANCE AGGREGATION (Single DB Hit)
    # We use 'distinct=True' for project counts because tasks_qs might have duplicates from JOINS
    # --- UPDATED AGGREGATION ---
    stats = tasks_qs.aggregate(
        active_tasks=Count('id', filter=Q(project__status='active') & ~Q(status='completed')),
        
        # FIX: Remove 'project__status=active' to count ALL completed tasks in the pool
        # completed_tasks=Count('id', filter=Q(status='completed')), 
        # completed_tasks=Count('id', filter=Q(project__status='active', status='completed')),
        completed_tasks=Count('id', filter=Q(status='completed')),
        
        on_hold_tasks=Count('id', filter=Q(project__status='on_hold')),
        inactive_tasks=Count('id', filter=Q(project__status='inactive')),
        # actionable_pool_count=Count('id', filter=Q(project__status='active')),
        actionable_pool_count=Count('id', filter=Q(project__status__in=['active','completed']) &  ~Q(status='blocked')),
        # actionable_pool_count=Count('id'),
        # Project counts
        # active_projs=Count('project', filter=Q(project__status='active'), distinct=True),
        # on_hold_projs=Count('project', filter=Q(project__status='on_hold'), distinct=True),
        # inactive_projs=Count('project', filter=Q(project__status='inactive'), distinct=True),
        overall_progress=Avg('progress')
    )
    total = stats['actionable_pool_count'] or 0
    completed = stats['completed_tasks'] or 0
    
    # 3. EFFICIENCY CALCULATION
    # actionable = stats['actionable_pool_count']
    # efficiency = round((stats['completed_tasks'] / actionable) * 100) if actionable > 0 else 0
    efficiency = round((completed / total) * 100) if total > 0 else 0
    efficiency = min(efficiency, 100)

    # 4. RECENT TASKS (Optimized with select_related)
    # Added 'assigned_to__profile' to prevent N+1 if you show user roles/avatars in the table
    
    # recent_tasks = tasks_qs.select_related('project', 'assigned_to', 'assigned_to__profile').order_by('-updated_at')[:10]
    recent_tasks = tasks_qs.select_related('project', 'assigned_to', 'assigned_by__profile').order_by('-updated_at')[:10]
    # recent_tasks = tasks_qs.select_related('project', 'assigned_to', 'assigned_to__profile') \
    # .annotate(project_avg=Avg('project__tasks__progress')) \
    # .order_by('-updated_at')[:10]
    
    if user.profile.role in ['admin', 'manager']:
        # Admins see all blocked tasks across the company
        my_blocked_tasks = Task.objects.filter(status='blocked')
    else:
        # Developers only see their own assigned/lead blocked tasks
        my_blocked_tasks = Task.objects.filter(
            status='blocked'
        ).filter(Q(assigned_to=user) | Q(project__team_lead=user))
    
    # 2. Get the COUNT of those tasks (The Number)
    blocked_tasks_count = my_blocked_tasks.count()
    # 2. Get the number of UNIQUE projects that contain those blocked tasks
    projects_with_blocked_tasks = my_blocked_tasks.values('project').distinct().count()
    
    
    # --- RESPONSE HANDLING ---
    context = {
        'overall_completion': round(stats['overall_progress'] or 0),
        'today': timezone.now().date(),
        'view_mode': view_mode,
        'total_active': stats['active_tasks'],
        'completed_tasks': stats['completed_tasks'],
        'on_hold_count': stats['on_hold_tasks'],
        'blocked_tasks_count': blocked_tasks_count,
        'projects_with_blocked_tasks': projects_with_blocked_tasks,
        'inactive_count': stats['inactive_tasks'],
        'active_projects_count': proj_stats['active_projs'],
        'on_hold_projects_count':  proj_stats['on_hold_projs'],
        'inactive_projects_count': proj_stats['inactive_projs'],
        'efficiency': efficiency,
        'recent_tasks': recent_tasks,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('tasks/includes/dashboard_table_rows.html', {
            'recent_tasks': recent_tasks,
            'view_mode': view_mode,

        }, request=request)
        
        # Update context values into the AJAX response
        return JsonResponse({
            'html': html,
            'total_active': context['total_active'],
            'completed': context['completed_tasks'],
            'on_hold': context['on_hold_count'],
            'inactive': context['inactive_count'],
            'active_projects': context['active_projects_count'],
            'on_hold_projects': context['on_hold_projects_count'],
            'inactive_projects': context['inactive_projects_count'],
            'efficiency': context['efficiency'], 
            'overall_completion': context['overall_completion'],
        })

    return render(request, 'tasks/dashboard.html', context)
















# @login_required
# def dashboard(request):
#     user = request.user
#     view_mode = request.GET.get('view', 'personal')
#     search_query = request.GET.get('q', '').strip()


#     # 1. ORCHESTRATE THE TASK POOL
#     # Managers/Admins see everything. 
#     # Leads see all tasks for projects they lead.
#     # Members see only tasks assigned to them.
#     if user.profile.role in ['admin', 'manager']:
#         tasks_qs = Task.objects.all()
#     else:
#         # Get projects where user is the designated Lead
#         led_projects = Project.objects.filter(team_lead=user)
        
#         if view_mode == 'team':
#             # Team view: Tasks from projects you lead OR projects you are a member of
#             tasks_qs = Task.objects.filter(
#                 Q(project__in=led_projects) | Q(project__team_members=user)
#             ).distinct()
#         else:
#             # Personal view: Only things explicitly assigned to you
#             tasks_qs = Task.objects.filter(assigned_to=user)

    
    
#     # # Base Projects Pool
#     # projects_qs = Project.objects.filter(Q(team_lead=user) | Q(team_members=user)).distinct()
    
#     # # Base Tasks Pool
#     # if view_mode == 'team':
#     #     tasks_qs = Task.objects.filter(project__in=projects_qs)
#     # else:
#     #     tasks_qs = Task.objects.filter(assigned_to=user)



#     # Apply Dashboard Search
#     if search_query:
#         tasks_qs = tasks_qs.filter(
#             Q(title__icontains=search_query) | 
#             Q(project__title__icontains=search_query)
#         )

#     # --- THE SMART COUNTS (TASKS) ---
#     active_tasks_qs = tasks_qs.filter(project__status='active').exclude(status='completed')
#     active_tasks = active_tasks_qs.count()
#     on_hold_tasks = tasks_qs.filter(project__status='on_hold').count()
#     inactive_tasks = tasks_qs.filter(project__status='inactive').count()
    
#     # --- THE PROJECT COUNTS ---
#     active_projects_count = active_tasks_qs.values('project').distinct().count()
#     on_hold_projects_count = tasks_qs.filter(project__status='on_hold').values('project').distinct().count()
#     inactive_projects_count = tasks_qs.filter(project__status='inactive').values('project').distinct().count()

#     # --- EFFICIENCY CALCULATION (ACCURACY FIX) ---
#     # We define "actionable" as any task in an active project.
#     actionable_pool = tasks_qs.filter(project__status='active')
#     actionable_tasks_count = actionable_pool.count()
    
#     # We only count completed tasks that belong to that same actionable pool.
#     completed_tasks = actionable_pool.filter(status='completed').count()
    
#     # Calculate efficiency based on current active scope only
#     if actionable_tasks_count > 0:
#         raw_efficiency = (completed_tasks / actionable_tasks_count) * 100
#         efficiency = round(min(raw_efficiency, 100))
#     else:
#         efficiency = 0

#     recent_tasks = tasks_qs.select_related('project', 'assigned_to').order_by('-updated_at')[:10]

#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         html = render_to_string('tasks/includes/dashboard_table_rows.html', {
#             'recent_tasks': recent_tasks,
#             'view_mode': view_mode
#         }, request=request)
        
#         return JsonResponse({
#             'html': html,
#             'total_active': active_tasks,
#             'completed': completed_tasks,
#             'on_hold': on_hold_tasks,
#             'inactive': inactive_tasks,
#             'active_projects': active_projects_count,
#             'on_hold_projects': on_hold_projects_count,
#             'inactive_projects': inactive_projects_count,
#             'efficiency': efficiency, 
#         })

#     context = {
#         'view_mode': view_mode,
#         'total_active': active_tasks,
#         'completed_tasks': completed_tasks,
#         'on_hold_count': on_hold_tasks,
#         'inactive_count': inactive_tasks,
#         'active_projects_count': active_projects_count,
#         'on_hold_projects_count': on_hold_projects_count,
#         'inactive_projects_count': inactive_projects_count,
#         'efficiency': efficiency,
#         'recent_tasks': recent_tasks,
#     }
#     return render(request, 'tasks/dashboard.html', context)





# --- TASK LIST VIEW ---
class TaskListView(LoginRequiredMixin, FilterView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    filterset_class = TaskFilter
    paginate_by = 10

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Pass user from the view
        super().__init__(*args, **kwargs)
        if user:
            self.filters['project'].field.queryset = Project.objects.filter(
                Q(team_members=user) | Q(team_lead=user)
            ).distinct()

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.select_related('project', 'assigned_to')
        
    
        # 1. SECURITY SCOPE
        if user.profile.role not in ['admin', 'manager','observer']:
            qs = qs.filter(
                Q(assigned_to=user) | 
                Q(assigned_by=user) | 
                Q(project__team_members=user)
            ).distinct()

        # 2. WORKSPACE POOL (Mine vs Team)
        view_mode = self.request.GET.get('view', 'all')
        if view_mode == 'mine':
            qs = qs.filter(assigned_to=user)
        elif view_mode == 'team':
            qs = qs.filter(project__team_members=user).exclude(assigned_to=user)

        # 3. UPDATED LIFECYCLE TOGGLE
        proj_status = self.request.GET.get('proj_status', 'active')
        
        if proj_status == 'completed':
            # NEW: Section for only completed tasks
            qs = qs.filter(status='completed')
        elif proj_status == 'on_hold':
            # Show blocked tasks or tasks in stalled projects (excluding completed ones)
            qs = qs.filter(
                Q(project__status__in=['on_hold', 'inactive']) | 
                Q(status='blocked')
            ).exclude(status='completed')
        else:
            # Default: Active work in active projects (excluding completed/blocked)
            qs = qs.filter(project__status='active').exclude(status__in=['completed', 'blocked'])

        # 4. FIXED SMART SEARCH
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | 
                Q(project__title__icontains=query)
            ).distinct()
            
        # 5. INTEGRATE FILTERS
        self.filterset = self.filterset_class(self.request.GET, queryset=qs.order_by('-updated_at'))
        return self.filterset.qs
    
    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['user'] = self.request.user # Pass user to the filter
        return kwargs

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('tasks/includes/task_inventory_table.html', context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)
    

# --- TASK DETAIL VIEW ---
@method_decorator(never_cache, name='dispatch')
class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        # Use prefetch_related for the related sets to avoid N+1 queries
        return super().get_queryset().prefetch_related(
            'comments__commented_by', 
            'attachments__uploaded_by',
            'history__changed_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_locked'] = self.object.project.status == 'inactive'
        # context['comments'] = self.object.comments.select_related('commented_by').all()
        # context['attachments'] = self.object.attachments.select_related('uploaded_by').all()
        # We remove .select_related() because the data is already prefetched above.
        context['comments'] = self.object.comments.all() 
        context['attachments'] = self.object.attachments.all()
        context['comment_form'] = TaskCommentForm()
        # Pass the attachment form to the template
        context['attachment_form'] = TaskAttachmentForm() 
        return context

# --- TASK CREATE/UPDATE/DELETE ---
class TaskCreateView(LoginRequiredMixin,UserPassesTestMixin,CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def test_func(self):
        user = self.request.user
        project_id = self.request.GET.get('project')

        if user.profile.role in ['admin', 'manager']:
            return True
        
        # 2. Check if this Developer is the Lead for the specific project
        if project_id:
            project = get_object_or_404(Project, id=project_id)

            # RULE: Cannot create tasks in an Inactive/Locked project
            if project.status == 'inactive':
                return False
            
            # Allow if the Developer is the designated Team Lead
            return project.team_lead == user

        return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Injects the current user into the form
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Get the 'project' ID from the URL query parameters
        project_id = self.request.GET.get('project')
        
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            
            # 1. Automatically select the project in the dropdown
            initial['project'] = project
            
            # 2. Automatically set the Task's due_date to the Project's end_date
            if project.end_date:
                # Format for the datetime-local HTML input: 'YYYY-MM-DDTHH:MM'
                initial['due_date'] = project.end_date.strftime('%Y-%m-%dT23:59')
        
        return initial

    def form_valid(self, form):
        form.instance.assigned_by = self.request.user
        response = super().form_valid(form)
    
        # Create the "Initial" history log
        TaskHistory.objects.create(
            task=self.object,
            old_status="N/A",
            new_status=self.object.get_status_display(),
            changed_by=self.request.user,
            # You could even add a 'comment' field to TaskHistory for "Task Created"
        )
        messages.success(self.request, f'Task "{form.instance.title}" created.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})


@method_decorator(never_cache, name='dispatch')
class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Injects the current user into the form
        return kwargs

    def test_func(self):
        user = self.request.user
        task = self.get_object()

        is_authorized = (
            user.profile.role in ['admin', 'manager'] or 
            task.project.team_lead == user or  # <--- This is already here!
            task.assigned_to == user
        )

        # Rule 1: Project-wide lock
        if task.project.status == 'inactive':
            return False
        
       # Rule 2: Global Role restrictions
        if user.profile.role == 'observer':
            return False

        # Rule 3: Authority Override (Admin, Manager, OR Project Team Lead)
        if user.profile.role in ['admin', 'manager'] or task.project.team_lead == user:
            return True
        
        # Rule 4: Standard Member (Only their own assigned tasks)
        return task.assigned_to == user
        
    
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        user = self.request.user
        task = self.get_object()

        # LOGIC: Lock fields ONLY if the user is a Developer AND NOT the Team Lead
        # If they are the Lead, they get full access to assign/edit everything.
        is_developer = hasattr(user, 'profile') and user.profile.role == 'developer'
        is_not_lead = task.project.team_lead != user

        if is_developer and is_not_lead:
            # Fields that a regular developer should not change
            fields_to_lock = [
                'priority', 'due_date', 'estimated_hours', 'title', 
                'project', 'tags', 'description', 'assigned_to'
            ]
            for field_name in fields_to_lock:
                if field_name in form.fields:
                    # Server-side: prevent data processing for these fields
                    form.fields[field_name].disabled = True
                    
                    # Client-side: Visual styling for the locked fields
                    current_classes = form.fields[field_name].widget.attrs.get('class', '')
                    form.fields[field_name].widget.attrs.update({
                        'class': f"{current_classes} bg-light locked-field",
                        'style': 'pointer-events: none; cursor: not-allowed;',
                    })
        return form

    def form_valid(self, form):
        old_task = self.get_object()
        old_status_label = old_task.get_status_display()

        actual = form.cleaned_data.get('actual_hours')
        estimated = form.cleaned_data.get('estimated_hours')

        # Add a warning message if hours exceed estimate
        if actual and estimated and actual > estimated:
            messages.warning(self.request, f"Note: Actual hours ({actual}) exceeded the estimate ({estimated}).")


        new_status = form.cleaned_data.get('status')
        new_progress = form.cleaned_data.get('progress')

        # if new_progress == 100:
        #     form.instance.status = 'completed'
        #     if new_status != 'completed':
        #         messages.info(self.request, "Status forced to 'Completed' because progress is 100%.")

        ## If progress is 0 and status was 'completed', force it back to 'todo'
        # elif new_progress == 0 and new_status == 'completed':
            # form.instance.status = 'todo'
            # messages.info(self.request, "Status forced to 'To Do' because progress is 0%.")

        if new_status == 'todo':
            form.instance.progress = 0
        elif new_status == 'completed':
            form.instance.progress = 100
        elif new_status == 'in_review':
            form.instance.progress = 90
        elif new_status == 'blocked':
            # DO NOTHING: We keep the current progress as it is.
            # This allows the developer to keep their 75% progress visible.
            pass
        elif new_status == 'in_progress':
            # Ensure In Progress isn't accidentally 0 or 100
            if new_progress == 0 or new_progress == 100:
                form.instance.progress = 10
        
        response = super().form_valid(form)
        if old_status_label != self.object.get_status_display():
            TaskHistory.objects.create(
                task=self.object,
                old_status=old_status_label,
                new_status=self.object.get_status_display(),
                changed_by=self.request.user
            )
        messages.success(self.request, 'Task details updated.')
        return response
            

        # # --- UPDATED SYNC LOGIC ---
        # # 1. Force 100% for completed tasks
        # if new_status == 'completed' and new_progress < 100:
        #     form.instance.progress = 100
        #     messages.info(self.request, 'Progress automatically set to 100% for completed task.')
        # # 2. Force 0% ONLY if the status is explicitly 'todo'
        # elif new_status == 'todo' and new_progress > 0:
        #     form.instance.progress = 0
        # # 3. If slider hits 100, set status to completed
        # elif new_progress == 100 and new_status != 'completed':
        #     form.instance.status = 'completed'
        # # 4. If a completed task is reopened by moving the slider
        # elif 0 < new_progress < 100 and new_status == 'completed':
        #     form.instance.status = 'in_progress'
        
        # NOTE: We no longer force status to 'todo' if progress is 0.
        # This allows 'blocked' or 'in_progress' tasks to stay at 0%.

        # messages.success(self.request, 'Task details updated.')
        # return super().form_valid(form)

    def get_success_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})


# @method_decorator(never_cache, name='dispatch')
# class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
#     model = Task
#     form_class = TaskForm
#     template_name = 'tasks/task_form.html'

#     def test_func(self):
#         task = self.get_object()
#         # Rule A: Block all edits if the project is inactive (Locked)
#         if task.project.status == 'inactive':
#             return False
#         # Admins and Managers have global edit rights
#         if self.request.user.profile.role in ['admin', 'manager']:
#             return True
#         # Developers can ONLY edit tasks assigned specifically TO THEM
#         return task.assigned_to == self.request.user
    
#     def get_form(self, *args, **kwargs):
#         form = super().get_form(*args, **kwargs)
#         # Fix: Disable sensitive fields for Developers
#         if self.request.user.profile.role == 'developer':
#             if 'project' in form.fields:
#                 form.fields['project'].disabled = True
#             if 'assigned_to' in form.fields:
#                 form.fields['assigned_to'].disabled = True
#         return form

#     def form_valid(self, form):
#         new_status = form.cleaned_data.get('status')
#         new_progress = form.cleaned_data.get('progress')

#         # --- INTELLIGENT SYNC ---
        
#         # 1. If user marks as completed, progress MUST be 100
#         if new_status == 'completed' and new_progress < 100:
#             form.instance.progress = 100
#             messages.info(self.request, 'Progress automatically set to 100% for completed task.')

#         # 2. If user marks as todo, progress MUST be 0
#         elif new_status == 'todo' and new_progress > 0:
#             form.instance.progress = 0

#         # 3. If they move the slider to 100, status MUST be completed
#         elif new_progress == 100 and new_status != 'completed':
#             form.instance.status = 'completed'

#         # 4. If they move the slider to 0, status MUST be todo
#         elif new_progress == 0 and new_status != 'todo':
#             form.instance.status = 'todo'
            
#         # 5. If slider is in middle but status was 'completed', move to 'in_progress'
#         # (This covers the case where someone re-opens a closed task by sliding progress back)
#         elif 0 < new_progress < 100 and new_status == 'completed':
#             form.instance.status = 'in_progress'

#         messages.success(self.request, 'Task details updated.')
#         return super().form_valid(form)

#     def get_success_url(self):
#         # Keeps user on the detail page of the task they just edited
#         return reverse('tasks:task_detail', kwargs={'pk': self.object.pk})



class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')

    def test_func(self):
        # Only Admins and Managers can delete tasks
        return self.request.user.profile.role in ['admin', 'manager']

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Task removed.')
        return super().delete(request, *args, **kwargs)

# --- PROTECTED ACTIONS ---

@login_required
def add_comment(request, pk):
    task = get_object_or_404(Task, pk=pk)

    # ADD THIS: Enforce Rule A for comments
    if task.project.status == 'inactive':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Project is locked.'}, status=403)
        messages.error(request, "Comments are disabled for locked projects.")
        return redirect('tasks:task_detail', pk=pk)
    
    if request.method == 'POST':
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.commented_by = request.user

            # ADD THIS: Handle the reply logic
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(TaskComment, id=parent_id)

            comment.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'id': comment.pk,  # Needed for immediate edit/delete
                    'user': request.user.username,
                    'comment': comment.comment,
                    'is_reply': bool(comment.parent),
                    'parent_id': parent_id
                })
    return redirect('tasks:task_detail', pk=pk)

@login_required
def edit_comment(request, pk):
    comment = get_object_or_404(TaskComment, pk=pk)

    is_author = comment.commented_by == request.user
    is_staff = request.user.profile.role in ['admin', 'manager']

    if not (is_author or is_staff):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        new_text = request.POST.get('comment')
        if new_text:
            comment.comment = new_text
            comment.save()
            return JsonResponse({'status': 'success', 'comment': comment.comment})
            
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(TaskComment, pk=pk)
    # Security: Only uploader or Admin/Manager can delete
    if comment.commented_by == request.user or request.user.profile.role in ['admin', 'manager']:
        comment.delete()
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

@login_required
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    user = request.user

    is_authorized = (
        user.profile.role in ['admin', 'manager'] or 
        task.project.team_lead == user or  # Team Lead check
        task.assigned_to == user
    )
    
    if task.project.status == 'inactive' or not is_authorized:
        return JsonResponse({'status': 'error', 'message': 'Not authorized.'}, status=403)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES) and new_status != task.status:
            old_label = task.get_status_display()

            # --- FORWARD-FORCING LOGIC ---
            if new_status == 'completed':
                task.progress = 100
            elif new_status == 'todo':
                task.progress = 0
            elif new_status == 'in_review':
                task.progress = 90
            elif new_status == 'blocked':
                pass
            
            elif new_status == 'in_progress':
                # "Re-open" logic: if it was Done or Todo, jump to a working state
                if task.status in ['completed', 'todo']:
                    task.progress = 10  # Set to a high "nearly done" value
            
            task.status = new_status
            task.save() 

            # Create History Log
            log=TaskHistory.objects.create(
            task=task,
            old_status=old_label,
            new_status=task.get_status_display(),
            changed_by=request.user
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'new_status': task.get_status_display(),
                    'progress': task.progress,
                    'log_user': request.user.username,
                    'log_old': old_label,
                    'log_new': task.get_status_display(),
                    'project_status': task.project.status,
                    'log_time': "just now"
                })
                
            messages.success(request, f'Status updated to {task.get_status_display()}.')
    return redirect('tasks:task_detail', pk=pk)







@login_required
def update_progress(request, pk):
    task = get_object_or_404(Task, pk=pk)
    user = request.user

    # Updated Permission Logic
    is_authorized = (
        user.profile.role in ['admin', 'manager'] or 
        task.project.team_lead == user or  # Added Team Lead check
        task.assigned_to == user
    )

    if task.project.status == 'inactive' or not is_authorized:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

    if request.method == 'POST':
        
        old_status_label = task.get_status_display()
        val = int(request.POST.get('progress', 0))

        project_tasks = task.project.tasks.all()
        overall_stats = project_tasks.aggregate(avg_progress=Avg('progress'))
        overall_completion = round(overall_stats['avg_progress'] or 0)



        # --- INTELLIGENT STATUS SYNC ---
        status_changed = False
        new_status = task.status

        # if val == 100 and task.status != 'completed':
        #     new_status = 'completed'
        #     status_changed = True
        # elif val == 0 and task.status != 'todo':
        #     new_status = 'todo'
        #     status_changed = True
        # elif 0 < val < 100 and task.status in ['completed', 'todo']:
        #     new_status = 'in_progress'
        #     status_changed = True
        
        # --- SLIDER PATTERN LOGIC ---
        if val == 100:
            new_status = 'completed'
        elif val == 0:
            if task.status != 'blocked': # Blocked can be 0% without being Todo
                new_status = 'todo'
        elif val == 90:
            new_status = 'in_review'
        else:
            # Any other movement (10-85%) forces In Progress if it was Todo/Done
            if task.status in ['todo', 'completed']:
                new_status = 'in_progress'
        
        if new_status != task.status:
            status_changed = True

        task.status = new_status
        task.progress = val
        # if val == 100:
        #     task.status = 'completed'
        # elif val == 0:
        #     task.status = 'todo'
        # # If the user slides away from 100 on a completed task, mark it active again
        # elif task.status == 'completed' and val < 100:
        #     task.status = 'in_progress'
        # # If the user slides away from 0 on a todo task, mark it active
        # elif task.status == 'todo' and val > 0:
        #     task.status = 'in_progress'
            
        task.save() 
        log_data = {}
        if status_changed:
            TaskHistory.objects.create(
                task=task,
                old_status=old_status_label,
                new_status=task.get_status_display(),
                changed_by=request.user
            )
            log_data = {
                'log_user': request.user.username,
                'log_old': old_status_label,
                'log_new': task.get_status_display(),
                'log_time': "just now"
            }

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            response_data={
                'status': 'success', 
                'progress': val,
                'new_status': task.get_status_display(),
                'overall_completion': overall_completion,
            }
            response_data.update(log_data)
            return JsonResponse(response_data)
            
        messages.success(request, f'Progress updated to {val}%.')
    return redirect('tasks:task_detail', pk=pk)

@login_required
def add_attachment(request, pk):
    # sourcery skip: merge-else-if-into-elif, reintroduce-else, use-fstring-for-concatenation
    task = get_object_or_404(Task, pk=pk)
    

    
    # Check if project is inactive
    if task.project.status == 'inactive':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Uploads are disabled for paused projects.'}, status=403)
        messages.error(request, 'Uploads are disabled for paused projects.')
        return redirect('tasks:task_detail', pk=pk)

    if request.method == 'POST':
        form = TaskAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                attachment = form.save(commit=False)
                attachment.task = task
                attachment.uploaded_by = request.user

                uploaded_file = request.FILES.get('file')
                if not uploaded_file:
                    return JsonResponse({'error': 'No file uploaded'}, status=400)
                
                filename = uploaded_file.name
                attachment.file_name = filename

                import os
                _, extension = os.path.splitext(filename)
                ext = extension.lstrip('.').lower()
                attachment.save()

                
                # TO THIS (Add the extension logic):
                # extension = attachment.file.url.split('.')[-1].lower()

                # 2. IMPORTANT: Append the extension to the public_id for Cloudinary to handle fl_attachment
                download_url, _ = cloudinary_url(
                    f"{attachment.file.public_id}.{ext}", # FIX: Append .extension here
                    resource_type="auto", 
                    flags="attachment",
                    attachment=attachment.file_name 
                )
                # AJAX Response
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'id': attachment.id,
                        'file_name': attachment.file_name,
                        'url': download_url,
                        'user': request.user.username,
                        'extension': ext
                    })
                
                messages.success(request, f'File "{attachment.file_name}" uploaded successfully.')
            except Exception as e:
                print(f"CLOUDINARY UPLOAD ERROR: {str(e)}") 
                return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Failed to upload file.'}, status=400)
            messages.error(request, "Failed to upload file. Please check the form.")
            
    return redirect('tasks:task_detail', pk=pk)

def download_attachment(request, pk):
    attachment = get_object_or_404(TaskAttachment, pk=pk)

    try:
        file_path = str(attachment.file)
        if file_path.startswith('media/'):
            file_path = file_path.replace('media/', '', 1)
            
            

        
        # Generate the URL with the attachment flag on the fly
        url, _ = cloudinary_url(
            file_path,
            resource_type='auto',
            flags="attachment",
            attachment=attachment.file_name, # Forces the Save As filename
            secure=True,
            sign_url=True
            )
    
        return HttpResponseRedirect(url)
    except Exception as e:
        # This will help you see the actual error in your Render logs
        print(f"CRITICAL DOWNLOAD ERROR [ID {pk}]: {str(e)}")
        return HttpResponseRedirect("Error generating download link.", status=500)

@login_required
def delete_attachment(request, pk):
    attachment = get_object_or_404(TaskAttachment, pk=pk)
    task_pk = attachment.task.pk
    
    # Permission Check: Only uploader or Admin/Manager can delete
    if request.user == attachment.uploaded_by or request.user.profile.role in ['admin', 'manager']:
        attachment.delete()
        
        # AJAX Response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Attachment removed.'})
            
        messages.success(request, "Attachment removed successfully.")
    else:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Permission denied.'}, status=403)
        messages.error(request, "You do not have permission to delete this file.")
        
    return redirect('tasks:task_detail', pk=task_pk)


@login_required
def clear_task_history(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    # Permission Check: Only Admin/Manager can wipe history
    if request.user.profile.role not in ['admin', 'manager']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        # This deletes all TaskHistory objects related to this task
        task.history.all().delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Timeline cleared.'})
            
        messages.success(request, 'History cleared.')
    return redirect('tasks:task_detail', pk=pk)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q, Avg, Count, Case, When, IntegerField
from django.contrib.auth.models import User 
from .models import Project
from .forms import ProjectForm
from django.http import JsonResponse
from django.template.loader import render_to_string



# def get_project_members(request, project_id):
#     project = get_object_or_404(Project, id=project_id)
    
#     # Use a dictionary to store users by ID to automatically prevent duplicates
#     # Key: User ID, Value: Username
#     unique_members = {user.id: user.username for user in project.team_members.all()}
    
#     # Add the lead if they aren't already there
#     if project.team_lead:
#         unique_members[project.team_lead.id] = f"{project.team_lead.username} (Lead)"

#     # Convert back to the list format your JavaScript expects
#     member_data = [
#         {'id': user_id, 'username': name} 
#         for user_id, name in unique_members.items()
#     ]

#     return JsonResponse({'members': member_data})

def get_project_members(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Combine lead and members into a single queryset using Union or simple iteration
    members = project.team_members.all().values('id', 'username')
    member_list = list(members)
    
    if project.team_lead:
        # Check if lead is already in list to avoid duplicates
        if not any(m['id'] == project.team_lead.id for m in member_list):
            member_list.append({
                'id': project.team_lead.id, 
                'username': f"{project.team_lead.username} (Lead)"
            })
            
    return JsonResponse({'members': member_list})



class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        # 1. Start with the basic queryset
        queryset = Project.objects.all()

        # 2. Permissions: If not a global 'admin', show only projects where the user is a member
        # This now works for Managers too because they are added to team_members by default
        # UPDATED: Allow both 'admin' and 'observer' to see all projects
        if user.profile.role not in ['admin','observer']:
            # queryset = queryset.filter(Q(team_members=user) | Q(tasks__assigned_to=user))
            queryset = queryset.filter(Q(team_lead=user) | Q(team_members=user) | Q(tasks__assigned_to=user))

        # 3. Handle Search and Filtering
        query = self.request.GET.get('q', '').strip()
        status_val = self.request.GET.get('status', '').strip().lower()

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
        
        if status_val:
            queryset = queryset.filter(status=status_val)

        # 4. Optimization: Prefetch and distinct are vital for ManyToMany filtering
        return queryset.prefetch_related('team_members').distinct().order_by('-created_at')

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Renders only the project grid partial for AJAX requests
            html = render_to_string('projects/includes/project_cards.html', context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        user = self.request.user
        # Admins and Observers can see everything
        if user.profile.role in ['admin', 'observer']:
            return Project.objects.all()
        
        # Managers and Developers can only see projects they are members of
        # This matches the logic you have in ProjectListView
        # return Project.objects.filter(
        #     Q(team_members=user) | Q(team_lead=user)
        # ).distinct()
        return Project.objects.filter(
            Q(team_members=user) | Q(team_lead=user) |Q(tasks__assigned_to=user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        stats = project.tasks.aggregate(
            total=Count('id'),
            # todo=Count(Case(When(status='todo', then=1), output_field=IntegerField())),
            # in_progress=Count(Case(When(status='in_progress', then=1), output_field=IntegerField())),
            # completed=Count(Case(When(status='completed', then=1), output_field=IntegerField())),
            todo=Count('id', filter=Q(status='todo')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            completed=Count('id', filter=Q(status='completed')),
            avg_progress=Avg('progress')
        )

        context['task_counts'] = stats
        context['project_progress'] = round(stats['avg_progress'] or 0)
        context['all_tasks'] = project.tasks.select_related('assigned_to').all()
        context['my_tasks'] = context['all_tasks'].filter(assigned_to=self.request.user)
        return context

class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def test_func(self):
        return self.request.user.profile.role in ['admin', 'manager']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        try:
            with transaction.atomic():
                self.object = form.save()
                # if self.request.user not in self.object.team_members.all():
                #     self.object.team_members.add(self.request.user)
            
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'redirect_url': str(reverse_lazy('projects:project_list'))})
            return redirect('projects:project_list')
        except Exception as e:
            form.add_error(None, f"Critical Error: {str(e)}")
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            return self.form_invalid(form)
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # Pass the logged-in user to the form
        return kwargs

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def test_func(self):
        # Rights: Only Leads/Managers/Admins
        if self.request.user.profile.role == 'observer':
            return False

        project = self.get_object()
        return self.request.user.profile.role in ['admin', 'manager'] or project.team_lead == self.request.user

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # Pass the logged-in user to the form
        return kwargs

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects:project_list')

    def test_func(self):
        return self.request.user.profile.role in ['admin', 'manager']

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.tasks.filter(status='in_progress').exists():
            msg = "Cannot delete a project with tasks in progress."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': msg}, status=400)
            messages.error(self.request, msg)
            return redirect('projects:project_detail', pk=self.object.pk)
        
        self.object.delete()
        success_msg = f"Project '{self.object.title}' was successfully deleted."
        messages.success(self.request, success_msg)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'redirect_url': str(self.success_url)})
        return redirect(self.success_url)
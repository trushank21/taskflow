import django_filters

from projects.models import Project
from .models import Task

class TaskFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        widget=django_filters.widgets.forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title...'
        })
    )
    
    project = django_filters.ModelChoiceFilter(
        # queryset=None,
        queryset=Project.objects.all(),
        empty_label='All Projects',
        widget=django_filters.widgets.forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = django_filters.ChoiceFilter(
        choices=Task.STATUS_CHOICES,
        empty_label='All Status',
        widget=django_filters.widgets.forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    priority = django_filters.ChoiceFilter(
        choices=Task.PRIORITY_CHOICES,
        empty_label='All Priority',
        widget=django_filters.widgets.forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    assigned_to = django_filters.ModelChoiceFilter(
        queryset=None,
        empty_label='All Users',
        widget=django_filters.widgets.forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    due_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    project_status = django_filters.ChoiceFilter(
        field_name='project__status',
        choices=(('active', 'Active Projects'), ('inactive', 'Paused Projects')),
        label='Project Status',
        widget=django_filters.widgets.forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Task
        fields = ['title', 'project', 'status', 'priority', 'assigned_to', 'due_date', 'project_status']
        
    def __init__(self, *args, **kwargs):

        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)
        from projects.models import Project
        from django.contrib.auth.models import User
        from django.db.models import Q

        # self.filters['project'].field.queryset = Project.objects.all()
        # self.filters['assigned_to'].field.queryset = User.objects.filter(
        #     profile__role='developer'
        # ).select_related('profile')

        if user:
            # 1. Filter Projects: Show only projects where user is lead or member
            self.filters['project'].field.queryset = Project.objects.filter(
                Q(team_lead=user) | Q(team_members=user)
            ).distinct()

            # 2. Filter Users: Show only people who share a project with the current user
            # This prevents seeing every developer in the whole system
            shared_projects = Project.objects.filter(
                Q(team_lead=user) | Q(team_members=user)
            ).distinct()

            # Use the correct related_name identifiers found in your error message
            self.filters['assigned_to'].field.queryset = User.objects.filter(
                Q(projects_assigned__in=shared_projects) | 
                Q(led_projects__in=shared_projects)
            ).distinct().select_related('profile')
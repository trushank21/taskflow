from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'team_lead', 'created_by', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'created_at', 'start_date')
    search_fields = ('title', 'description')
    filter_horizontal = ('team_members',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Project Info', {'fields': ('title', 'description', 'status')}),
        ('Team', {'fields': ('created_by', 'team_lead', 'team_members')}),
        ('Dates', {'fields': ('start_date', 'end_date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

from django.contrib import admin
from .models import Task, TaskComment, TaskAttachment

class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ('created_at',)
    # readonly_fields = ('created_at', 'updated_at')
    # fields = ('commented_by', 'comment', 'created_at')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Set default user for commented_by"""
        if db_field.name == 'commented_by':
            kwargs['initial'] = request.user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0
    # extra = 1
    # readonly_fields = ('uploaded_by', 'uploaded_at')
    # fields = ('file', 'file_name', 'uploaded_by')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'status', 'priority', 'due_date', 'progress', 'created_at')
    list_filter = ('status', 'priority', 'project', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'project__title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TaskCommentInline, TaskAttachmentInline]
    fieldsets = (
        ('Task Info', {'fields': ('title', 'description', 'project')}),
        ('Assignment', {'fields': ('assigned_to', 'assigned_by')}),
        ('Status', {'fields': ('status', 'priority', 'progress')}),
        ('Details', {'fields': ('due_date', 'estimated_hours', 'actual_hours', 'tags')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'commented_by', 'created_at')
    list_filter = ('created_at', 'task__project')
    search_fields = ('task__title', 'comment')
    readonly_fields = ('task', 'commented_by', 'created_at', 'updated_at')

@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'file_name', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at', 'task__project')
    search_fields = ('task__title', 'file_name')
    readonly_fields = ('task', 'uploaded_by', 'uploaded_at')

from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'department')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Info', {'fields': ('user', 'role')}),
        ('Personal', {'fields': ('department', 'phone', 'bio')}),
        ('Avatar', {'fields': ('avatar',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

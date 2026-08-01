from django.contrib import admin
from .models import UserProfile, Resume, Job, SkillAnalysis, Notification


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email']


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['user', 'resume_file', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['user__username']
    readonly_fields = ['extracted_text']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'hr', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'hr__username']


@admin.register(SkillAnalysis)
class SkillAnalysisAdmin(admin.ModelAdmin):
    list_display = ['resume', 'job', 'match_score', 'gap_percentage', 'readiness_level', 'analyzed_at']
    list_filter = ['readiness_level', 'analyzed_at']
    search_fields = ['resume__user__username', 'job__title']
    readonly_fields = ['matched_skills', 'missing_skills']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'message']
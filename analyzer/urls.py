from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Candidate URLs
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('analyze-resume/<int:resume_id>/<int:job_id>/', views.analyze_resume, name='analyze_resume'),
    path('analysis-result/<int:analysis_id>/', views.analysis_result, name='analysis_result'),
    path('analysis-status/<int:analysis_id>/', views.check_analysis_status, name='check_analysis_status'),
    path('resume-history/', views.resume_history, name='resume_history'),
    path('notifications/', views.notifications, name='notifications'),
    path('mark-notification-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    
    # HR URLs
    path('hr-dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('create-job/', views.create_job, name='create_job'),
    path('job-list/', views.job_list, name='job_list'),
    path('job-detail/<int:job_id>/', views.job_detail, name='job_detail'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('filter-resumes/', views.filter_resumes, name='filter_resumes'),
    path('candidate-detail/<int:analysis_id>/', views.candidate_detail, name='candidate_detail'),
    path('accept-candidate/<int:analysis_id>/', views.accept_candidate, name='accept_candidate'),
    path('reject-candidate/<int:analysis_id>/', views.reject_candidate, name='reject_candidate'),
    path('send-feedback/<int:analysis_id>/', views.send_feedback, name='send_feedback'),
    path('analytics/', views.analytics, name='analytics'),
    path('export-analysis/<int:analysis_id>/<str:format>/', views.export_analysis, name='export_analysis'),
    
    # AJAX URLs
    path('get-jobs/', views.get_jobs, name='get_jobs'),
    path('check-password-strength/', views.check_password_strength, name='check_password_strength'),
    path('available-jobs/', views.available_jobs, name='available_jobs'),
    path('test-skills/', views.test_skills, name='test_skills'),
    path('candidate-view/', views.candidate_view, name='candidate_view'),
]
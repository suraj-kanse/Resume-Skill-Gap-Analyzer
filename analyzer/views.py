from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.auth.models import User
import json
import os
import re
import threading
from django.db import connection
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from .models import UserProfile, Resume, Job, SkillAnalysis, Notification
from .forms import CustomUserCreationForm, ResumeUploadForm, JobCreationForm, BulkResumeUploadForm, FilterForm
from .utils import (
    extract_text_from_resume, extract_skills_from_text, calculate_skill_match,
    determine_readiness_level, parse_skills_from_string, format_skills_list,
    get_skill_suggestions
)


def process_analysis_async(analysis_id):
    """Run resume text extraction and skill analysis in a background thread"""
    try:
        analysis = SkillAnalysis.objects.get(id=analysis_id)
        analysis.status = 'PROCESSING'
        analysis.save()
        
        resume = analysis.resume
        # Extract text from resume if not already done
        if not resume.extracted_text:
            extracted_text = extract_text_from_resume(resume.resume_file)
            resume.extracted_text = extracted_text
            resume.save()
            
        resume_skills = extract_skills_from_text(resume.extracted_text)
        job_skills = parse_skills_from_string(analysis.job.required_skills)
        
        match_result = calculate_skill_match(resume_skills, job_skills)
        
        analysis.matched_skills = format_skills_list(match_result['matched_skills'])
        analysis.missing_skills = format_skills_list(match_result['missing_skills'])
        analysis.gap_percentage = match_result['gap_percentage']
        analysis.match_score = match_result['match_score']
        analysis.readiness_level = determine_readiness_level(match_result['match_score'])
        analysis.status = 'COMPLETED'
        analysis.save()
    except Exception as e:
        try:
            analysis = SkillAnalysis.objects.get(id=analysis_id)
            analysis.status = 'FAILED'
            # fallback defaults
            analysis.matched_skills = ''
            analysis.missing_skills = analysis.job.required_skills
            analysis.gap_percentage = 100
            analysis.match_score = 0
            analysis.readiness_level = 'BEGINNER'
            analysis.save()
        except:
            pass
    finally:
        connection.close()


def home(request):
    """Home page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'auth/home.html')


def custom_login(request):
    """Custom login view with role-based redirection"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            try:
                profile = user.userprofile
                if profile.role == 'HR':
                    return redirect('hr_dashboard')
                else:
                    return redirect('dashboard')
            except UserProfile.DoesNotExist:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')


def signup(request):
    """User registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            
            # Create user profile
            UserProfile.objects.create(user=user, role=role)
            
            # Login user
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            messages.success(request, 'Account created successfully!')
            
            if role == 'HR':
                return redirect('hr_dashboard')
            else:
                return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'auth/signup.html', {'form': form})


@login_required
def dashboard(request):
    """Candidate dashboard"""
    try:
        profile = request.user.userprofile
        if profile.role == 'HR':
            return redirect('hr_dashboard')
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user, role='USER')
    
    # Get user's resumes and analyses
    resumes = Resume.objects.filter(user=request.user)[:5]
    analyses = SkillAnalysis.objects.filter(resume__user=request.user)[:5]
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    jobs = Job.objects.all()[:10]
    
    context = {
        'resumes': resumes,
        'analyses': analyses,
        'notifications': notifications,
        'jobs': jobs,
        'total_resumes': resumes.count(),
        'total_analyses': analyses.count(),
        'unread_notifications': notifications.count(),
    }
    
    return render(request, 'user/dashboard.html', context)


@login_required
def hr_dashboard(request):
    """HR dashboard"""
    try:
        profile = request.user.userprofile
        if profile.role != 'HR':
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get HR statistics
    jobs = Job.objects.filter(hr=request.user)
    analyses = SkillAnalysis.objects.filter(job__hr=request.user)
    
    context = {
        'total_jobs': jobs.count(),
        'total_analyses': analyses.count(),
        'avg_match_score': analyses.aggregate(Avg('match_score'))['match_score__avg'] or 0,
        'recent_jobs': jobs[:5],
        'recent_analyses': analyses[:10],
    }
    
    return render(request, 'hr/dashboard.html', context)


@login_required
def upload_resume(request):
    """Upload resume"""
    # Check if HR user is accessing this page
    is_hr_user = False
    try:
        profile = request.user.userprofile
        if profile.role == 'HR':
            is_hr_user = True
    except UserProfile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()
            
            # Extract text from resume
            try:
                extracted_text = extract_text_from_resume(resume.resume_file)
                resume.extracted_text = extracted_text
                resume.save()
                messages.success(request, 'Resume uploaded and processed successfully!')
            except Exception as e:
                messages.warning(request, f'Resume uploaded but text extraction failed: {str(e)}')
            
            # Redirect based on user type
            if is_hr_user:
                return redirect('candidate_view')
            else:
                return redirect('resume_history')
    else:
        form = ResumeUploadForm()
    
    context = {
        'form': form,
        'is_hr_user': is_hr_user
    }
    
    return render(request, 'user/upload_resume.html', context)


@login_required
def analyze_resume(request, resume_id, job_id):
    """Analyze resume against job requirements"""
    resume = get_object_or_404(Resume, id=resume_id)
    job = get_object_or_404(Job, id=job_id)
    
    # Check permissions
    if resume.user and resume.user != request.user:
        try:
            profile = request.user.userprofile
            if profile.role != 'HR' or job.hr != request.user:
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    elif not resume.user:
        try:
            profile = request.user.userprofile
            if profile.role != 'HR' or job.hr != request.user:
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
            
    # Check if analysis already exists
    analysis, created = SkillAnalysis.objects.get_or_create(
        resume=resume,
        job=job,
        defaults={
            'matched_skills': '',
            'missing_skills': '',
            'gap_percentage': 0,
            'match_score': 0,
            'readiness_level': 'BEGINNER',
            'status': 'PENDING'
        }
    )
    
    # If newly created or status is not completed/processing, start analysis
    if created or analysis.status in ['PENDING', 'FAILED']:
        if getattr(settings, 'IS_SERVERLESS', False):
            # Run synchronously on serverless to avoid frozen threads
            process_analysis_async(analysis.id)
        else:
            # Run asynchronously on traditional server
            analysis.status = 'PENDING'
            analysis.save()
            thread = threading.Thread(target=process_analysis_async, args=(analysis.id,))
            thread.daemon = True
            thread.start()
        
    return redirect('analysis_result', analysis_id=analysis.id)


@login_required
def analysis_result(request, analysis_id):
    """Display analysis result"""
    analysis = get_object_or_404(SkillAnalysis, id=analysis_id)
    
    # Check access permissions
    if analysis.resume.user != request.user:
        try:
            profile = request.user.userprofile
            if profile.role != 'HR' or analysis.job.hr != request.user:
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    
    # Get skill suggestions
    missing_skills = parse_skills_from_string(analysis.missing_skills)
    matched_skills = parse_skills_from_string(analysis.matched_skills)
    suggestions = get_skill_suggestions(missing_skills, matched_skills)
    
    context = {
        'analysis': analysis,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'suggestions': suggestions,
    }
    
    return render(request, 'user/analysis_result.html', context)


@login_required
def resume_history(request):
    """Resume history"""
    resumes = Resume.objects.filter(user=request.user)
    jobs = Job.objects.all()  # Get all available jobs for analysis
    paginator = Paginator(resumes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'user/resume_history.html', {
        'page_obj': page_obj,
        'jobs': jobs
    })


@login_required
def notifications(request):
    """User notifications"""
    notifications = Notification.objects.filter(user=request.user)
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'user/notifications.html', {'page_obj': page_obj})


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')


@login_required
def create_job(request):
    """Create job posting (HR only)"""
    try:
        profile = request.user.userprofile
        if profile.role != 'HR':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = JobCreationForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.hr = request.user
            job.save()
            messages.success(request, 'Job created successfully!')
            return redirect('job_list')
    else:
        form = JobCreationForm()
    
    return render(request, 'hr/create_job.html', {'form': form})


@login_required
def job_list(request):
    """Job list (HR only)"""
    try:
        profile = request.user.userprofile
        if profile.role != 'HR':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    jobs = Job.objects.filter(hr=request.user)
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'hr/job_list.html', {'page_obj': page_obj})


@login_required
def job_detail(request, job_id):
    """Job detail with candidates"""
    job = get_object_or_404(Job, id=job_id)
    
    try:
        profile = request.user.userprofile
        if profile.role != 'HR' or job.hr != request.user:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    analyses = SkillAnalysis.objects.filter(job=job).order_by('-match_score')
    
    context = {
        'job': job,
        'analyses': analyses,
        'total_candidates': analyses.count(),
    }
    
    return render(request, 'hr/job_detail.html', context)


@login_required
def bulk_upload(request):
    """Bulk resume upload (HR only)"""
    try:
        profile = request.user.userprofile
        if profile.role != 'HR':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BulkResumeUploadForm(request.POST, request.FILES)
        job_id = request.POST.get('job_id')
        
        if form.is_valid() and job_id:
            job = get_object_or_404(Job, id=job_id, hr=request.user)
            files = form.cleaned_data['resumes']
            
            # Handle single file case
            if not isinstance(files, list):
                files = [files]
            
            uploaded_count = 0
            analyzed_count = 0
            
            for file in files:
                try:
                    # Clean filename to get candidate name
                    base_name = os.path.splitext(file.name)[0]
                    candidate_name = base_name.replace('_', ' ').replace('-', ' ').title()
                    candidate_email = f"{base_name.lower()}@example.com"
                    
                    # Create resume
                    resume = Resume.objects.create(
                        user=None,
                        candidate_name=candidate_name,
                        candidate_email=candidate_email,
                        resume_file=file
                    )
                    
                    uploaded_count += 1
                    
                    # Create analysis record as PENDING
                    analysis = SkillAnalysis.objects.create(
                        resume=resume,
                        job=job,
                        matched_skills='',
                        missing_skills='',
                        gap_percentage=0,
                        match_score=0,
                        readiness_level='BEGINNER',
                        status='PENDING'
                    )
                    
                    # Run analysis
                    if getattr(settings, 'IS_SERVERLESS', False):
                        # Run synchronously on serverless to avoid frozen threads
                        process_analysis_async(analysis.id)
                    else:
                        # Run asynchronously on traditional server
                        thread = threading.Thread(target=process_analysis_async, args=(analysis.id,))
                        thread.daemon = True
                        thread.start()
                    
                    analyzed_count += 1
                    
                except Exception as e:
                    messages.warning(request, f'Error processing {file.name}: {str(e)}')
            
            messages.success(request, f'Successfully uploaded {uploaded_count} resumes and started analysis for {analyzed_count}.')
            return redirect('job_detail', job_id=job.id)
    else:
        form = BulkResumeUploadForm()
    
    jobs = Job.objects.filter(hr=request.user)
    return render(request, 'hr/bulk_upload.html', {'form': form, 'jobs': jobs})


@login_required
def filter_resumes(request):
    """Filter and search resumes (HR only)"""
    try:
        profile = request.user.userprofile
        if profile.role != 'HR':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    form = FilterForm(request.GET, user=request.user)
    analyses = SkillAnalysis.objects.filter(job__hr=request.user)
    
    if form.is_valid():
        if form.cleaned_data['min_match_score']:
            analyses = analyses.filter(match_score__gte=form.cleaned_data['min_match_score'])
        
        if form.cleaned_data['max_gap_percentage']:
            analyses = analyses.filter(gap_percentage__lte=form.cleaned_data['max_gap_percentage'])
        
        if form.cleaned_data['readiness_level']:
            analyses = analyses.filter(readiness_level=form.cleaned_data['readiness_level'])
        
        if form.cleaned_data['job']:
            analyses = analyses.filter(job=form.cleaned_data['job'])
    
    analyses = analyses.order_by('-match_score')
    paginator = Paginator(analyses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'hr/filter_resumes.html', {
        'form': form,
        'page_obj': page_obj,
        'total_results': analyses.count()
    })


@login_required
def candidate_detail(request, analysis_id):
    """Candidate detail view (HR only)"""
    analysis = get_object_or_404(SkillAnalysis, id=analysis_id)
    
    try:
        profile = request.user.userprofile
        if profile.role != 'HR' or analysis.job.hr != request.user:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    matched_skills = parse_skills_from_string(analysis.matched_skills)
    missing_skills = parse_skills_from_string(analysis.missing_skills)
    suggestions = get_skill_suggestions(missing_skills, matched_skills)
    
    context = {
        'analysis': analysis,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'suggestions': suggestions,
    }
    
    return render(request, 'hr/candidate_detail.html', context)


@login_required
def accept_candidate(request, analysis_id):
    """Accept candidate (HR only)"""
    analysis = get_object_or_404(SkillAnalysis, id=analysis_id)
    
    try:
        profile = request.user.userprofile
        if profile.role != 'HR' or analysis.job.hr != request.user:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    candidate_name = (analysis.resume.user.get_full_name() or analysis.resume.user.username) if analysis.resume.user else (analysis.resume.candidate_name or "Anonymous")
    
    # Create notification if candidate has a user account
    if analysis.resume.user:
        message = f"Congratulations! Your resume has been accepted for the position: {analysis.job.title}"
        Notification.objects.create(
            user=analysis.resume.user,
            message=message
        )
    
    messages.success(request, f'Candidate {candidate_name} accepted.')
    return redirect('candidate_detail', analysis_id=analysis_id)


@login_required
def reject_candidate(request, analysis_id):
    """Reject candidate (HR only)"""
    analysis = get_object_or_404(SkillAnalysis, id=analysis_id)
    
    try:
        profile = request.user.userprofile
        if profile.role != 'HR' or analysis.job.hr != request.user:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    candidate_name = (analysis.resume.user.get_full_name() or analysis.resume.user.username) if analysis.resume.user else (analysis.resume.candidate_name or "Anonymous")
    
    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        
        # Create notification if candidate has a user account
        if analysis.resume.user:
            message = f"Your resume for the position '{analysis.job.title}' was not selected. "
            if feedback:
                message += f"Feedback: {feedback}"
            
            Notification.objects.create(
                user=analysis.resume.user,
                message=message
            )
        
        messages.success(request, f'Candidate {candidate_name} rejected.')
        return redirect('candidate_detail', analysis_id=analysis_id)
    
    return render(request, 'hr/reject_candidate.html', {'analysis': analysis})


@login_required
def send_feedback(request, analysis_id):
    """Send feedback to candidate (HR only)"""
    analysis = get_object_or_404(SkillAnalysis, id=analysis_id)
    
    try:
        profile = request.user.userprofile
        if profile.role != 'HR' or analysis.job.hr != request.user:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    candidate_name = (analysis.resume.user.get_full_name() or analysis.resume.user.username) if analysis.resume.user else (analysis.resume.candidate_name or "Anonymous")
    
    if request.method == 'POST':
        feedback = request.POST.get('feedback', '')
        
        if feedback:
            if analysis.resume.user:
                missing_skills = parse_skills_from_string(analysis.missing_skills)
                matched_skills = parse_skills_from_string(analysis.matched_skills)
                suggestions = get_skill_suggestions(missing_skills, matched_skills)
                
                message = f"Feedback for your application to '{analysis.job.title}': {feedback}\n\n"
                message += "Skill Improvement Suggestions:\n"
                for suggestion in suggestions:
                    message += f"• {suggestion}\n"
                
                Notification.objects.create(
                    user=analysis.resume.user,
                    message=message
                )
            
            messages.success(request, f'Feedback sent to candidate {candidate_name}.')
            return redirect('candidate_detail', analysis_id=analysis_id)
            
    missing_skills = parse_skills_from_string(analysis.missing_skills)
    matched_skills = parse_skills_from_string(analysis.matched_skills)
    suggestions = get_skill_suggestions(missing_skills, matched_skills)
    
    context = {
        'analysis': analysis,
        'suggestions': suggestions,
    }
    
    return render(request, 'hr/send_feedback.html', context)


@login_required
def analytics(request):
    """HR analytics dashboard"""
    try:
        profile = request.user.userprofile
        if profile.role != 'HR':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    analyses = SkillAnalysis.objects.filter(job__hr=request.user)
    jobs = Job.objects.filter(hr=request.user)
    
    # Calculate statistics
    total_resumes = analyses.count()
    total_candidates = analyses.values('resume__user').distinct().count()
    avg_gap = analyses.aggregate(Avg('gap_percentage'))['gap_percentage__avg'] or 0
    avg_match = analyses.aggregate(Avg('match_score'))['match_score__avg'] or 0
    
    # Top missing skills
    all_missing_skills = []
    for analysis in analyses:
        if analysis.missing_skills:
            skills = parse_skills_from_string(analysis.missing_skills)
            all_missing_skills.extend(skills)
    
    from collections import Counter
    skill_counter = Counter(all_missing_skills)
    top_missing_skills = skill_counter.most_common(5)
    
    # Job-wise statistics
    job_stats = []
    for job in jobs:
        job_analyses = analyses.filter(job=job)
        if job_analyses.exists():
            job_stats.append({
                'job': job,
                'total_candidates': job_analyses.count(),
                'avg_match_score': job_analyses.aggregate(Avg('match_score'))['match_score__avg'] or 0,
                'top_candidate': job_analyses.order_by('-match_score').first()
            })
    
    context = {
        'total_resumes': total_resumes,
        'total_candidates': total_candidates,
        'avg_gap': round(avg_gap, 2),
        'avg_match': round(avg_match, 2),
        'top_missing_skills': top_missing_skills,
        'job_stats': job_stats,
    }
    
    return render(request, 'hr/analytics.html', context)


@login_required
def export_analysis(request, analysis_id, format):
    """Export analysis as PDF or JSON"""
    analysis = get_object_or_404(SkillAnalysis, id=analysis_id)
    
    # Check access permissions
    if analysis.resume.user != request.user:
        try:
            profile = request.user.userprofile
            if profile.role != 'HR' or analysis.job.hr != request.user:
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    
    candidate_name = (analysis.resume.user.get_full_name() or analysis.resume.user.username) if analysis.resume.user else (analysis.resume.candidate_name or "Anonymous")

    if format == 'json':
        data = {
            'candidate': candidate_name,
            'job_title': analysis.job.title,
            'match_score': analysis.match_score,
            'gap_percentage': analysis.gap_percentage,
            'readiness_level': analysis.get_readiness_level_display(),
            'matched_skills': parse_skills_from_string(analysis.matched_skills),
            'missing_skills': parse_skills_from_string(analysis.missing_skills),
            'analyzed_at': analysis.analyzed_at.isoformat(),
        }
        
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="analysis_{analysis_id}.json"'
        return response
    
    elif format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="analysis_{analysis_id}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
        )
        story.append(Paragraph("Skill Gap Analysis Report", title_style))
        story.append(Spacer(1, 12))
        
        # Basic info
        info_data = [
            ['Candidate:', candidate_name],
            ['Job Title:', analysis.job.title],
            ['Match Score:', f"{analysis.match_score}%"],
            ['Gap Percentage:', f"{analysis.gap_percentage}%"],
            ['Readiness Level:', analysis.get_readiness_level_display()],
            ['Analysis Date:', analysis.analyzed_at.strftime('%Y-%m-%d %H:%M')],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Skills sections
        matched_skills = parse_skills_from_string(analysis.matched_skills)
        missing_skills = parse_skills_from_string(analysis.missing_skills)
        
        if matched_skills:
            story.append(Paragraph("Matched Skills:", styles['Heading2']))
            for skill in matched_skills:
                story.append(Paragraph(f"• {skill}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        if missing_skills:
            story.append(Paragraph("Missing Skills:", styles['Heading2']))
            for skill in missing_skills:
                story.append(Paragraph(f"• {skill}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Suggestions
        suggestions = get_skill_suggestions(missing_skills, matched_skills)
        if suggestions:
            story.append(Paragraph("Improvement Suggestions:", styles['Heading2']))
            for suggestion in suggestions:
                story.append(Paragraph(f"• {suggestion}", styles['Normal']))
        
        doc.build(story)
        return response
    
    return redirect('analysis_result', analysis_id=analysis_id)


@login_required
def available_jobs(request):
    """Show all available jobs for candidates"""
    jobs = Job.objects.all().order_by('-created_at')
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'user/available_jobs.html', {'page_obj': page_obj})


@login_required
def get_jobs(request):
    """AJAX endpoint to get jobs (paginated with search support)"""
    search_query = request.GET.get('search', '')
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
    except ValueError:
        page = 1
        limit = 10
    
    jobs = Job.objects.all().order_by('-created_at')
    if search_query:
        jobs = jobs.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
        
    paginator = Paginator(jobs, limit)
    try:
        jobs_page = paginator.page(page)
    except Exception:
        jobs_page = []
        
    jobs_list = []
    if jobs_page:
        jobs_list = list(jobs_page.object_list.values('id', 'title', 'hr__username'))
        
    return JsonResponse({
        'jobs': jobs_list,
        'has_next': jobs_page.has_next() if jobs_page else False,
        'total_pages': paginator.num_pages,
        'current_page': page
    })


@csrf_exempt
def check_password_strength(request):
    """AJAX endpoint to check password strength"""
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        strength = 0
        feedback = []
        
        if len(password) >= 8:
            strength += 1
        else:
            feedback.append("At least 8 characters")
        
        if re.search(r'[A-Z]', password):
            strength += 1
        else:
            feedback.append("One uppercase letter")
        
        if re.search(r'[a-z]', password):
            strength += 1
        else:
            feedback.append("One lowercase letter")
        
        if re.search(r'\d', password):
            strength += 1
        else:
            feedback.append("One number")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            strength += 1
        else:
            feedback.append("One special character")
        
        strength_levels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']
        strength_level = strength_levels[min(strength, 4)]
        
        return JsonResponse({
            'strength': strength,
            'strength_level': strength_level,
            'feedback': feedback
        })
    
    return JsonResponse({'error': 'Invalid request'})


def test_skills(request):
    """Test skill extraction functionality"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    sample_text = """
    I am a Python developer with 5 years of experience in Django web development.
    I have worked with MySQL, PostgreSQL databases and have experience with JavaScript, HTML, CSS.
    I am familiar with Git version control, Docker containerization, and AWS cloud services.
    I have experience with React.js, Node.js, and REST API development.
    I also have knowledge of Machine Learning using TensorFlow and Scikit-learn.
    """
    
    extracted_skills = extract_skills_from_text(sample_text)
    
    job_skills = ['Python', 'Django', 'MySQL', 'JavaScript', 'React', 'AWS', 'Docker']
    match_result = calculate_skill_match(extracted_skills, job_skills)
    
    context = {
        'sample_text': sample_text,
        'extracted_skills': extracted_skills,
        'job_skills': job_skills,
        'match_result': match_result,
    }
    
    return render(request, 'test_skills.html', context)

@login_required
def candidate_view(request):
    """Allow HR users to view candidate dashboard"""
    try:
        profile = request.user.userprofile
        if profile.role != 'HR':
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get candidate-like data for HR to see the candidate experience
    # Show all resumes and jobs from HR perspective but in candidate view
    resumes = Resume.objects.all()[:5]  # Show all resumes for HR to understand candidate experience
    analyses = SkillAnalysis.objects.filter(job__hr=request.user)[:5]
    notifications = Notification.objects.all()[:5]  # Show sample notifications
    jobs = Job.objects.all()[:10]
    
    context = {
        'resumes': resumes,
        'analyses': analyses,
        'notifications': notifications,
        'jobs': jobs,
        'total_resumes': resumes.count(),
        'total_analyses': analyses.count(),
        'unread_notifications': notifications.count(),
        'is_hr_viewing': True,  # Flag to indicate HR is viewing candidate dashboard
    }
    
    return render(request, 'user/dashboard.html', context)


@login_required
def check_analysis_status(request, analysis_id):
    """AJAX endpoint to check the status of a skill analysis"""
    analysis = get_object_or_404(SkillAnalysis, id=analysis_id)
    
    # Check permissions
    if analysis.resume.user:
        if analysis.resume.user != request.user:
            try:
                profile = request.user.userprofile
                if profile.role != 'HR' or analysis.job.hr != request.user:
                    return JsonResponse({'error': 'Access denied'}, status=403)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'Access denied'}, status=403)
    else:
        try:
            profile = request.user.userprofile
            if profile.role != 'HR' or analysis.job.hr != request.user:
                return JsonResponse({'error': 'Access denied'}, status=403)
        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'Access denied'}, status=403)
            
    return JsonResponse({
        'status': analysis.status,
        'match_score': analysis.match_score,
        'gap_percentage': analysis.gap_percentage,
        'readiness_level': analysis.get_readiness_level_display()
    })
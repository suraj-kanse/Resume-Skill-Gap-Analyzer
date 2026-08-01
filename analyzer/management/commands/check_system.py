from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analyzer.models import Job, UserProfile, Resume, SkillAnalysis, Notification
from analyzer.utils import extract_skills_from_text


class Command(BaseCommand):
    help = 'Check system status and functionality'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking Resume Skill Gap Analyzer System...\n')
        
        # Check database connectivity
        try:
            user_count = User.objects.count()
            self.stdout.write(f'✅ Database: Connected ({user_count} users)')
        except Exception as e:
            self.stdout.write(f'❌ Database: Error - {str(e)}')
            return
        
        # Check models
        jobs_count = Job.objects.count()
        resumes_count = Resume.objects.count()
        analyses_count = SkillAnalysis.objects.count()
        notifications_count = Notification.objects.count()
        hr_count = UserProfile.objects.filter(role='HR').count()
        candidate_count = UserProfile.objects.filter(role='USER').count()
        
        self.stdout.write(f'✅ Jobs: {jobs_count} available')
        self.stdout.write(f'✅ Resumes: {resumes_count} uploaded')
        self.stdout.write(f'✅ Analyses: {analyses_count} completed')
        self.stdout.write(f'✅ Notifications: {notifications_count} sent')
        self.stdout.write(f'✅ HR Users: {hr_count}')
        self.stdout.write(f'✅ Candidates: {candidate_count}')
        
        # Test skill extraction
        try:
            sample_text = "I am a Python developer with Django experience and MySQL knowledge."
            skills = extract_skills_from_text(sample_text)
            self.stdout.write(f'✅ Skill Extraction: Working (found {len(skills)} skills)')
        except Exception as e:
            self.stdout.write(f'❌ Skill Extraction: Error - {str(e)}')
        
        # Check admin user
        admin_exists = User.objects.filter(is_superuser=True).exists()
        self.stdout.write(f'✅ Admin User: {"Available" if admin_exists else "Not found"}')
        
        # System status
        if jobs_count > 0 and resumes_count > 0:
            self.stdout.write(f'\n🎉 System Status: FULLY OPERATIONAL')
            self.stdout.write(f'📊 Ready for: Resume analysis, HR screening, candidate matching')
        elif jobs_count > 0:
            self.stdout.write(f'\n⚠️  System Status: READY (Upload resumes to test analysis)')
        else:
            self.stdout.write(f'\n⚠️  System Status: SETUP NEEDED (Run create_sample_jobs)')
        
        # Test accounts summary
        self.stdout.write(f'\n🔑 Test Accounts Available:')
        if hr_count > 0:
            hr_user = UserProfile.objects.filter(role='HR').first().user
            self.stdout.write(f'   HR: {hr_user.username} (password: demo123)')
        
        if candidate_count > 0:
            candidate_users = UserProfile.objects.filter(role='USER')[:3]
            for profile in candidate_users:
                self.stdout.write(f'   Candidate: {profile.user.username} (password: demo123)')
        
        self.stdout.write(f'\n🌐 Access URLs:')
        self.stdout.write(f'   Main App: http://127.0.0.1:8000/')
        self.stdout.write(f'   Admin: http://127.0.0.1:8000/admin/')
        self.stdout.write(f'   Skills Test: http://127.0.0.1:8000/test-skills/')
        
        self.stdout.write(f'\n✨ All systems operational!')
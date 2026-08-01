from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analyzer.models import Job, UserProfile, Resume, SkillAnalysis, Notification
from analyzer.utils import extract_skills_from_text, calculate_skill_match, determine_readiness_level, format_skills_list, parse_skills_from_string
from django.core.files.base import ContentFile
import os


class Command(BaseCommand):
    help = 'Setup demo data for testing HR features'

    def handle(self, *args, **options):
        self.stdout.write('Setting up demo data...')
        
        # Create HR user
        hr_user, created = User.objects.get_or_create(
            username='hr_demo',
            defaults={
                'email': 'hr@demo.com',
                'first_name': 'HR',
                'last_name': 'Manager',
                'is_staff': False
            }
        )
        
        if created:
            hr_user.set_password('demo123')
            hr_user.save()
            self.stdout.write(f'Created HR user: {hr_user.username}')
        
        # Create HR profile
        hr_profile, created = UserProfile.objects.get_or_create(
            user=hr_user,
            defaults={'role': 'HR'}
        )
        
        # Create sample candidates
        candidates_data = [
            {
                'username': 'john_dev',
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Developer',
                'skills': 'Python, Django, MySQL, JavaScript, HTML, CSS, Git, REST API, Docker'
            },
            {
                'username': 'sarah_fullstack',
                'email': 'sarah@example.com',
                'first_name': 'Sarah',
                'last_name': 'Wilson',
                'skills': 'JavaScript, React, Node.js, MongoDB, HTML, CSS, Git, AWS, Express.js'
            },
            {
                'username': 'mike_data',
                'email': 'mike@example.com',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'skills': 'Python, Machine Learning, Pandas, NumPy, TensorFlow, SQL, Statistics'
            },
            {
                'username': 'lisa_frontend',
                'email': 'lisa@example.com',
                'first_name': 'Lisa',
                'last_name': 'Chen',
                'skills': 'JavaScript, React, Vue.js, HTML, CSS, Bootstrap, Webpack, Git'
            }
        ]
        
        created_candidates = []
        for candidate_data in candidates_data:
            user, created = User.objects.get_or_create(
                username=candidate_data['username'],
                defaults={
                    'email': candidate_data['email'],
                    'first_name': candidate_data['first_name'],
                    'last_name': candidate_data['last_name']
                }
            )
            
            if created:
                user.set_password('demo123')
                user.save()
                
                # Create user profile
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': 'USER'}
                )
                
                # Create sample resume with skills text
                resume_content = f"""
                {candidate_data['first_name']} {candidate_data['last_name']}
                Software Developer
                
                SKILLS:
                {candidate_data['skills']}
                
                EXPERIENCE:
                - 3+ years of software development experience
                - Worked on various web applications and projects
                - Strong problem-solving and analytical skills
                
                EDUCATION:
                - Bachelor's degree in Computer Science
                """
                
                # Create resume object
                resume = Resume.objects.create(
                    user=user,
                    extracted_text=resume_content
                )
                
                # Create a dummy file for the resume
                resume.resume_file.save(
                    f'{candidate_data["username"]}_resume.txt',
                    ContentFile(resume_content.encode()),
                    save=True
                )
                
                created_candidates.append((user, resume, candidate_data['skills']))
                self.stdout.write(f'Created candidate: {user.username}')
        
        # Get all jobs
        jobs = Job.objects.all()
        
        if not jobs.exists():
            self.stdout.write('No jobs found. Please run create_sample_jobs first.')
            return
        
        # Create skill analyses for each candidate against each job
        analysis_count = 0
        for user, resume, candidate_skills in created_candidates:
            for job in jobs:
                # Check if analysis already exists
                if not SkillAnalysis.objects.filter(resume=resume, job=job).exists():
                    # Extract skills from resume
                    resume_skills = extract_skills_from_text(resume.extracted_text)
                    
                    # Parse job skills
                    job_skills = parse_skills_from_string(job.required_skills)
                    
                    # Calculate match
                    match_result = calculate_skill_match(resume_skills, job_skills)
                    
                    # Create analysis
                    analysis = SkillAnalysis.objects.create(
                        resume=resume,
                        job=job,
                        matched_skills=format_skills_list(match_result['matched_skills']),
                        missing_skills=format_skills_list(match_result['missing_skills']),
                        gap_percentage=match_result['gap_percentage'],
                        match_score=match_result['match_score'],
                        readiness_level=determine_readiness_level(match_result['match_score'])
                    )
                    
                    analysis_count += 1
                    
                    # Create some sample notifications
                    if match_result['match_score'] >= 70:
                        Notification.objects.create(
                            user=user,
                            message=f"Great news! Your resume shows a {match_result['match_score']}% match for the {job.title} position. You're well-qualified for this role!"
                        )
                    elif match_result['match_score'] >= 50:
                        Notification.objects.create(
                            user=user,
                            message=f"Your resume shows a {match_result['match_score']}% match for the {job.title} position. Consider developing skills in: {', '.join(match_result['missing_skills'][:3])}"
                        )
        
        self.stdout.write(f'Created {analysis_count} skill analyses')
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nDemo data setup complete!\n'
                f'- HR User: hr_demo (password: demo123)\n'
                f'- Candidates: {len(created_candidates)} users created\n'
                f'- Jobs: {jobs.count()} available\n'
                f'- Analyses: {analysis_count} created\n'
                f'- Notifications: {Notification.objects.count()} created\n'
            )
        )
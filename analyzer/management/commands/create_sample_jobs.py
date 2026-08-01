from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analyzer.models import Job, UserProfile


class Command(BaseCommand):
    help = 'Create sample job postings for testing'

    def handle(self, *args, **options):
        # Create or get an HR user
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
        
        # Create or get HR profile
        hr_profile, created = UserProfile.objects.get_or_create(
            user=hr_user,
            defaults={'role': 'HR'}
        )

        # Sample job data
        sample_jobs = [
            {
                'title': 'Python Developer',
                'description': 'We are looking for a skilled Python developer to join our team. You will be responsible for developing web applications using Django framework.',
                'required_skills': 'Python, Django, MySQL, JavaScript, HTML, CSS, Git, REST API'
            },
            {
                'title': 'Full Stack Developer',
                'description': 'Join our dynamic team as a Full Stack Developer. Work on both frontend and backend technologies to build amazing web applications.',
                'required_skills': 'JavaScript, React, Node.js, Express.js, MongoDB, HTML, CSS, Git, AWS'
            },
            {
                'title': 'Data Scientist',
                'description': 'We are seeking a Data Scientist to analyze complex data sets and provide insights to drive business decisions.',
                'required_skills': 'Python, Machine Learning, Pandas, NumPy, Scikit-learn, TensorFlow, SQL, Statistics, Data Visualization'
            },
            {
                'title': 'DevOps Engineer',
                'description': 'Looking for a DevOps Engineer to manage our infrastructure and deployment pipelines.',
                'required_skills': 'Docker, Kubernetes, AWS, Jenkins, Terraform, Linux, Python, Bash, CI/CD, Monitoring'
            },
            {
                'title': 'Frontend Developer',
                'description': 'We need a Frontend Developer to create beautiful and responsive user interfaces.',
                'required_skills': 'JavaScript, React, Vue.js, HTML, CSS, Bootstrap, Webpack, Git, Responsive Design'
            }
        ]

        created_count = 0
        for job_data in sample_jobs:
            job, created = Job.objects.get_or_create(
                title=job_data['title'],
                hr=hr_user,
                defaults={
                    'description': job_data['description'],
                    'required_skills': job_data['required_skills']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created job: {job.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample jobs!')
        )
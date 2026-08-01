# Resume Skill Gap Analyzer & HR Resume Screening Platform

A comprehensive Django-based recruitment platform that enables intelligent skill gap analysis and candidate screening for both job seekers and HR professionals.

## 🚀 Features

### For Candidates (Users)
- **Resume Upload**: Upload PDF/DOCX resumes with secure file handling
- **Skill Gap Analysis**: AI-powered analysis against job requirements
- **Improvement Suggestions**: Personalized recommendations for skill development
- **Application History**: Track all resume analyses and applications
- **HR Notifications**: Receive feedback and status updates from recruiters

### For HR/Recruiters
- **Job Management**: Create and manage job postings with skill requirements
- **Bulk Resume Processing**: Upload and analyze multiple resumes simultaneously
- **Advanced Filtering**: Filter candidates by match score, skill gaps, and readiness level
- **Candidate Screening**: Accept/reject candidates with personalized feedback
- **Analytics Dashboard**: Comprehensive insights and reporting
- **Export Options**: Download analysis results in PDF/JSON formats

## 🛠️ Technology Stack

- **Backend**: Django 4.2.7, Django ORM, MySQL
- **Frontend**: HTML5, CSS3, Bootstrap 5, Vanilla JavaScript
- **File Processing**: PyPDF2 (PDF), python-docx (DOCX)
- **Authentication**: Django Authentication with role-based access
- **Database**: MySQL (production-ready)

## 📋 Prerequisites

- Python 3.8+
- MySQL 5.7+
- pip (Python package manager)

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd resume_skill_gap
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. MySQL Database Setup
```sql
CREATE DATABASE resume_skill_gap;
CREATE USER 'resume_user'@'localhost' IDENTIFIED BY 'CoffeeScreen@123';
GRANT ALL PRIVILEGES ON resume_skill_gap.* TO 'resume_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configure Database Settings
Update `resume_skill_gap/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'resume_skill_gap',
        'USER': 'resume_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Collect Static Files
```bash
python manage.py collectstatic
```

### 9. Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the application.

## 👥 User Roles & Access

### Candidate Access
- Register as "Candidate" during signup
- Upload and manage resumes
- Analyze skills against job postings
- View improvement suggestions
- Receive HR notifications

### HR Access
- Register as "HR/Recruiter" during signup
- Create and manage job postings
- Bulk upload and analyze resumes
- Filter and screen candidates
- Send feedback and notifications
- Access analytics dashboard

## 🧠 AI & NLP Features

### Skill Extraction
- Advanced tokenization and text processing
- Multi-word skill detection
- Stop-word removal and normalization
- Frequency-based skill ranking

### Skill Categories
- **Programming Languages**: Python, Java, JavaScript, etc.
- **Frameworks**: Django, React, Angular, etc.
- **Databases**: MySQL, PostgreSQL, MongoDB, etc.
- **Tools**: Git, Docker, Jenkins, etc.
- **Concepts**: Machine Learning, DevOps, etc.

### Scoring System
- **Match Score**: 0-100% based on skill overlap
- **Gap Percentage**: Percentage of missing required skills
- **Readiness Levels**:
  - Beginner (0-49%)
  - Intermediate (50-69%)
  - Job Ready (70-89%)
  - Highly Compatible (90-100%)

## 📊 Analytics & Reporting

### HR Dashboard Metrics
- Total resumes processed
- Average match scores
- Top missing skills across candidates
- Job-wise candidate statistics
- Readiness level distribution

### Export Options
- **PDF Reports**: Formatted analysis reports
- **JSON Data**: Structured data for integration

## 🔒 Security Features

- **Authentication**: Secure user registration and login
- **File Validation**: PDF/DOCX only, 2MB size limit
- **CSRF Protection**: Built-in Django security
- **Role-based Access**: Separate candidate and HR interfaces
- **Session Management**: Secure session handling

## 📁 Project Structure

```
resume_skill_gap/
├── resume_skill_gap/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── analyzer/                  # Main application
│   ├── models.py             # Database models
│   ├── views.py              # View controllers
│   ├── forms.py              # Form definitions
│   ├── utils.py              # Utility functions
│   ├── templates/            # HTML templates
│   │   ├── auth/            # Authentication pages
│   │   ├── user/            # Candidate pages
│   │   └── hr/              # HR pages
│   └── static/              # CSS, JS, images
├── media/                    # Uploaded files
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🚀 Deployment

### Production Settings
1. Set `DEBUG = False` in settings.py
2. Configure proper `ALLOWED_HOSTS`
3. Use environment variables for sensitive data
4. Set up proper MySQL configuration
5. Configure static file serving
6. Set up SSL/HTTPS

### Environment Variables
```bash
export SECRET_KEY='your-secret-key'
export DB_NAME='resume_skill_gap'
export DB_USER='your-db-user'
export DB_PASSWORD='your-db-password'
export DB_HOST='localhost'
export DB_PORT='3306'
```

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

## 📝 API Endpoints

### Authentication
- `/login/` - User login
- `/signup/` - User registration
- `/logout/` - User logout

### Candidate Endpoints
- `/dashboard/` - Candidate dashboard
- `/upload-resume/` - Resume upload
- `/analyze-resume/<resume_id>/<job_id>/` - Skill analysis
- `/notifications/` - View notifications

### HR Endpoints
- `/hr-dashboard/` - HR dashboard
- `/create-job/` - Create job posting
- `/bulk-upload/` - Bulk resume upload
- `/filter-resumes/` - Filter candidates
- `/analytics/` - Analytics dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code comments

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
- Full skill gap analysis
- HR screening capabilities
- Analytics dashboard
- Export functionality

---

**Built with ❤️ using Django and modern web technologies**
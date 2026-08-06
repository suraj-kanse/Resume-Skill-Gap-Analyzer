import PyPDF2
from docx import Document
import re
import string
from collections import Counter
from django.core.files.storage import default_storage


def extract_text_from_pdf(file_obj):
    """Extract text from PDF file object"""
    pdf_reader = PyPDF2.PdfReader(file_obj)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(file_obj):
    """Extract text from DOCX file object"""
    doc = Document(file_obj)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text


def extract_text_from_resume(resume_file):
    """Extract text from resume file based on extension"""
    file_extension = resume_file.name.lower().split('.')[-1]
    
    # Open the file context using Django's FieldFile interface, which works
    # dynamically with both local storage and remote cloud storage (e.g. S3/Cloudinary)
    with resume_file.open('rb') as file_obj:
        if file_extension == 'pdf':
            return extract_text_from_pdf(file_obj)
        elif file_extension == 'docx':
            return extract_text_from_docx(file_obj)
        else:
            raise ValueError(f"Unsupported file format: .{file_extension}")


def clean_text(text):
    """Clean and normalize text"""
    # Convert to lowercase
    text = text.lower()
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove punctuation except for specific cases
    text = re.sub(r'[^\w\s\+\#\.]', ' ', text)
    return text.strip()


def get_predefined_skills():
    """Get predefined skill categories"""
    return {
        'programming_languages': [
            'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
            'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'typescript', 'dart',
            'objective-c', 'vb.net', 'cobol', 'fortran', 'assembly', 'shell', 'bash'
        ],
        'frameworks': [
            'django', 'flask', 'fastapi', 'spring', 'spring boot', 'react', 'angular',
            'vue.js', 'node.js', 'express.js', 'laravel', 'symfony', 'codeigniter',
            'rails', 'asp.net', 'mvc', 'bootstrap', 'jquery', 'ember.js', 'backbone.js',
            'meteor', 'gatsby', 'next.js', 'nuxt.js', 'svelte', 'flutter', 'xamarin'
        ],
        'databases': [
            'mysql', 'postgresql', 'mongodb', 'sqlite', 'oracle', 'sql server',
            'redis', 'cassandra', 'elasticsearch', 'dynamodb', 'firebase', 'couchdb',
            'neo4j', 'influxdb', 'mariadb', 'db2', 'sybase', 'teradata'
        ],
        'tools': [
            'git', 'docker', 'kubernetes', 'jenkins', 'travis ci', 'gitlab ci',
            'ansible', 'terraform', 'vagrant', 'webpack', 'gulp', 'grunt',
            'maven', 'gradle', 'npm', 'yarn', 'pip', 'composer', 'jira', 'confluence',
            'slack', 'trello', 'asana', 'postman', 'swagger', 'figma', 'sketch'
        ],
        'concepts': [
            'machine learning', 'artificial intelligence', 'data science', 'big data',
            'cloud computing', 'devops', 'microservices', 'api', 'rest api', 'graphql',
            'agile', 'scrum', 'kanban', 'tdd', 'bdd', 'ci/cd', 'version control',
            'object oriented programming', 'functional programming', 'design patterns',
            'data structures', 'algorithms', 'cybersecurity', 'blockchain', 'iot'
        ]
    }


def extract_skills_from_text(text):
    """Extract skills from text using predefined skill categories"""
    cleaned_text = clean_text(text)
    predefined_skills = get_predefined_skills()
    
    found_skills = []
    skill_categories = {}
    
    # Flatten all skills
    all_skills = []
    for category, skills in predefined_skills.items():
        all_skills.extend(skills)
        for skill in skills:
            skill_categories[skill] = category
    
    # Sort skills by length (longest first) to match multi-word skills first
    all_skills.sort(key=len, reverse=True)
    
    # Find skills in text
    for skill in all_skills:
        # Create regex pattern for skill matching
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, cleaned_text):
            if skill not in found_skills:
                found_skills.append(skill)
    
    # Remove duplicates and normalize
    unique_skills = []
    for skill in found_skills:
        normalized_skill = skill.strip().lower()
        if normalized_skill not in [s.lower() for s in unique_skills]:
            unique_skills.append(skill.title())
    
    return unique_skills


def get_skill_synonyms():
    """Define skill synonyms and variations for better matching"""
    return {
        'html': ['html', 'html5'],
        'css': ['css', 'css3', 'sass', 'scss'],
        'javascript': ['js', 'javascript', 'ecmascript'],
        'react': ['react', 'reactjs', 'react.js'],
        'node': ['node', 'nodejs', 'node.js'],
        'angular': ['angular', 'angularjs', 'angular.js'],
        'vue': ['vue', 'vuejs', 'vue.js'],
        'mongodb': ['mongodb', 'mongo'],
        'postgresql': ['postgresql', 'postgres'],
        'sql server': ['sql server', 'mssql', 'microsoft sql server'],
        'aws': ['aws', 'amazon web services'],
        'gcp': ['gcp', 'google cloud', 'google cloud platform'],
        'azure': ['azure', 'microsoft azure'],
        'kubernetes': ['kubernetes', 'k8s'],
        'golang': ['go', 'golang'],
        'machine learning': ['machine learning', 'ml'],
        'artificial intelligence': ['artificial intelligence', 'ai'],
        'django': ['django', 'django framework'],
        'flask': ['flask', 'flask framework'],
        'fastapi': ['fastapi', 'fastapi framework'],
        'spring boot': ['spring boot', 'spring'],
        'git': ['git', 'github', 'gitlab'],
        'ci/cd': ['ci/cd', 'continuous integration', 'continuous delivery', 'continuous deployment'],
        'docker': ['docker', 'docker containerization'],
        'rest api': ['rest api', 'restful api', 'rest apis'],
        'nlp': ['nlp', 'natural language processing'],
        'ui/ux': ['ui/ux', 'ui', 'ux', 'user interface', 'user experience'],
        'devops': ['devops', 'site reliability engineering', 'sre']
    }


def normalize_skill(skill):
    """Normalize skill name to its canonical form"""
    skill_lower = skill.lower().strip()
    synonyms = get_skill_synonyms()
    
    # Check if skill matches any synonym group
    for canonical, variations in synonyms.items():
        if skill_lower in [v.lower() for v in variations]:
            return canonical  # Return canonical form
    
    return skill_lower  # Return as-is if no synonym found


def skills_match(skill1, skill2):
    """Check if two skills match (considering synonyms)"""
    norm1 = normalize_skill(skill1)
    norm2 = normalize_skill(skill2)
    
    # Direct match after normalization
    if norm1 == norm2:
        return True
        
    return False


def calculate_skill_match(resume_skills, job_skills):
    """Calculate skill match between resume and job requirements"""
    matched_skills = []
    missing_skills = []
    
    for original_job_skill in job_skills:
        matched = False
        for resume_skill in resume_skills:
            if skills_match(resume_skill, original_job_skill):
                matched_skills.append(original_job_skill)
                matched = True
                break
        if not matched:
            missing_skills.append(original_job_skill)
            
    total_job_skills = len(job_skills)
    matched_count = len(matched_skills)
    
    if total_job_skills == 0:
        match_score = 0
        gap_percentage = 100
    else:
        match_score = (matched_count / total_job_skills) * 100
        gap_percentage = ((total_job_skills - matched_count) / total_job_skills) * 100
    
    return {
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'match_score': round(match_score, 2),
        'gap_percentage': round(gap_percentage, 2)
    }


def determine_readiness_level(match_score):
    """Determine readiness level based on match score"""
    if match_score >= 90:
        return 'HIGHLY_COMPATIBLE'
    elif match_score >= 70:
        return 'JOB_READY'
    elif match_score >= 50:
        return 'INTERMEDIATE'
    else:
        return 'BEGINNER'


def parse_skills_from_string(skills_string):
    """Parse skills from comma-separated string"""
    if not skills_string:
        return []
    
    skills = [skill.strip() for skill in skills_string.split(',')]
    return [skill for skill in skills if skill]


def format_skills_list(skills_list):
    """Format skills list to comma-separated string"""
    if not skills_list:
        return ""
    return ", ".join(skills_list)


def get_skill_suggestions(missing_skills, matched_skills):
    """Generate skill improvement suggestions"""
    suggestions = []
    
    if not missing_skills:
        suggestions.append("Excellent! You have all the required skills for this position.")
        return suggestions
    
    # Categorize missing skills
    predefined_skills = get_predefined_skills()
    skill_categories = {}
    for category, skills in predefined_skills.items():
        for skill in skills:
            skill_categories[skill.lower()] = category.replace('_', ' ').title()
    
    categorized_missing = {}
    for skill in missing_skills:
        category = skill_categories.get(skill.lower(), 'Other')
        if category not in categorized_missing:
            categorized_missing[category] = []
        categorized_missing[category].append(skill)
    
    # Generate suggestions
    for category, skills in categorized_missing.items():
        if len(skills) == 1:
            suggestions.append(f"Consider learning {skills[0]} to strengthen your {category} skills.")
        else:
            skills_str = ", ".join(skills[:-1]) + f" and {skills[-1]}"
            suggestions.append(f"Focus on developing {category} skills, particularly {skills_str}.")
    
    # Add general advice
    if len(missing_skills) > 5:
        suggestions.append("Prioritize learning the most critical skills first based on the job requirements.")
    
    suggestions.append("Consider taking online courses, tutorials, or hands-on projects to gain these skills.")
    
    return suggestions
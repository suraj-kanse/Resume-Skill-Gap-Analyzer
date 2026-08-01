import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_skill_gap.settings')
django.setup()

from analyzer.utils import parse_skills_from_string, extract_skills_from_text, calculate_skill_match
from analyzer.models import SkillAnalysis

# Test parsing
print("=" * 60)
print("TEST 1: Parse Job Skills")
print("=" * 60)
job_skills_raw = """Frontend: HTML5, CSS3, JavaScript, Bootstrap
* Backend: Python, Django
* Database: MySQL
* Tools: Git, GitHub, VS Code
* Other: Responsive Web Design, REST APIs, Basic SEO"""

parsed = parse_skills_from_string(job_skills_raw)
print(f"Parsed {len(parsed)} skills:")
for skill in parsed:
    print(f"  - {skill}")

# Test resume extraction
print("\n" + "=" * 60)
print("TEST 2: Extract Skills from Resume")
print("=" * 60)
resume_text = """
Frontend: HTML5, CSS3, JavaScript, Bootstrap
Backend: Python, Django
Database: MySQL
Tools: Git, GitHub, VS Code
Other: Responsive Web Design, REST APIs, Basic SEO
"""

extracted = extract_skills_from_text(resume_text)
print(f"Extracted {len(extracted)} skills:")
for skill in extracted:
    print(f"  - {skill}")

# Test matching
print("\n" + "=" * 60)
print("TEST 3: Skill Matching")
print("=" * 60)
result = calculate_skill_match(extracted, parsed)
print(f"Match Score: {result['match_score']}%")
print(f"Gap: {result['gap_percentage']}%")
print(f"\nMatched ({len(result['matched_skills'])}):")
for skill in result['matched_skills']:
    print(f"  ✓ {skill}")
print(f"\nMissing ({len(result['missing_skills'])}):")
for skill in result['missing_skills']:
    print(f"  ✗ {skill}")

# Re-analyze existing analysis
print("\n" + "=" * 60)
print("TEST 4: Re-analyze Analysis ID 65")
print("=" * 60)
try:
    analysis = SkillAnalysis.objects.get(id=65)
    print(f"Resume: {analysis.resume.user.username}")
    print(f"Job: {analysis.job.title}")
    
    # Extract skills from resume
    resume_skills = extract_skills_from_text(analysis.resume.extracted_text)
    print(f"\nResume Skills ({len(resume_skills)}):")
    for skill in resume_skills[:10]:
        print(f"  - {skill}")
    
    # Parse job skills
    job_skills = parse_skills_from_string(analysis.job.required_skills)
    print(f"\nJob Skills ({len(job_skills)}):")
    for skill in job_skills:
        print(f"  - {skill}")
    
    # Calculate match
    match_result = calculate_skill_match(resume_skills, job_skills)
    print(f"\n=== RESULTS ===")
    print(f"Match Score: {match_result['match_score']}%")
    print(f"Gap: {match_result['gap_percentage']}%")
    print(f"Matched: {len(match_result['matched_skills'])}")
    print(f"Missing: {len(match_result['missing_skills'])}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

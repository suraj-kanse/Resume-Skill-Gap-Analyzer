import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_skill_gap.settings')
django.setup()

from analyzer.models import SkillAnalysis
from analyzer.utils import (
    extract_skills_from_text, parse_skills_from_string, 
    calculate_skill_match, determine_readiness_level, format_skills_list
)

# Get analysis ID from command line or use default
analysis_id = int(sys.argv[1]) if len(sys.argv) > 1 else 65

# Update analysis
analysis = SkillAnalysis.objects.get(id=analysis_id)

# Extract and match skills
resume_skills = extract_skills_from_text(analysis.resume.extracted_text)
job_skills = parse_skills_from_string(analysis.job.required_skills)
match_result = calculate_skill_match(resume_skills, job_skills)

# Update analysis
analysis.matched_skills = format_skills_list(match_result['matched_skills'])
analysis.missing_skills = format_skills_list(match_result['missing_skills'])
analysis.gap_percentage = match_result['gap_percentage']
analysis.match_score = match_result['match_score']
analysis.readiness_level = determine_readiness_level(match_result['match_score'])
analysis.save()

print(f"✓ Successfully Updated Analysis ID {analysis_id}")
print("=" * 60)
print(f"Match Score: {analysis.match_score}%")
print(f"Gap Percentage: {analysis.gap_percentage}%")
print(f"Readiness Level: {analysis.get_readiness_level_display()}")
print(f"\nMatched Skills ({len(match_result['matched_skills'])}):")
for skill in match_result['matched_skills']:
    print(f"  ✓ {skill}")
print(f"\nMissing Skills ({len(match_result['missing_skills'])}):")
for skill in match_result['missing_skills']:
    print(f"  ✗ {skill}")
print("\n" + "=" * 60)
print("Refresh the browser to see updated results!")

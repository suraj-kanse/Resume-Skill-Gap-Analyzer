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

print("=" * 70)
print("RE-ANALYZING ALL SKILL ANALYSES WITH IMPROVED ALGORITHM")
print("=" * 70)

analyses = SkillAnalysis.objects.all()
total = analyses.count()
updated = 0
errors = 0

print(f"\nFound {total} analyses to process...\n")

for i, analysis in enumerate(analyses, 1):
    try:
        print(f"[{i}/{total}] Processing Analysis ID {analysis.id}...", end=" ")
        
        # Extract skills from resume
        if not analysis.resume.extracted_text:
            print("X No extracted text")
            errors += 1
            continue
            
        resume_skills = extract_skills_from_text(analysis.resume.extracted_text)
        job_skills = parse_skills_from_string(analysis.job.required_skills)
        
        # Calculate match
        match_result = calculate_skill_match(resume_skills, job_skills)
        
        # Update analysis
        old_score = analysis.match_score
        analysis.matched_skills = format_skills_list(match_result['matched_skills'])
        analysis.missing_skills = format_skills_list(match_result['missing_skills'])
        analysis.gap_percentage = match_result['gap_percentage']
        analysis.match_score = match_result['match_score']
        analysis.readiness_level = determine_readiness_level(match_result['match_score'])
        analysis.save()
        
        improvement = match_result['match_score'] - old_score
        print(f"OK {old_score}% -> {match_result['match_score']}% ({improvement:+.1f}%)")
        updated += 1
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        errors += 1

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total Analyses: {total}")
print(f"Successfully Updated: {updated}")
print(f"Errors: {errors}")
print(f"Success Rate: {(updated/total*100):.1f}%")
print("\nAll analyses have been re-processed with the improved algorithm!")
print("Refresh your browser to see the updated results.")


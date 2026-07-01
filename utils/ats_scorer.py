def calculate_ats_score(matched_skills, jd_skills):
    if not jd_skills:
        return 0
    score = (len(matched_skills) / len(jd_skills)) * 100
    return round(score, 2)

import re
from skills_data import SKILLS_DB

# Different names for the same skill
SKILL_ALIASES = {
    "react.js": "react",
    "reactjs": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "express": "express.js",
    "expressjs": "express.js",
    "rest apis": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "js": "javascript",
}


def normalize_skill(skill):
    """Lowercase, strip, and resolve through alias map only.
    No singularization here — that would mangle names like
    'express.js' -> 'express.j' or 'aws' -> 'aw'.
    """
    skill = skill.lower().strip()
    return SKILL_ALIASES.get(skill, skill)


def extract_skills(text):
    text = text.lower()
    found = set()
    for skill in SKILLS_DB:
        base = re.escape(skill.lower())
        # allow an optional trailing 's' or 'es' IN THE TEXT being searched
        # (e.g. matches "APIs" against stored "api"), without ever
        # altering the stored skill name itself
        pattern = r'(?<![\w])' + base + r'(?:es|s)?(?![\w])'
        if re.search(pattern, text):
            found.add(normalize_skill(skill))
    return found


def compare_skills(resume_text, jd_text):
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)

    return {
        "resume_skills": sorted(resume_skills),
        "jd_skills": sorted(jd_skills),
        "matched": matched,
        "missing": missing,
    }
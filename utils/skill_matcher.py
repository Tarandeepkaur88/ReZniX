import re
from skills_data import SKILLS_DB

# All possible variations of each skill
SKILL_ALIASES = {
    # Programming Languages
    "c++": ["c++", "cpp", "c plus plus"],
    "c programming": ["c programming", " c ", "c language"],
    "python": ["python", "python3", "python 3"],
    "javascript": ["javascript", "js", "java script"],
    "typescript": ["typescript", "ts"],
    "java": ["java"],
    "sql": ["sql", "structured query language"],
    "pl/sql": ["pl/sql", "plsql", "pl sql"],

    # Web
    "react": ["react", "react.js", "reactjs", "react js"],
    "node.js": ["node.js", "nodejs", "node js", "node"],
    "express.js": ["express.js", "expressjs", "express js", "express"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "tailwind css": ["tailwind css", "tailwind", "tailwindcss"],
    "flask": ["flask"],
    "django": ["django"],

    # APIs & Tools
    "rest apis": ["rest apis", "rest api", "restful api", "restful apis", "rest"],
    "git": ["git"],
    "github": ["github"],
    "docker": ["docker", "containerization"],
    "aws": ["aws", "amazon web services", "amazon aws"],
    "linux": ["linux", "ubuntu", "unix"],
    "vs code": ["vs code", "vscode", "visual studio code"],
    "jupyter notebook": ["jupyter notebook", "jupyter", "ipynb"],

    # AI/ML
    "machine learning": ["machine learning", "ml", " ml "],
    "deep learning": ["deep learning", "dl", " dl "],
    "tensorflow": ["tensorflow", "tf", "tensor flow"],
    "keras": ["keras"],
    "neural networks": ["neural networks", "neural network", "nn", "ann"],
    "nlp": ["nlp", "natural language processing", "natural-language processing"],
    "bert": ["bert", "bidirectional encoder"],
    "huggingface transformers": ["huggingface", "hugging face", "transformers", "hf transformers"],
    "tokenization": ["tokenization", "tokenizer", "tokenizing"],
    "tf-idf": ["tf-idf", "tfidf", "tf idf"],
    "text classification": ["text classification", "text classifier"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],

    # Databases
    "mysql": ["mysql", "my sql"],
    "mongodb": ["mongodb", "mongo db", "mongo"],
    "postgresql": ["postgresql", "postgres", "postgre sql"],
    "redis": ["redis"],
    "firebase": ["firebase", "fire base"],

    # CS Fundamentals
    "data structures": ["data structures", "data structure"],
    "algorithms": ["algorithms", "algorithm"],
    "data structures and algorithms": ["data structures and algorithms", "dsa", "ds&a", "ds & a"],
    "operating systems": ["operating systems", "operating system", "os"],
    "computer networks": ["computer networks", "computer network", "networking", "cn"],
    "database management systems": ["database management systems", "database management", "dbms", "rdbms"],
    "software engineering": ["software engineering", "software development"],
    "object-oriented programming": ["object-oriented programming", "object oriented programming", "oop", "oops", "ooad"],
    "problem solving": ["problem solving", "problem-solving"],
    "competitive programming": ["competitive programming", "cp"],

    # Cloud & DevOps
    "kubernetes": ["kubernetes", "k8s"],
    "ci/cd": ["ci/cd", "cicd", "ci cd", "continuous integration"],
    "devops": ["devops", "dev ops"],

    # Other
    "gemini api": ["gemini api", "gemini"],
    "prompt engineering": ["prompt engineering", "prompting"],
    "leetcode": ["leetcode", "leet code"],
    "geeksforgeeks": ["geeksforgeeks", "gfg", "geeks for geeks"],
    "matlab": ["matlab"],
    "autocad": ["autocad", "auto cad"],
}

NEGATION_WORDS = ["no", "not", "without", "lack", "never", "zero", "unfamiliar", "no experience"]

def clean_text(text):
    # Convert to lowercase
    text = text.lower()
    # Replace special characters with space except . + #
    text = re.sub(r'[^\w\s\.\+\#\/]', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text

def is_negated(text, skill):
    skill_pos = text.find(skill)
    if skill_pos == -1:
        return False
    before = text[max(0, skill_pos - 50):skill_pos]
    for neg in NEGATION_WORDS:
        if neg in before:
            return True
    return False

def extract_skills(text):
    text = clean_text(text)
    found = set()

    for standard_skill, variations in SKILL_ALIASES.items():
        for variation in variations:
            variation = variation.lower()
            if variation in text:
                if not is_negated(text, variation):
                    found.add(standard_skill)
                    break

    return found

def compare_skills(resume_text, jd_text):
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)
    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched": matched,
        "missing": missing
    }
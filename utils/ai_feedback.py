import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY", "").strip()
client = Groq(api_key=api_key)

def clean_text(text):
    # Remove non-ASCII characters that break the API
    return text.encode("ascii", errors="ignore").decode("ascii")

def get_resume_feedback(resume_text, jd_text, missing_skills):
    # Clean texts before sending
    resume_text = clean_text(resume_text)
    jd_text = clean_text(jd_text)

    prompt = f"""
You are an expert resume reviewer and career coach.

Analyze this resume against the job description and give honest, specific feedback.

Resume:
{resume_text}

Job Description:
{jd_text}

Missing Skills: {", ".join(missing_skills)}

Give feedback in exactly this format:

OVERALL FEEDBACK:
(2-3 sentences about the resume overall)

STRENGTHS:
- (strength 1)
- (strength 2)
- (strength 3)

IMPROVEMENTS:
- (specific improvement 1)
- (specific improvement 2)
- (specific improvement 3)

MISSING SKILLS ADVICE:
- (how to address each missing skill)
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return response.choices[0].message.content

def get_interview_questions(matched_skills):
    skills = ", ".join(list(matched_skills)[:8])
    prompt = f"""
You are a technical interviewer.

Generate 2 interview questions for EACH of these skills: {skills}

Format exactly like this:

SKILL NAME:
1. Question one?
2. Question two?

Only include the skills listed. Keep questions clear and specific.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return response.choices[0].message.content
def generate_cover_letter(resume_text, jd_text, user_name, company_name, job_role):
    resume_text = clean_text(resume_text)
    jd_text = clean_text(jd_text)

    prompt = f"""
You are a professional cover letter writer.

Extract information from this resume and write a formal cover letter.

Candidate Name: {user_name}
Applying for: {job_role} at {company_name}

Resume:
{resume_text}

Job Description:
{jd_text}

Write the cover letter in this EXACT format:

[Candidate Full Name]
[Email from resume if found, else leave blank]
[Phone from resume if found, else leave blank]
[City, Country]
[Today's Date]

Hiring Manager
{company_name}

Dear Hiring Manager,

[Opening paragraph - strong hook mentioning the role and company]

[Second paragraph - highlight 2-3 most relevant skills/projects from resume that match the job]

[Third paragraph - why this specific company, show genuine interest]

[Closing paragraph - confident call to action]

Sincerely,
{user_name}

Important:
- Use ONLY real information from the resume
- Do not use placeholder brackets like [mention skill] 
- Make it sound human and specific, not generic
- Keep it to 4 paragraphs
- Today's date is {__import__('datetime').datetime.now().strftime('%B %d, %Y')}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200
    )
    return response.choices[0].message.content
def generate_interview_question(company, round_type, difficulty, topic, previous_questions, resume_skills):
    prev = "\n".join(previous_questions) if previous_questions else "None"

    company_style = {
        "Google": "Google focuses on DSA, algorithms, time/space complexity, and clean code. They love graph problems, dynamic programming, and system scalability.",
        "Amazon": "Amazon focuses on Leadership Principles, behavioral questions, and practical coding. They love questions about scalability, customer obsession, and ownership.",
        "Microsoft": "Microsoft focuses on problem solving, system design, coding clarity, and collaboration. They value communication and structured thinking.",
        "Meta": "Meta focuses on product sense, coding speed, system design at scale, and behavioral questions around impact and collaboration.",
        "Apple": "Apple focuses on creativity, attention to detail, system design, and coding quality. They value innovative thinking.",
        "Flipkart": "Flipkart focuses on DSA, system design, and practical coding problems relevant to e-commerce at scale.",
        "TCS": "TCS focuses on basic programming, aptitude, verbal ability, and fundamental CS concepts.",
        "Infosys": "Infosys focuses on logical reasoning, basic coding, and fundamental CS and database concepts.",
        "Wipro": "Wipro focuses on aptitude, basic coding, and fundamental programming concepts."
    }.get(company, f"{company} follows standard software engineering interview practices.")

    prompt = f"""
You are a senior technical interviewer at {company}.

Company style: {company_style}

Round: {round_type}
Difficulty: {difficulty}
Topic: {topic if topic else "General"}

Previous questions asked (DO NOT repeat these):
{prev}

Generate ONE new interview question that:
- Matches {company}'s interview style exactly
- Is appropriate for {difficulty} difficulty
- Is for {round_type} round
- Has NOT been asked before

Format exactly like this:

QUESTION:
[The interview question here]

HINT:
[A small hint or what the interviewer is looking for - 1 line]

EXPECTED TOPICS:
[What concepts the answer should cover - 1 line]

Only output the question in this format. Nothing else.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )
    return response.choices[0].message.content

def evaluate_interview_answer(question, answer, company, round_type):
    prompt = f"""
You are a senior interviewer at {company} evaluating a candidate's answer.

Question asked: {question}

Candidate's answer: {answer}

Evaluate the answer and respond in exactly this format:

SCORE: [X/10]

WHAT YOU DID WELL:
- [point 1]
- [point 2]

WHAT WAS MISSING:
- [point 1]
- [point 2]

IDEAL ANSWER SUMMARY:
[2-3 sentences of what a perfect answer looks like]

{company} TIP:
[One specific tip about how {company} expects this type of question to be answered]
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content
def get_resume_breakdown(resume_text, jd_text):
    resume_text = clean_text(resume_text)
    jd_text = clean_text(jd_text)

    prompt = f"""
You are an expert resume analyzer.

Analyze this resume against the job description and give scores for each dimension.

Resume:
{resume_text}

Job Description:
{jd_text}

Return ONLY a JSON object with these exact keys and integer scores 0-100:

{{
  "skills": <score>,
  "keywords": <score>,
  "formatting": <score>,
  "grammar": <score>,
  "experience": <score>,
  "overall": <score>
}}

Scoring criteria:
- skills: How well technical skills match the JD
- keywords: How many important JD keywords appear in resume
- formatting: How well structured and organized the resume is
- grammar: Quality of writing, grammar, and clarity
- experience: How relevant the experience/projects are to the JD
- overall: Overall impression score

Return ONLY the JSON, no explanation, no markdown, no backticks.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    import json
    try:
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except:
        return {
            "skills": 70,
            "keywords": 65,
            "formatting": 75,
            "grammar": 80,
            "experience": 70,
            "overall": 72
        }
# Reznix

**AI-powered resume analyzer that helps you land the job.**

Reznix analyzes your resume against a job description, scores it for ATS (Applicant Tracking System) compatibility, matches your skills to role requirements, generates tailored cover letters, and helps you prep for interviews — all in one place.

## Features

- **ATS Scoring** — See how well your resume matches a job description
- **Skill Gap Analysis** — Compare your resume skills against the job description and see what is missing
- **AI Resume Feedback** — Personalized, actionable suggestions powered by AI
- **Resume Breakdown** — Standalone scoring across skills match, keywords, formatting, grammar, and experience
- **Cover Letter Generator** — Auto-generates a formatted, print-ready, downloadable cover letter
- **Interview Prep** — AI-generated interview questions with answer evaluation
- **History Dashboard** — Track past analyses and see stats over time
- **User Accounts** — Secure signup, login, and password reset with hashed passwords

## Security

- Environment-based secret key and debug configuration
- Server-side file type and size validation on resume uploads
- Filenames sanitized before saving to disk
- Passwords hashed with Werkzeug secure hashing
- Parameterized SQL queries throughout

## Tech Stack

- Backend: Python (Flask)
- Database: PostgreSQL (Supabase)
- Frontend: HTML, CSS, JavaScript (Jinja2 templates)
- AI: LLM-powered feedback and content generation
- PDF handling: pdfplumber (extraction), ReportLab (cover letter export)

## Getting Started

1. Clone the repo
2. Create a virtual environment and install dependencies from requirements.txt
3. Set up your .env file with SECRET_KEY and API keys
4. Run: python app.py
5. Open http://127.0.0.1:5000

## License

This project is for personal/educational use.

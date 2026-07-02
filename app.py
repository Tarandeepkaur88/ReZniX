from flask import Flask, request, render_template, session, make_response, redirect, url_for
import os
import io
import json
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib import colors
from utils.pdf_extractor import extract_text_from_pdf
from utils.skill_matcher import compare_skills
from utils.ats_scorer import calculate_ats_score
from utils.database import create_table, save_analysis, get_all_analyses, register_user, login_user, update_password, check_email_exists, get_dashboard_stats
from utils.ai_feedback import get_resume_feedback, get_interview_questions, generate_cover_letter, generate_interview_question, evaluate_interview_answer, get_resume_breakdown

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "resumeanalyzer2024secret")

UPLOAD_FOLDER = "uploads"
TEMP_FOLDER = "temp_data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf"}
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

create_table()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]
        if password != confirm:
            error = "Passwords do not match!"
        elif len(password) < 6:
            error = "Password must be at least 6 characters!"
        else:
            success = register_user(name, email, password)
            if success:
                return redirect(url_for('login'))
            else:
                error = "Email already registered! Please login."
    return render_template("signup.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = login_user(email, password)
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid email or password!"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None
    success = None
    if request.method == "POST":
        email = request.form["email"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        if not check_email_exists(email):
            error = "No account found with this email!"
        elif new_password != confirm_password:
            error = "Passwords do not match!"
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters!"
        else:
            update_password(email, new_password)
            success = "Password updated successfully! You can now login."
    return render_template("forgot_password.html", error=error, success=success)

@app.route("/dashboard")
@login_required
def dashboard():
    stats = get_dashboard_stats(session['user_id'])
    breakdown = session.get('last_breakdown', None)
    return render_template("dashboard.html",
        user_name=session['user_name'],
        stats=stats,
        breakdown=breakdown
    )

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        resume = request.files.get("resume")
        job_description = request.form.get("job_description", "")

        if not resume or resume.filename == "":
            return render_template("index.html",
                user_name=session['user_name'],
                error="Please choose a resume file.")

        if not allowed_file(resume.filename):
            return render_template("index.html",
                user_name=session['user_name'],
                error="Only PDF files are allowed.")

        filename = secure_filename(resume.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        resume.save(filepath)

        resume_text = extract_text_from_pdf(filepath)
        result = compare_skills(resume_text, job_description)
        ats_score = calculate_ats_score(result['matched'], result['jd_skills'])

        print("✅ Score calculated:", ats_score)

        session['resume_text'] = resume_text
        session['job_description'] = job_description

        try:
            feedback = get_resume_feedback(
                resume_text,
                job_description,
                result['missing']
            )
            print("✅ Feedback done")
        except Exception as e:
            print("❌ Feedback error:", e)
            feedback = "Could not generate feedback at this time."

        try:
            questions = get_interview_questions(result['matched'])
            print("✅ Questions done")
        except Exception as e:
            print("❌ Questions error:", e)
            questions = "Could not generate questions at this time."

        try:
            breakdown = get_resume_breakdown(resume_text, job_description)
            session['last_breakdown'] = breakdown
            print("✅ Breakdown done:", breakdown)
        except Exception as e:
            print("❌ Breakdown error:", e)
            breakdown = None
            session['last_breakdown'] = None

        save_analysis(
            session['user_id'],
            filename,
            ats_score,
            result['matched'],
            result['missing']
        )

        # Store only small data in session cookie
        session['last_result'] = {
            "ats_score": ats_score,
            "matched": list(result['matched']),
            "missing": list(result['missing']),
            "breakdown": breakdown,
        }

        # Store large text in temp file to avoid cookie size limit
        user_temp = os.path.join(TEMP_FOLDER, f"user_{session['user_id']}.json")
        with open(user_temp, "w") as f:
            json.dump({
                "feedback": feedback,
                "questions": questions
            }, f)

        return redirect(url_for('result'))

    notice = request.args.get('notice')
    banner_message = None
    if notice == 'upload_first':
        banner_message = "Please analyze a resume first before generating a cover letter."
    return render_template("index.html",
        user_name=session['user_name'],
        banner_message=banner_message)

@app.route("/result")
@login_required
def result():
    data = session.get('last_result')
    if not data:
        return redirect(url_for('index', notice='upload_first'))

    # Load large data from temp file
    feedback = "Could not load feedback."
    questions = "Could not load questions."
    user_temp = os.path.join(TEMP_FOLDER, f"user_{session['user_id']}.json")
    if os.path.exists(user_temp):
        with open(user_temp, "r") as f:
            temp = json.load(f)
            feedback = temp.get("feedback", feedback)
            questions = temp.get("questions", questions)

    return render_template("result.html",
        ats_score=data["ats_score"],
        matched=data["matched"],
        missing=data["missing"],
        feedback=feedback,
        questions=questions,
        breakdown=data["breakdown"],
        user_name=session['user_name']
    )

@app.route("/history")
@login_required
def history():
    analyses = get_all_analyses(session['user_id'])
    return render_template("history.html",
        analyses=analyses,
        user_name=session['user_name'])

@app.route("/cover-letter", methods=["GET", "POST"])
@login_required
def cover_letter():
    generated = None
    resume_text = session.get('resume_text', '')
    jd_text = session.get('job_description', '')

    if not resume_text:
        return redirect(url_for('index', notice='upload_first'))

    if request.method == "POST":
        user_name = request.form["user_name"]
        company_name = request.form["company_name"]
        if company_name == "other":
            company_name = request.form["company_name_custom"]
        job_role = request.form["job_role"]
        if job_role == "other":
            job_role = request.form["job_role_custom"]
        generated = generate_cover_letter(
            resume_text, jd_text,
            user_name, company_name, job_role
        )
    return render_template("cover_letter.html",
        cover_letter=generated,
        user_name=session['user_name'])

@app.route("/download-pdf", methods=["POST"])
@login_required
def download_pdf():
    content = request.form.get("content", "")
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=inch, leftMargin=inch,
        topMargin=inch, bottomMargin=inch
    )
    styles = getSampleStyleSheet()
    style = ParagraphStyle(
        'Letter', parent=styles['Normal'],
        fontSize=12, leading=20,
        fontName='Times-Roman',
        textColor=colors.black, spaceAfter=6
    )
    paragraphs = []
    for line in content.split('\n'):
        if line.strip() == '':
            paragraphs.append(Spacer(1, 10))
        else:
            paragraphs.append(Paragraph(line.strip(), style))
    doc.build(paragraphs)
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=cover_letter.pdf'
    return response

@app.route("/interview-prep")
@login_required
def interview_prep():
    return render_template("interview_prep.html",
        user_name=session['user_name'])

@app.route("/get-question", methods=["POST"])
@login_required
def get_question():
    data = request.get_json()
    question = generate_interview_question(
        data.get("company", ""),
        data.get("round_type", ""),
        data.get("difficulty", ""),
        data.get("topic", ""),
        data.get("previous_questions", []),
        session.get("resume_text", "")
    )
    return {"question": question}

@app.route("/evaluate-answer", methods=["POST"])
@login_required
def evaluate_answer():
    data = request.get_json()
    feedback = evaluate_interview_answer(
        data.get("question", ""),
        data.get("answer", ""),
        data.get("company", ""),
        data.get("round_type", "")
    )
    return {"feedback": feedback}

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(debug=debug_mode)
from flask import Flask, render_template, request, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from openpyxl import load_workbook
import random
import os

app = Flask(__name__)
app.secret_key = "secret123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ======================
# DATABASE MODELS
# ======================
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    exam_timer = db.Column(db.Integer, default=120)
    start_time = db.Column(db.String(20))
    end_time = db.Column(db.String(20))


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    question = db.Column(db.String(500))
    opt1 = db.Column(db.String(200))
    opt2 = db.Column(db.String(200))
    opt3 = db.Column(db.String(200))
    opt4 = db.Column(db.String(200))
    answer = db.Column(db.String(200))


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    student_id = db.Column(db.String(50))
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    subject = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()

# ======================
# FIXED TIME FUNCTION
# ======================
def subject_is_open(subject_obj):
    """
    FIX:
    - Works even if server time differs
    - Allows empty time (always open)
    """
    try:
        if not subject_obj.start_time or not subject_obj.end_time:
            return True

        now = datetime.now().strftime("%H:%M")

        return subject_obj.start_time <= now <= subject_obj.end_time
    except:
        return True


# ======================
# LOGIN
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        student_id = request.form.get("student_id")
        password = request.form.get("password")

        # Admin login
        if username == "admin" and password == "admin123":
            session.clear()
            session["admin"] = True
            return redirect("/admin")

        # Student login
        if username:
            session.clear()
            session["student"] = username
            session["student_id"] = student_id
            return redirect("/home")

    return render_template("login.html")


# ======================
# HOME
# ======================
@app.route("/home")
def home():
    if "student" not in session:
        return redirect("/")

    subjects = Subject.query.all()
    now = datetime.now().strftime("%H:%M")

    return render_template(
        "home.html",
        student_name=session["student"],
        subjects=subjects,
        now=now
    )


# ======================
# STUDENT EXAM
# ======================
@app.route("/student/<int:subject_id>")
def student(subject_id):
    if "student" not in session:
        return redirect("/")

    subject = Subject.query.get(subject_id)

    # FIXED CHECK
    if not subject_is_open(subject):
        return render_template("subject_closed.html", subject=subject)

    questions = Question.query.filter_by(subject=subject.name).all()
    random.shuffle(questions)

    return render_template(
        "student.html",
        questions=questions,
        student_name=session["student"],
        exam_timer=subject.exam_timer,
        subject_name=subject.name,
        subject_id=subject.id
    )


# ======================
# REVIEW PAGE
# ======================
@app.route("/review/<int:subject_id>", methods=["POST"])
def review(subject_id):
    subject = Subject.query.get(subject_id)
    questions = Question.query.filter_by(subject=subject.name).all()

    answers = {}
    for q in questions:
        answers[str(q.id)] = request.form.get(str(q.id))

    session["answers"] = answers
    session["subject"] = subject.name

    return render_template(
        "review.html",
        questions=questions,
        answers=answers,
        subject_id=subject_id
    )


# ======================
# SUBMIT EXAM (FIXED MARKING)
# ======================
@app.route("/submit", methods=["POST"])
def submit():
    subject = session.get("subject")
    questions = Question.query.filter_by(subject=subject).all()
    answers = session.get("answers", {})

    score = 0

    for q in questions:
        selected = answers.get(str(q.id))

        # FIX: ensure correct comparison
        if selected and selected.strip() == q.answer.strip():
            score += 1

    result = Result(
        name=session["student"],
        student_id=session.get("student_id"),
        score=score,
        total=len(questions),
        subject=subject
    )

    db.session.add(result)
    db.session.commit()

    return render_template(
        "result.html",
        score=score,
        total=len(questions),
        result_id=result.id
    )


# ======================
# ADMIN PANEL
# ======================
@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/")

    questions = Question.query.all()
    subjects = Subject.query.all()

    return render_template("admin.html", questions=questions, subjects=subjects)


# ======================
# ADD QUESTION
# ======================
@app.route("/add", methods=["GET", "POST"])
def add():
    subjects = Subject.query.all()

    if request.method == "POST":
        q = Question(
            subject=request.form["subject"],
            question=request.form["question"],
            opt1=request.form["opt1"],
            opt2=request.form["opt2"],
            opt3=request.form["opt3"],
            opt4=request.form["opt4"],
            answer=request.form["answer"]
        )
        db.session.add(q)
        db.session.commit()
        return redirect("/admin")

    return render_template("add.html", subjects=subjects)


# ======================
# DELETE QUESTION
# ======================
@app.route("/delete/<int:id>")
def delete(id):
    q = Question.query.get(id)
    db.session.delete(q)
    db.session.commit()
    return redirect("/admin")


# ======================
# LOGOUT
# ======================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ======================
# RUN
# ======================
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)

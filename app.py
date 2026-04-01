from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = "secret123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ======================
# MODELS
# ======================
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
# LOGIN
# ======================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "").strip()

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
    return render_template("home.html", student_name=session.get("student", "Ifelodun"))


# ======================
# STUDENT EXAM
# ======================
@app.route("/student")
def student():
    if "student" not in session:
        return redirect("/")

    questions = Question.query.filter_by(subject="CSC 201").all()
    random.shuffle(questions)
    return render_template(
        "student.html",
        questions=questions,
        student_name=session.get("student", "Ifelodun")
    )


# ======================
# REVIEW
# ======================
@app.route("/review", methods=["POST"])
def review():
    if "student" not in session:
        return redirect("/")

    questions = Question.query.filter_by(subject="CSC 201").all()
    answers = {q.id: request.form.get(str(q.id)) for q in questions}
    session["answers"] = answers

    return render_template(
        "review.html",
        questions=questions,
        answers=answers,
        student_name=session.get("student", "Ifelodun")
    )


# ======================
# SUBMIT
# ======================
@app.route("/submit", methods=["POST"])
def submit():
    if "student" not in session:
        return redirect("/")

    questions = Question.query.filter_by(subject="CSC 201").all()
    answers = session.get("answers", {})

    score = sum(1 for q in questions if answers.get(q.id) == q.answer)

    result = Result(
        name=session["student"],
        student_id=session.get("student_id", ""),
        score=score,
        total=len(questions),
        subject="CSC 201"
    )
    db.session.add(result)
    db.session.commit()

    return render_template(
        "result.html",
        score=score,
        total=len(questions),
        student_name=session.get("student", "Ifelodun")
    )


# ======================
# ADMIN
# ======================
@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/")
    questions = Question.query.all()
    return render_template("admin.html", questions=questions)


# ======================
# ADD QUESTION
# ======================
@app.route("/add", methods=["GET", "POST"])
def add():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        opt1 = request.form.get("opt1", "").strip()
        opt2 = request.form.get("opt2", "").strip()
        opt3 = request.form.get("opt3", "").strip()
        opt4 = request.form.get("opt4", "").strip()
        answer = request.form.get("answer", "").strip()

        if question and opt1 and opt2 and opt3 and opt4 and answer:
            q = Question(
                subject="CSC 201",
                question=question,
                opt1=opt1,
                opt2=opt2,
                opt3=opt3,
                opt4=opt4,
                answer=answer
            )
            db.session.add(q)
            db.session.commit()
            return redirect("/admin")

    return render_template("add.html")


# ======================
# DELETE QUESTION
# ======================
@app.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/")

    q = Question.query.get_or_404(id)
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

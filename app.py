from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= MODELS =================

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
    student_id = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    exam_timer = db.Column(db.Integer, default=120)


# ================= LOGIN =================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        student_id = request.form.get("student_id")

        admin_user = request.form.get("admin_username")
        admin_pass = request.form.get("admin_password")

        if admin_user == "admin" and admin_pass == "admin123":
            session.clear()
            session["admin"] = True
            return redirect("/admin")

        if name:
            session.clear()
            session["student"] = name
            session["student_id"] = student_id
            return redirect("/home")

    return render_template("login.html")


# ================= HOME =================

@app.route("/home")
def home():
    if "student" not in session:
        return redirect("/")

    subjects = Subject.query.all()

    return render_template(
        "home.html",
        subjects=subjects,
        student_name=session["student"]
    )


# ================= EXAM =================

@app.route("/student/<int:subject_id>")
def student(subject_id):
    if "student" not in session:
        return redirect("/")

    subject = Subject.query.get_or_404(subject_id)

    session["current_subject"] = subject.name

    questions = Question.query.filter_by(subject=subject.name).all()

    return render_template(
        "student.html",
        questions=questions,
        exam_timer=subject.exam_timer,
        student_name=session["student"],
        subject_name=subject.name
    )


# ================= SUBMIT =================

@app.route("/submit", methods=["POST"])
def submit():
    if "student" not in session:
        return redirect("/")

    subject = session.get("current_subject")

    questions = Question.query.filter_by(subject=subject).all()

    score = 0
    total = len(questions)

    for q in questions:
        user = request.form.get(str(q.id))
        if user and user.strip() == q.answer.strip():
            score += 1

    percent = round((score / total) * 100, 2) if total else 0

    grade = "F"
    if percent >= 70:
        grade = "A"
    elif percent >= 60:
        grade = "B"
    elif percent >= 50:
        grade = "C"

    result = Result(
        name=session["student"],
        student_id=session["student_id"],
        subject=subject,
        score=score,
        total=total
    )

    db.session.add(result)
    db.session.commit()

    return render_template(
        "result.html",
        score=score,
        total=total,
        percentage=percent,
        grade=grade,
        student_name=session["student"],
        subject_name=subject
    )


# ================= ADMIN =================

@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/")

    return render_template(
        "admin.html",
        questions=Question.query.all(),
        subjects=Subject.query.all()
    )


# ================= ADD SUBJECT =================

@app.route("/add_subject", methods=["POST"])
def add_subject():
    if "admin" not in session:
        return redirect("/")

    name = request.form.get("name")
    timer = request.form.get("exam_timer")

    db.session.add(Subject(name=name, exam_timer=int(timer)))
    db.session.commit()

    return redirect("/admin")


# ================= ADD QUESTION =================

@app.route("/add", methods=["GET", "POST"])
def add():
    if "admin" not in session:
        return redirect("/")

    subjects = Subject.query.all()

    if request.method == "POST":
        q = Question(
            subject=request.form.get("subject"),
            question=request.form.get("question"),
            opt1=request.form.get("opt1"),
            opt2=request.form.get("opt2"),
            opt3=request.form.get("opt3"),
            opt4=request.form.get("opt4"),
            answer=request.form.get("answer")
        )

        db.session.add(q)
        db.session.commit()

        return redirect("/admin")

    return render_template("add.html", subjects=subjects)


# ================= DELETE =================

@app.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/")

    q = Question.query.get(id)
    db.session.delete(q)
    db.session.commit()

    return redirect("/admin")


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= RUN =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)

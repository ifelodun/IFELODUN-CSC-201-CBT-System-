from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ===================== MODELS =====================

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
    start_time = db.Column(db.String(10), default="00:00")
    end_time = db.Column(db.String(10), default="23:59")


# ===================== LOGIN =====================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("name")
        student_id = request.form.get("student_id")
        admin_username = request.form.get("admin_username")
        admin_password = request.form.get("admin_password")

        # admin login
        if admin_username == "admin" and admin_password == "admin123":
            session.clear()
            session["admin"] = True
            return redirect("/admin")

        # student login
        if username:
            session.clear()
            session["student"] = username
            session["student_id"] = student_id
            return redirect("/home")

    return render_template("index.html")


# ===================== STUDENT HOME =====================

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


# ===================== START EXAM =====================

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
        student_name=session["student"],
        exam_timer=subject.exam_timer,
        subject_name=subject.name
    )


# ===================== SUBMIT =====================

@app.route("/submit", methods=["POST"])
def submit():
    if "student" not in session:
        return redirect("/")

    subject_name = session.get("current_subject")
    if not subject_name:
        return redirect("/home")

    questions = Question.query.filter_by(subject=subject_name).all()

    score = 0
    total = len(questions)

    for q in questions:
        user_ans = request.form.get(str(q.id))
        if user_ans and q.answer and user_ans.strip() == q.answer.strip():
            score += 1

    percentage = round((score / total) * 100, 2) if total > 0 else 0

    if percentage >= 70:
        grade = "A"
    elif percentage >= 60:
        grade = "B"
    elif percentage >= 50:
        grade = "C"
    elif percentage >= 45:
        grade = "D"
    elif percentage >= 40:
        grade = "E"
    else:
        grade = "F"

    result = Result(
        name=session.get("student"),
        student_id=session.get("student_id"),
        subject=subject_name,
        score=score,
        total=total
    )

    db.session.add(result)
    db.session.commit()

    return render_template(
        "result.html",
        score=score,
        total=total,
        percentage=percentage,
        grade=grade,
        student_name=session.get("student"),
        subject_name=subject_name
    )


# ===================== ADMIN =====================

@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/")

    questions = Question.query.all()
    subjects = Subject.query.all()
    return render_template("admin.html", questions=questions, subjects=subjects)


# ===================== ADD SUBJECT =====================

@app.route("/add_subject", methods=["POST"])
def add_subject():
    if "admin" not in session:
        return redirect("/")

    name = request.form.get("name")
    exam_timer = request.form.get("exam_timer")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    if name:
        subject = Subject(
            name=name,
            exam_timer=int(exam_timer),
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(subject)
        db.session.commit()

    return redirect("/admin")


# ===================== ADD QUESTION =====================

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


# ===================== DELETE QUESTION =====================

@app.route("/delete/<int:id>")
def delete(id):
    if "admin" not in session:
        return redirect("/")

    q = Question.query.get(id)
    if q:
        db.session.delete(q)
        db.session.commit()
    return redirect("/admin")


# ===================== LOGOUT =====================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ===================== RUN =====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

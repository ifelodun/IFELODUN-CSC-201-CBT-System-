from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    exam_timer = db.Column(db.Integer)
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))


# ===================== HOME =====================

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        session["student"] = request.form["name"]
        session["student_id"] = request.form["student_id"]
        return redirect("/home")

    return render_template("index.html")


# ===================== STUDENT HOME =====================

@app.route("/home")
def student_home():
    if "student" not in session:
        return redirect("/")

    subjects = Subject.query.all()

    now = datetime.now().strftime("%H:%M")

    return render_template(
        "home.html",
        subjects=subjects,
        student_name=session["student"],
        now=now
    )


# ===================== START EXAM =====================

@app.route("/student/<int:subject_id>")
def student(subject_id):
    if "student" not in session:
        return redirect("/")

    subject = Subject.query.get_or_404(subject_id)

    session["current_subject"] = subject.name  # 🔥 IMPORTANT

    questions = Question.query.filter_by(subject=subject.name).all()

    return render_template(
        "student.html",
        questions=questions,
        student_name=session["student"],
        exam_timer=subject.exam_timer
    )


# ===================== SUBMIT =====================

@app.route("/submit", methods=["POST"])
def submit():
    if "student" not in session:
        return redirect("/")

    subject_name = session.get("current_subject")

    questions = Question.query.filter_by(subject=subject_name).all()

    score = 0
    total = len(questions)

    for q in questions:
        user_ans = request.form.get(str(q.id))
        if user_ans and user_ans.strip() == q.answer.strip():
            score += 1

    result = Result(
        name=session["student"],
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
        student_name=session["student"],
        subject_name=subject_name
    )


# ===================== ADMIN LOGIN =====================

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")

    if "admin" not in session:
        return render_template("admin_login.html")

    questions = Question.query.all()
    subjects = Subject.query.all()

    return render_template("admin.html", questions=questions, subjects=subjects)


# ===================== ADD SUBJECT =====================

@app.route("/add_subject", methods=["POST"])
def add_subject():
    if "admin" not in session:
        return redirect("/admin")

    name = request.form["name"]
    exam_timer = request.form["exam_timer"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]

    subject = Subject(
        name=name,
        exam_timer=int(exam_timer),
        start_time=start_time,
        end_time=end_time
    )

    db.session.add(subject)
    db.session.commit()

    return redirect("/admin")


# ===================== DELETE SUBJECT =====================

@app.route("/delete_subject/<int:id>")
def delete_subject(id):
    subject = Subject.query.get(id)
    db.session.delete(subject)
    db.session.commit()
    return redirect("/admin")


# ===================== ADD QUESTION =====================

@app.route("/add", methods=["GET", "POST"])
def add():
    if "admin" not in session:
        return redirect("/admin")

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


# ===================== DELETE QUESTION =====================

@app.route("/delete/<int:id>")
def delete(id):
    q = Question.query.get(id)
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

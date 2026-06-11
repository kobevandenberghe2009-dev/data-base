import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from difflib import get_close_matches

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "secret")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- DATABASE ----------------
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voornaam = db.Column(db.String(100))
    achternaam = db.Column(db.String(100))
    telefoon = db.Column(db.String(100))
    email = db.Column(db.String(100))
    woonplaats = db.Column(db.String(100))
    notities = db.Column(db.Text)
    files = db.Column(db.Text)

# ---------------- USERS ----------------
USERS = {
    "admin": {"password": "1234", "role": "admin"}
}

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in USERS and USERS[u]["password"] == p:
            session["user"] = u
            session["role"] = USERS[u]["role"]
            return redirect("/")

        return "Foute login"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- HOME + SEARCH ----------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    query = request.args.get("q")
    people = Person.query.all()

    if query:
        names = [p.voornaam + " " + p.achternaam for p in people]
        matches = get_close_matches(query, names, n=20, cutoff=0.4)
        people = [p for p in people if (p.voornaam + " " + p.achternaam) in matches]

    return render_template("index.html", people=people, role=session["role"])

# ---------------- ADD ----------------
@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/login")

    p = Person(
        voornaam=request.form["voornaam"],
        achternaam=request.form["achternaam"],
        telefoon=request.form["telefoon"],
        email=request.form["email"],
        woonplaats=request.form["woonplaats"],
        notities=request.form["notities"],
        files=""
    )

    db.session.add(p)
    db.session.commit()
    return redirect("/")

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    p = Person.query.get(id)
    db.session.delete(p)
    db.session.commit()
    return redirect("/")

# ---------------- EDIT ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    p = Person.query.get(id)

    if request.method == "POST":
        p.voornaam = request.form["voornaam"]
        p.achternaam = request.form["achternaam"]
        p.telefoon = request.form["telefoon"]
        p.email = request.form["email"]
        p.woonplaats = request.form["woonplaats"]
        p.notities = request.form["notities"]

        db.session.commit()
        return redirect("/")

    return render_template("edit.html", p=p)

# ---------------- UPLOAD ----------------
@app.route("/upload/<int:id>", methods=["POST"])
def upload(id):
    file = request.files["file"]
    filename = secure_filename(file.filename)

    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    p = Person.query.get(id)

    if p.files:
        p.files += "," + filename
    else:
        p.files = filename

    db.session.commit()
    return redirect("/")

# ---------------- START ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

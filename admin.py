import os
from flask import Blueprint, render_template, redirect, request, url_for, session, abort, flash, current_app
from functools import wraps

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def load_highscores():
    highscores = []
    try:
        with open("data/-highscores.txt", "r") as file:
            lines = file.read().splitlines()
        for i in range(0, len(lines), 2):
            username = lines[i]
            score = int(lines[i + 1])
            highscores.append({"username": username, "score": score})
    except FileNotFoundError:
        return []
    return highscores


def save_highscores(highscores):
    with open("data/-highscores.txt", "w") as file:
        for entry in highscores:
            file.write(f"{entry['username']}\n")
            file.write(f"{entry['score']}\n")


def update_highscore(entry_id, username, score):
    highscores = load_highscores()
    highscores[entry_id] = {"username": username, "score": score}
    save_highscores(highscores)


def delete_highscore(entry_id):
    highscores = load_highscores()
    if 0 <= entry_id < len(highscores):
        highscores.pop(entry_id)
        save_highscores(highscores)


def get_users():
    users = []
    for filename in os.listdir("data"):
        if filename.startswith("user-") and filename.endswith("-score.txt"):
            username = filename[len("user-"):-len("-score.txt")]
            score = 0
            with open(os.path.join("data", filename), "r") as score_file:
                for line in score_file:
                    try:
                        score += int(line)
                    except ValueError:
                        pass
            users.append({"username": username, "score": score})
    return sorted(users, key=lambda item: item["score"], reverse=True)


def load_riddles_answers():
    riddles = []
    answers = []
    try:
        with open("data/-riddles.txt", "r") as rfile:
            riddles = [line.rstrip("\n") for line in rfile.readlines()]
    except FileNotFoundError:
        riddles = []
    try:
        with open("data/-answers.txt", "r") as afile:
            answers = [line.rstrip("\n") for line in afile.readlines()]
    except FileNotFoundError:
        answers = []
    return riddles, answers


def save_riddles_answers(riddles, answers):
    with open("data/-riddles.txt", "w") as rfile:
        for line in riddles:
            rfile.write(f"{line}\n")
    with open("data/-answers.txt", "w") as afile:
        for line in answers:
            afile.write(f"{line}\n")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect(url_for("admin.admin_login"))
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if session.get("role") == "admin":
        return redirect(url_for("admin.admin_dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == current_app.config.get("ADMIN_USERNAME") and password == current_app.config.get("ADMIN_PASSWORD"):
            session["role"] = "admin"
            flash("Logged in successfully.")
            return redirect(url_for("admin.admin_dashboard"))
        error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@admin_bp.route("/logout")
def admin_logout():
    session.pop("role", None)
    flash("Logged out.")
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")


@admin_bp.route("/highscores")
@admin_required
def admin_highscores():
    highscores = load_highscores()
    return render_template("admin_highscores.html", highscores=highscores)


@admin_bp.route("/highscores/<int:entry_id>", methods=["POST"])
@admin_required
def modify_highscore(entry_id):
    action = request.form.get("action")
    if action == "edit":
        new_username = request.form.get("username", "").strip()
        new_score = request.form.get("score", "").strip()
        if not new_username or not new_score.isdigit():
            abort(400)
        update_highscore(entry_id, new_username, int(new_score))
        flash("Highscore updated successfully")
        return redirect(url_for("admin.admin_highscores"))
    elif action == "delete":
        delete_highscore(entry_id)
        flash("Highscore deleted successfully")
        return redirect(url_for("admin.admin_highscores"))
    abort(400)


@admin_bp.route("/users")
@admin_required
def admin_users():
    users = get_users()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/riddles")
@admin_required
def admin_riddles():
    riddles, answers = load_riddles_answers()
    return render_template("admin_riddles.html", riddles=zip(riddles, answers))


@admin_bp.route("/riddles/<int:riddle_id>", methods=["POST"])
@admin_required
def modify_riddle(riddle_id):
    action = request.form.get("action")
    riddles, answers = load_riddles_answers()
    if riddle_id < 0 or riddle_id >= len(riddles):
        abort(404)

    if action == "edit":
        new_riddle = request.form.get("riddle", "").strip()
        new_answer = request.form.get("answer", "").strip()
        if not new_riddle or not new_answer:
            abort(400)
        riddles[riddle_id] = new_riddle
        answers[riddle_id] = new_answer
        save_riddles_answers(riddles, answers)
        flash("Riddle updated successfully")
        return redirect(url_for("admin.admin_riddles"))
    elif action == "delete":
        riddles.pop(riddle_id)
        answers.pop(riddle_id)
        save_riddles_answers(riddles, answers)
        flash("Riddle deleted successfully")
        return redirect(url_for("admin.admin_riddles"))
    abort(400)


@admin_bp.route("/riddles/add", methods=["POST"])
@admin_required
def add_riddle():
    new_riddle = request.form.get("new_riddle", "").strip()
    new_answer = request.form.get("new_answer", "").strip()
    if not new_riddle or not new_answer:
        abort(400)
    riddles, answers = load_riddles_answers()
    riddles.append(new_riddle)
    answers.append(new_answer)
    save_riddles_answers(riddles, answers)
    flash("Riddle added successfully")
    return redirect(url_for("admin.admin_riddles"))

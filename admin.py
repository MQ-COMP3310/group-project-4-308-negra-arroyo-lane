import os
from flask import Blueprint, render_template, redirect, request, url_for, session, abort, flash
from functools import wraps
import json
from pathlib import Path
from werkzeug.security import check_password_hash

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ADMIN_LOGIN = "admin.admin_login"
ADMIN_RIDDLES = "admin.admin_riddles"
USERS_FILE = Path("data/users.json")

@admin_bp.before_request
def block_non_admin_access():
    """
    Blocks normal users from accessing any admin route.
    Allows unauthenticated users to reach only /admin/login.
    ACR-04: Score modification routes check role == 'admin'.
    Only admins can modify scores through dedicated admin routes.
    """

    # Allow the admin login page only if not already logged in as normal user
    if request.endpoint == ADMIN_LOGIN:
        if "username" in session and session.get("role") != "admin":
            abort(403)
        return

    # Every other /admin route requires admin role
    if session.get("role") != "admin":
        abort(403)

def load_highscores():
    highscores = []
    try:
        with open("data/-highscores.txt", "r") as file:
            lines = file.read().splitlines()
    except FileNotFoundError:
        return []

    for i in range(0, len(lines), 2):
        if i + 1 >= len(lines):
            continue

        username = lines[i].strip()
        raw_score = lines[i + 1].strip()

        try:
            score = int(raw_score)
        except ValueError:
            # Invalid/tampered score entry. Skip instead of crashing.
            continue

        highscores.append({
            "username": username,
            "score": score
        })

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
        if "username" not in session:
            abort(403)

        if session.get("role") != "admin":
            abort(403)

        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if session.get("role") == "admin":
        return redirect(url_for("admin.admin_dashboard"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()


        if USERS_FILE.exists():
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
        else:
            users = {}

        if username in users:
            user = users[username]

            if user.get("role") == "admin" and check_password_hash(user["password_hash"], password):
                session["username"] = username
                session["role"] = "admin"
                flash("Logged in successfully.")
                return redirect(url_for("admin.admin_dashboard"))

        error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@admin_bp.route("/logout", methods=["GET", "POST"])
def admin_logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("index"))


@admin_bp.route("/", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")


@admin_bp.route("/highscores", methods=["GET", "POST"])
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


@admin_bp.route("/users", methods=["GET"])
@admin_required
def admin_users():
    users = get_users()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/riddles", methods=["GET"])
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
        return redirect(url_for(ADMIN_RIDDLES))
    elif action == "delete":
        riddles.pop(riddle_id)
        answers.pop(riddle_id)
        save_riddles_answers(riddles, answers)
        flash("Riddle deleted successfully")
        return redirect(url_for(ADMIN_RIDDLES))
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

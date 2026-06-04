# score_feature.py
# COMP3310 Part 2: User Score Integrity Feature
# Requirement: Users must not be able to edit or delete their scores.

import json
import re
from pathlib import Path
from functools import wraps
from flask import Blueprint, abort, render_template, session, redirect, url_for, request
from datetime import datetime
from pathlib import Path

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")
SCORE_HISTORY_DIR = Path("data/score_history")
AUDIT_LOG_FILE = Path("data/audit.log")

score_bp = Blueprint("score_feature", __name__)


# ============================================================
# Security helpers
# ============================================================

def validate_username(username):
    """
    Secure coding principle: treat all inputs as untrusted.
    Usernames are validated before being used in file paths.
    """
    if not username or not USERNAME_RE.fullmatch(username):
        abort(400, description="Invalid username")
    return username


def login_required(view_func):
    """
    Secure coding principle: complete mediation.
    Score-history routes require an authenticated session.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("index"))
        return view_func(*args, **kwargs)
    return wrapper

def admin_required(view_func):
    """
    Secure coding principle: role-based access control.
    Admin-only routes check the user's role before allowing access.
    ACR-04: Check role == 'admin' before modifying scores.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "username" not in session or session.get("role") != "admin":
            abort(403)
        return view_func(*args, **kwargs)
    return wrapper


def current_user_owns(username):
    """
    Secure coding principle: least privilege.
    A normal user may only view their own score history.
    ACR-02: Users may only view their own score history.
    """
    validate_username(username)
    return session.get("username") == username


def audit_log(actor, action, target_score, result):
    """
    Secure coding principle: accountability / repudiation protection.
    Log all score modification attempts with actor, action, timestamp, result.
    """
    AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "actor": actor,
        "action": action,
        "target_score": target_score,
        "result": result
    }
    with open(AUDIT_LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


# ============================================================
# Score storage helpers
# ============================================================

def ensure_score_history_dir():
    SCORE_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def score_history_path(username):
    """
    Secure coding principle: safe file access.
    The username is validated before being used to build a file path.
    """
    username = validate_username(username)
    ensure_score_history_dir()
    return SCORE_HISTORY_DIR / f"{username}.json"


def read_score_history(username):
    """
    Read-only score history.
    Users can view scores, but this function does not provide edit/delete behaviour.
    """
    path = score_history_path(username)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_score_history(username, scores):
    """
    Internal helper used only by trusted server-side score recording.
    This is not exposed through any user-editable route.
    """
    path = score_history_path(username)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(scores, file, indent=2)


def record_completed_score(username, score):
    """
    Requirement implementation:
    Users must not be able to edit or delete their scores.

    Scores are recorded only by trusted server-side game logic.
    The browser never submits the final score value.
    """
    username = validate_username(username)

    try:
        score = int(score)
    except (TypeError, ValueError):
        abort(400, description="Invalid score")

    scores = read_score_history(username)

    score_record = {
        "score_id": len(scores),
        "score": score
    }

    scores.append(score_record)
    write_score_history(username, scores)


# ============================================================
# Score routes
# ============================================================

@score_bp.route("/<username>/scores", methods=["GET"])
@login_required
def view_scores(username):
    """
    Requirement: logged-in users may view their own previous scores.
    Security principle: least privilege.
    """
    username = validate_username(username)

    if not current_user_owns(username) and session.get("role") != "admin":
        abort(403, description="Cannot view another user's scores")

    scores = read_score_history(username)
    return render_template("scores.html", username=username, scores=scores)



@score_bp.route("/admin/scores/<username>/<int:score_id>/edit", methods=["POST"])
@login_required
@admin_required
def admin_edit_score(username, score_id):
    """
    AC-06 / AC-07:
    Only authenticated administrators may edit stored score history.
    CSRF protection is enforced globally by Flask-WTF.
    """
    username = validate_username(username)
    new_score = request.form.get("score", "").strip()

    if not new_score.isdigit():
        audit_log(session.get("username"), "admin_edit_score", score_id, "denied_invalid_score")
        abort(400, description="Invalid score")

    scores = read_score_history(username)

    if score_id < 0 or score_id >= len(scores):
        audit_log(session.get("username"), "admin_edit_score", score_id, "denied_not_found")
        abort(404, description="Score not found")

    scores[score_id]["score"] = int(new_score)
    write_score_history(username, scores)

    audit_log(session.get("username"), "admin_edit_score", score_id, "allowed")
    return redirect(url_for("score_feature.view_scores", username=username))


@score_bp.route("/admin/scores/<username>/<int:score_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_score(username, score_id):
    """
    AC-06 / AC-07:
    Only authenticated administrators may delete stored score history.
    Normal users receive 403 before modification occurs.
    """
    username = validate_username(username)
    scores = read_score_history(username)

    if score_id < 0 or score_id >= len(scores):
        audit_log(session.get("username"), "admin_delete_score", score_id, "denied_not_found")
        abort(404, description="Score not found")

    scores.pop(score_id)

    for index, score in enumerate(scores):
        score["score_id"] = index

    write_score_history(username, scores)

    audit_log(session.get("username"), "admin_delete_score", score_id, "allowed")
    return redirect(url_for("score_feature.view_scores", username=username))




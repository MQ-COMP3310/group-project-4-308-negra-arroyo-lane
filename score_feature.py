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

    if not current_user_owns(username):
        abort(403, description="Cannot view another user's scores")

    scores = read_score_history(username)
    return render_template("scores.html", username=username, scores=scores)


@score_bp.route("/scores/<username>/<int:score_id>/edit", methods=["POST"])
@login_required
def user_cannot_edit_score(username, score_id):
    """
    Requirement ACR-03: users must not be able to edit their scores.
    Security principle: deny by default / fail securely.
    
    Even if this is an admin-only operation, normal users get 403 Forbidden.
    The browser request is treated as untrusted (CSRF protection).
    """
    audit_log(session.get("username"), "edit_score_attempt", score_id, "forbidden")
    abort(403, description="Users cannot edit scores")


@score_bp.route("/scores/<username>/<int:score_id>/delete", methods=["POST"])
@login_required
def user_cannot_delete_score(username, score_id):
    """
    Requirement ACR-03: users must not be able to delete their scores.
    Security principle: deny by default / fail securely.
    
    Even if this is an admin-only operation, normal users get 403 Forbidden.
    The browser request is treated as untrusted (CSRF protection).
    """
    audit_log(session.get("username"), "delete_score_attempt", score_id, "forbidden")
    abort(403, description="Users cannot delete scores")


# ============================================================
# Admin Routes - Future Enhancement
# ============================================================
# These routes are documented for admin score management but intentionally
# not fully implemented to enforce ACR-03: users must never be allowed to
# edit or delete scores, and current system does not require admin score editing.
#
# If admin modification becomes required in future, the following would be implemented:
#
# @score_bp.route("/admin/scores/<username>/<int:score_id>/edit", methods=["POST"])
# @admin_required
# def admin_edit_score(username, score_id):
#     """
#     ACR-04: Score modification routes check role == 'admin'.
#     Only admins can modify scores through dedicated admin routes.
#     """
#     # Validate inputs
#     # Verify score_id exists for username
#     # Update score with new value
#     # Log audit entry
#     pass
#
# @score_bp.route("/admin/scores/<username>/<int:score_id>/delete", methods=["POST"])
# @admin_required
# def admin_delete_score(username, score_id):
#     """
#     ACR-04: Score deletion requires admin role.
#     """
#     # Validate inputs
#     # Verify score_id exists for username
#     # Delete score record
#     # Log audit entry
#     pass
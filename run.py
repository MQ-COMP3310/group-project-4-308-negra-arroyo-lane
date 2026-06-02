#run.py
import os
import sys
import json
from importlib import reload
from flask import Flask, render_template, redirect, request, url_for
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from functools import wraps
from flask import session, abort
import re
from pathlib import Path
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from score_feature import score_bp, record_completed_score
from admin import admin_bp
from flask_wtf.csrf import CSRFProtect


# Needed for encoding to utf8
reload(sys)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
csrf = CSRFProtect(app)
app.register_blueprint(score_bp)
app.register_blueprint(admin_bp)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
data = []

# Data directory for user management
USERS_FILE = Path("data/users.json")
AUDIT_LOG_FILE = Path("data/audit.log")
USER_DATA_PREFIX = "data/user-"
USER_GUESSES_SUFFIX = "-guesses.txt"
USER_SCORE_SUFFIX = "-score.txt"
INDEX_HTML= "index.html"


# ============================================================
# User Management & Authentication
# ============================================================

def load_users():
    """Load user database from JSON file."""
    if USERS_FILE.exists():
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    """Save user database to JSON file."""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


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


def validate_username_format(username):
    """
    Secure coding principle: treat all inputs as untrusted.
    Validate username format before use in file paths or database operations.
    """
    if not username or not re.match(r"^[a-z0-9_]{3,30}$", username.lower()):
        return False
    return True


def validate_password(password):
    """
    Validate password strength.
    Password must be at least 8 characters.
    """
    if not password or len(password) < 8:
        return False
    return True


# ============================================================
# Authorization Decorators
# ============================================================

def login_required(f):
    """
    Secure coding principle: complete mediation.
    Routes decorated with this require an authenticated session.
    ACR-01: Use the authenticated session user, not just URL username.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Secure coding principle: role-based access control / least privilege.
    Routes decorated with this require admin role.
    ACR-04: Check role == 'admin' before allowing modifications.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session or session.get("role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def owner_or_admin(f):
    """
    Secure coding principle: least privilege.
    Users can only access their own data unless they're admin.
    ACR-02: Users may only view their own score history.
    """
    @wraps(f)
    def decorated_function(username, *args, **kwargs):
        current_user = session.get("username")
        current_role = session.get("role")
        
        if not validate_username_format(username):
            abort(400)
        
        if current_user != username and current_role != "admin":
            abort(403)
        
        return f(username, *args, **kwargs)
    return decorated_function


def write_to_file(filename, data):
    with open(filename, "a+") as file:
        file.writelines(data)


#This is where the riddles live
def riddle():
    riddles = []
    with open("data/-riddles.txt", "r") as e:
        lines = e.read().splitlines()
    for line in lines:
        riddles.append(line)
    return riddles


# This is where the answers for the riddles live
def riddle_answers():
    answers = []
    with open("data/-answers.txt", "r") as e:
        lines = e.read().splitlines()
    for line in lines:
        answers.append(line)
    return answers


# Clear functions for wrong answers and score
def clear_guesses(username):
    with open(USER_DATA_PREFIX + username + USER_GUESSES_SUFFIX, "w"):
        return

def clear_score(username):
    with open(USER_DATA_PREFIX + username + USER_SCORE_SUFFIX, "w"):
        return


# Wrong answer handling
def store_all_attempts(username):
    attempts = []
    with open(USER_DATA_PREFIX + username + USER_GUESSES_SUFFIX, "r") as incorrect_attempts:
        attempts = incorrect_attempts.readlines()
    return attempts

def num_of_attempts(username):
    attempts = store_all_attempts(username)
    return len(attempts)

def attempts_remaining(username):
    remaining_attempts = 3 - num_of_attempts(username)
    return remaining_attempts


# Score gets lower the more attempts used
def add_to_score(username):
    round_score = 4 - num_of_attempts(username)
    return round_score

#Adds all the scores from all riddles to make final score
def end_score(username):
    with open(USER_DATA_PREFIX + username + USER_SCORE_SUFFIX, "r") as numbers_file:
        total = 0
        for line in numbers_file:
            try:
                total += int(line)
            except ValueError:
                pass
    return total

#Add final score to highscore list after the last riddle
def final_score(username):
    score = str(end_score(username))

    if username != "" and score != "":
        # COMP3310 Part 2:
        # Secure coding principle: server-side score authority.
        # The score is calculated by the application, not submitted by the browser.
        # Normal users can view recorded scores but cannot edit or delete them.
        #Only function I changed in run.py the rest of the functionality is offloaded to score_feature.py
        record_completed_score(username, score)

        with open("data/-highscores.txt", "a") as file:
                file.writelines(username + "\n")
                file.writelines(score + "\n")
    else:
        return

#Used to retrieve scores from highscore file for use on highscore page
def get_scores():
    usernames = []
    scores = []

    with open("data/-highscores.txt", "r") as file:
        lines = file.read().splitlines()
    # Separates usernames and scores
    for i, text in enumerate(lines):
        if i%2 ==0:
            usernames.append(text)
        else:
            scores.append(text)
    # Sorts and zips all the highscore info up for use on highscore page
    usernames_and_scores = sorted(zip(usernames, scores), key=lambda x: x[1], reverse=True)
    return usernames_and_scores

def save_results(username, result):
    with open("data/user-" + username + "-results.txt", "a") as file:
        file.writelines(str(result) + "\n")

def show_results(username):
    results = []
    with open("data/user-" + username + "-results.txt", "r") as file:
        lines = file.read().splitlines()
    for line in lines:
        results.append(line)
    return results


def get_history_serializer():
    return URLSafeTimedSerializer(app.secret_key, salt="history-share")


def generate_history_token(username):
    return get_history_serializer().dumps({'username': username})


def verify_history_token(token, max_age=30 * 24 * 60 * 60):
    try:
        data = get_history_serializer().loads(token, max_age=max_age)
        return data.get('username')
    except (BadSignature, SignatureExpired):
        return None


def handle_registration(username, password, users):
    """Handle user registration flow."""
    if not validate_password(password):
        return render_template(INDEX_HTML, page_title="Home", 
                             error="Password must be at least 8 characters")
    
    if username in users:
        return render_template(INDEX_HTML, page_title="Home", 
                             error="Username already exists")
    
    # Secure coding principle: secure password storage (salted hash)
    password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    users[username] = {
        "password_hash": password_hash,
        "role": "user",
        "created_at": datetime.now().isoformat()
    }
    save_users(users)
    
    # Log user creation (audit)
    audit_log(username, "register", None, "success")
    
    # Auto-login after registration
    session['username'] = username
    session['role'] = 'user'
    return redirect(url_for('user', username=username))


def handle_login(username, password, users):
    """Handle user login flow."""
    if username not in users:
        return render_template(INDEX_HTML, page_title="Home", 
                             error="Invalid credentials")
    
    user = users[username]
    
    # Secure coding principle: password verification
    if not check_password_hash(user['password_hash'], password):
        audit_log(username, "login_failed", None, "invalid_password")
        return render_template(INDEX_HTML, page_title="Home", 
                             error="Invalid credentials")
    
    # Authentication successful
    session['username'] = username
    session['role'] = user.get('role', 'user')
    audit_log(username, "login", None, "success")

    if session["role"] == "admin":
        return redirect(url_for("admin.admin_dashboard"))
    return redirect(url_for('user', username=username))






# HOMEPAGE
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get('action', 'login')
        username = request.form.get('username', '').lower()
        password = request.form.get('password', '')
        
        # Input validation
        if not validate_username_format(username):
            return render_template(INDEX_HTML, page_title="Home", error="Invalid username format")
        
        users = load_users()
        
        if action == 'register':
            return handle_registration(username, password, users)
        
        return handle_login(username, password, users)
    
    return render_template(INDEX_HTML, page_title="Home")


# LOGOUT
@app.route('/logout', methods=["POST"])
@login_required
def logout():
    """
    Secure coding principle: complete mediation.
    Clear session on logout.
    ACR-01: Use the authenticated session user, not just URL username.
    """
    username = session.get('username')
    audit_log(username, "logout", None, "success")
    session.clear()
    return redirect(url_for('index'))


# USER WELCOME PAGE
@app.route('/<username>', methods=["GET", "POST"])
@login_required
@owner_or_admin
def user(username):

    # Create a User Specific File for Score Keeping etc.
    open(USER_DATA_PREFIX + username + USER_SCORE_SUFFIX, 'a').close()
    clear_score(username)
    open(USER_DATA_PREFIX + username + USER_GUESSES_SUFFIX, 'a').close()
    clear_guesses(username)

    if request.method == "POST":
        return redirect(url_for('game', username=username))

    return render_template("welcome.html",
                            username=username, show_results=show_results(username))


# GAME PAGE
@app.route('/<username>/game', methods=["GET", "POST"])
@login_required
@owner_or_admin
def game(username):
    riddles = riddle()
    riddle_index = 0
    answers = riddle_answers()

    if request.method == "POST":

        riddle_index = int(request.form["riddle_index"])
        user_response = request.form["answer"].title()

        write_to_file(USER_DATA_PREFIX + username + USER_GUESSES_SUFFIX, user_response + "\n")

        # Compare the user's answer to the correct answer of the riddle
        if answers[riddle_index] == user_response:
            # Correct answer
            if riddle_index < 9:
                # If riddle number is less than 10 & answer is correct: add score, clear wrong answers file and go to next riddle
                write_to_file(USER_DATA_PREFIX + username + USER_SCORE_SUFFIX, str(add_to_score(username)) + "\n")
                clear_guesses(username)
                riddle_index += 1
            else:
                # If right answer on LAST riddle: add score, submit score to highscore file and redirect to congrats page
                write_to_file(USER_DATA_PREFIX + username + USER_SCORE_SUFFIX, str(add_to_score(username)) + "\n")
                final_score(username)
                save_results(username, end_score(username))
                return redirect(url_for('congrats', username=username, score=end_score(username)))
        else:
            # Incorrect answer
            if attempts_remaining(username) > 0:
                # if answer was wrong and more than 0 attempts remaining, reload current riddle
                riddle_index = riddle_index
            else:
                # If all attempts are used up, redirect to Gameover page
                return redirect(url_for('gameover', username=username))

    return render_template("game.html",
                            username=username, riddle_index=riddle_index, riddles=riddles,
                            answers=answers, attempts=store_all_attempts(username), remaining_attempts=attempts_remaining(username), score=end_score(username))


# GAMEOVER PAGE
@app.route('/<username>/gameover', methods=["GET", "POST"])
@login_required
@owner_or_admin
def gameover(username):

    clear_guesses(username)
    clear_score(username)

    if request.method =="POST":

        return redirect(url_for('game', username=username))

    return render_template("gameover.html",
                            username=username)


# FINISH PAGE
@app.route('/<username>/congratulations', methods=["GET", "POST"])
@login_required
@owner_or_admin
def congrats(username):

    clear_guesses(username)

    if request.method =="POST":
        usernames_and_scores = get_scores()
        return redirect(url_for('highscores', usernames_and_scores=usernames_and_scores))

    return render_template("congratulations.html",
                            username=username, score=end_score(username))

# HIGHSCORE PAGE
@app.route('/highscores', methods=["GET"])
def highscores():

    usernames_and_scores = get_scores()

    return render_template("highscores.html", page_title="Highscores", usernames_and_scores=usernames_and_scores)

@app.route('/history/share/<token>')
def shared_history(token):
    username = verify_history_token(token)
    if not username:
        return render_template("history.html", page_title="History", username=None, results=[], shareable_link=None, error="Invalid or expired share link.")

    results = show_results(username)
    return render_template("history.html", page_title="History", username=username, results=results, shareable_link=request.url, shared_view=True)


@app.route('/<username>/history', methods=["GET", "POST"])
def history(username):
    shareable_link = None
    if request.method == "POST":
        token = generate_history_token(username)
        shareable_link = url_for('shared_history', token=token, _external=True)

    results = show_results(username)

    return render_template("history.html", page_title="History", username=username, results=results, shareable_link=shareable_link, error=None)


if __name__ == '__main__':
    ip = "127.0.0.1"
    port = 8000
    app.run(host=ip,
            port=port,
            debug=True)
    


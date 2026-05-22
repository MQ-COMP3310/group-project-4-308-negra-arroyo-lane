# Security Code Comments Index

This document indexes all secure coding principle comments in the codebase.

## run.py - Security Comments

### Session Configuration (Lines 22-25)
```python
app.config['SESSION_COOKIE_HTTPONLY'] = True      # Prevent JS access
app.config['SESSION_COOKIE_SECURE'] = False       # Set to True in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'    # CSRF protection
```
**Principles**: Sensitive data protection, CSRF protection

### audit_log Function (Lines 52-67)
```python
def audit_log(actor, action, target_score, result):
    """
    Secure coding principle: accountability / repudiation protection.
    Log all score modification attempts with actor, action, timestamp, result.
    """
```
**Principle**: Accountability, Repudiation Protection

### validate_username_format Function (Lines 70-77)
```python
def validate_username_format(username):
    """
    Secure coding principle: treat all inputs as untrusted.
    Validate username format before use in file paths or database operations.
    """
```
**Principle**: Input Validation, Treat Inputs as Untrusted

### validate_password Function (Lines 80-87)
```python
def validate_password(password):
    """
    Validate password strength.
    Password must be at least 8 characters.
    """
```
**Principle**: Input Validation

### login_required Decorator (Lines 94-103)
```python
def login_required(f):
    """
    Secure coding principle: complete mediation.
    Routes decorated with this require an authenticated session.
    ACR-01: Use the authenticated session user, not just URL username.
    """
```
**Principles**: Authentication, Complete Mediation
**ACR**: ACR-01 (Use session user, not URL)

### admin_required Decorator (Lines 106-117)
```python
def admin_required(f):
    """
    Secure coding principle: role-based access control / least privilege.
    Routes decorated with this require admin role.
    ACR-04: Check role == 'admin' before allowing modifications.
    """
```
**Principles**: Role-Based Access Control, Least Privilege
**ACR**: ACR-04 (Admin-only modifications)

### owner_or_admin Decorator (Lines 120-138)
```python
def owner_or_admin(f):
    """
    Secure coding principle: least privilege.
    Users can only access their own data unless they're admin.
    ACR-02: Users may only view their own score history.
    """
```
**Principles**: Least Privilege, Access Control
**ACR**: ACR-02 (View own scores only)

### Login Route - Registration (Lines 254-278)
```python
# Input validation
if not validate_username_format(username):
    return render_template("index.html", page_title="Home", error="Invalid username format")

# Validation checks
if not validate_password(password):
    return render_template("index.html", page_title="Home", 
                         error="Password must be at least 8 characters")

# Secure coding principle: secure password storage (salted hash)
password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

# Log user creation (audit)
audit_log(username, "register", None, "success")
```
**Principles**: Input Validation, Secure Password Storage, Accountability

### Login Route - Authentication (Lines 285-301)
```python
# Secure coding principle: password verification
if not check_password_hash(user['password_hash'], password):
    audit_log(username, "login_failed", None, "invalid_password")

# Authentication successful
session['username'] = username
session['role'] = user.get('role', 'user')
audit_log(username, "login", None, "success")
```
**Principles**: Password Verification, Authentication, Accountability

### Logout Route (Lines 309-319)
```python
@app.route('/logout', methods=["POST"])
@login_required
def logout():
    """
    Secure coding principle: complete mediation.
    Clear session on logout.
    """
    username = session.get('username')
    audit_log(username, "logout", None, "success")
    session.clear()
```
**Principles**: Complete Mediation, Accountability

### User Route (Lines 323-338)
```python
@app.route('/<username>', methods=["GET", "POST"])
@login_required
@owner_or_admin
def user(username):
```
**Principles**: Authentication, Authorization, Least Privilege
**ACRs**: ACR-01, ACR-02

### Game Route (Lines 342-377)
```python
@app.route('/<username>/game', methods=["GET", "POST"])
@login_required
@owner_or_admin
def game(username):
    # Secure coding principle: server-side score authority.
    # The score is calculated by the application, not submitted by the browser.
    # Normal users can view recorded scores but cannot edit or delete them.
    record_completed_score(username, score)
```
**Principles**: Authentication, Authorization, Server-Side Authority
**ACR**: ACR-05 (Server-side score calculation)

### Game Over Route (Lines 388-408)
```python
@app.route('/<username>/gameover', methods=["GET", "POST"])
@login_required
@owner_or_admin
def gameover(username):
```
**Principles**: Authentication, Authorization

### Congrats Route (Lines 412-424)
```python
@app.route('/<username>/congratulations', methods=["GET", "POST"])
@login_required
@owner_or_admin
def congrats(username):
```
**Principles**: Authentication, Authorization

---

## score_feature.py - Security Comments

### validate_username Function (Lines 24-31)
```python
def validate_username(username):
    """
    Secure coding principle: treat all inputs as untrusted.
    Usernames are validated before being used in file paths.
    """
```
**Principle**: Input Validation, Treat Inputs as Untrusted

### login_required Decorator (Lines 34-44)
```python
def login_required(view_func):
    """
    Secure coding principle: complete mediation.
    Score-history routes require an authenticated session.
    """
```
**Principle**: Complete Mediation, Authentication

### admin_required Decorator (Lines 47-56)
```python
def admin_required(view_func):
    """
    Secure coding principle: role-based access control.
    Admin-only routes check the user's role before allowing access.
    ACR-04: Check role == 'admin' before modifying scores.
    """
```
**Principles**: Role-Based Access Control
**ACR**: ACR-04 (Admin role check)

### current_user_owns Function (Lines 59-66)
```python
def current_user_owns(username):
    """
    Secure coding principle: least privilege.
    A normal user may only view their own score history.
    ACR-02: Users may only view their own score history.
    """
```
**Principles**: Least Privilege
**ACR**: ACR-02 (Own data only)

### audit_log Function (Lines 70-86)
```python
def audit_log(actor, action, target_score, result):
    """
    Secure coding principle: accountability / repudiation protection.
    Log all score modification attempts with actor, action, timestamp, result.
    """
```
**Principles**: Accountability, Repudiation Protection

### score_history_path Function (Lines 97-104)
```python
def score_history_path(username):
    """
    Secure coding principle: safe file access.
    The username is validated before being used to build a file path.
    """
```
**Principle**: Safe File Access, Input Validation

### read_score_history Function (Lines 107-118)
```python
def read_score_history(username):
    """
    Read-only score history.
    Users can view scores, but this function does not provide edit/delete behaviour.
    """
```
**Principle**: Least Privilege, Read-Only Access

### write_score_history Function (Lines 121-129)
```python
def write_score_history(username, scores):
    """
    Internal helper used only by trusted server-side score recording.
    This is not exposed through any user-editable route.
    """
```
**Principle**: Server-Side Authority, Encapsulation

### record_completed_score Function (Lines 132-155)
```python
def record_completed_score(username, score):
    """
    Requirement implementation:
    Users must not be able to edit or delete their scores.

    Scores are recorded only by trusted server-side game logic.
    The browser never submits the final score value.
    """
```
**Principles**: Server-Side Authority, Data Integrity
**ACR**: ACR-05 (Server-side score authority)

### view_scores Route (Lines 162-175)
```python
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
```
**Principles**: Authentication, Least Privilege, Access Control
**ACR**: ACR-02

### user_cannot_edit_score Route (Lines 178-189)
```python
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
```
**Principles**: Deny by Default, Fail Securely, CSRF Protection, Accountability
**ACR**: ACR-03 (No score editing)

### user_cannot_delete_score Route (Lines 192-203)
```python
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
```
**Principles**: Deny by Default, Fail Securely, CSRF Protection, Accountability
**ACR**: ACR-03 (No score deletion)

---

## Summary of Security Principles Applied

### Principles Present in Code:
1. ✅ Treat all inputs as untrusted - Username, password, score validation
2. ✅ Authenticate and validate permissions - Login required, decorators, checks
3. ✅ Role-based access control - Admin role, @admin_required decorator
4. ✅ Least privilege - Users access own data only
5. ✅ Deny by default - Edit/delete return 403
6. ✅ Data integrity - Server-side score calculation
7. ✅ Sensitive data protected - Password hashing (PBKDF2 + salt)
8. ✅ Accountability - Audit logging on all events
9. ✅ Treat browser as untrusted - POST-only state changes, audit attempts
10. ✅ Fail securely - Proper HTTP status codes (400, 403, 404)

### ACRs Implemented:
- ✅ ACR-01: Use authenticated session user (login_required, session checks)
- ✅ ACR-02: View own scores only (owner_or_admin, current_user_owns)
- ✅ ACR-03: Cannot edit/delete (user_cannot_edit_score, user_cannot_delete_score return 403)
- ✅ ACR-04: Admin role check documented (@admin_required decorator)
- ✅ ACR-05: Server-side score authority (record_completed_score internal)

### Total Security Comments: 28+
- Principle comments: 20+
- ACR comments: 8+
- Requirement comments: Multiple throughout

All security comments follow consistent format:
- "Secure coding principle: X" for COMP3310 principles
- "ACR-0X:" for Access Control Rules
- "Requirement:" for NFSR-02 specifications

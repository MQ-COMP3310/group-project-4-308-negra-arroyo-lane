# Security Implementation: Score Access Control

## Overview
This document outlines the security features implemented to prevent users from editing or deleting their scores. The implementation follows COMP3310 security principles and meets all requirements in the NFSR-02 design specification.

## Architecture Overview

### Key Components
1. **Authentication System** (run.py): Login/registration with password hashing
2. **Session Management** (run.py): Secure session cookies with HTTPOnly and SameSite flags
3. **Authorization Layer** (run.py & score_feature.py): Role-based access control decorators
4. **Score Recording** (score_feature.py): Server-side only score calculation and storage
5. **Audit Logging** (run.py & score_feature.py): Tracks all modifications and access attempts
6. **Input Validation** (both files): All user inputs validated before use

---

## Security Controls Implemented

### 1. Authentication & Password Security

**Files**: `run.py`

**Implementation**:
- User registration with email/username validation
- Passwords hashed using `werkzeug.security.generate_password_hash()` with PBKDF2:SHA256
- Salt length: 16 characters (automatic per Werkzeug)
- Password strength requirement: minimum 8 characters
- Login verification using `check_password_hash()`

**Code Location**: `run.py` lines 37-87 (load_users, save_users, validate_password)

**Security Principle**: "Sensitive data protected at rest" + "Treat all inputs as untrusted"

---

### 2. Session-Based Authorization (ACR-01, ACR-02)

**Files**: `run.py`, `score_feature.py`

**Implementation**:
- Session cookie configuration:
  ```python
  app.config['SESSION_COOKIE_HTTPONLY'] = True      # Prevent JS access
  app.config['SESSION_COOKIE_SECURE'] = False       # Set True in production
  app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'    # CSRF protection
  ```
- Authenticated session user used for all access decisions, not URL parameter
- Session expires when browser closes

**Code Location**: 
- `run.py` lines 22-25 (session config)
- `run.py` lines 94-109 (login_required decorator)

**Security Principle**: "Validate permissions on every request" + "Authentication"

**ACR-01 Enforcement**: The `login_required` decorator checks `session.get("username")` rather than trusting the URL parameter.

---

### 3. Role-Based Access Control (ACR-03, ACR-04)

**Files**: `run.py`, `score_feature.py`

**Implementation**:
- Two user roles: "user" (default) and "admin"
- Normal users cannot edit or delete scores (403 Forbidden)
- Routes protected by decorators:
  - `@login_required`: Must be authenticated
  - `@admin_required`: Must have role=="admin"
  - `@owner_or_admin`: Can only access own data unless admin

**Code Location**:
- `run.py` lines 94-138 (authorization decorators)
- `score_feature.py` lines 48-64 (admin_required and current_user_owns)
- `score_feature.py` lines 178-203 (edit/delete routes)

**Security Principle**: "Role-based access control" + "Least privilege" + "Deny by default"

**ACR-03 Enforcement**: Routes `user_cannot_edit_score()` and `user_cannot_delete_score()` always return 403 for any user.

**ACR-04 Enforcement**: If admin score editing becomes required, use `@admin_required` decorator on admin-only routes.

---

### 4. Server-Side Score Authority (ACR-05)

**Files**: `run.py`, `score_feature.py`

**Implementation**:
- Scores calculated entirely by server-side game logic in `run.py`
- Score values are NOT accepted from the browser
- Only the server can call `record_completed_score()` (internal function)
- Browser submits answers; server calculates score

**Code Location**:
- `run.py` lines 156-206 (game logic, score calculation)
- `run.py` lines 209-224 (final_score function calls record_completed_score)
- `score_feature.py` lines 132-155 (record_completed_score validates input)

**Security Principle**: "Treat all inputs as untrusted" + "Data integrity"

**ACR-05 Enforcement**: The `record_completed_score()` function validates score as integer and only allows internal calls.

---

### 5. Input Validation

**Files**: `run.py`, `score_feature.py`

**Implementation**:
- Username format validation: `^[a-z0-9_]{3,30}$`
- Password minimum length: 8 characters
- Score value validation: must be valid integer
- All validation performed before use in file paths or database operations

**Code Location**:
- `run.py` lines 70-87 (validate_username_format, validate_password)
- `score_feature.py` lines 23-29 (validate_username)
- `score_feature.py` lines 132-155 (record_completed_score validation)

**Security Principle**: "Treat all inputs as untrusted" + "Input validation"

---

### 6. Audit Logging

**Files**: `run.py`, `score_feature.py`

**Implementation**:
- All authentication events logged: login, register, logout, login_failed
- All score modification attempts logged: edit_score_attempt, delete_score_attempt
- Log entries include: timestamp, actor (username), action, target_score, result
- Logs written to `data/audit.log` in JSON format (one entry per line)

**Code Location**:
- `run.py` lines 52-67 (audit_log function)
- `run.py` lines 274, 294, 301, 317 (login/logout audit calls)
- `score_feature.py` lines 70-86 (audit_log function)
- `score_feature.py` lines 188, 202 (edit/delete attempt audit calls)

**Security Principle**: "Accountability" + "Repudiation protection"

**Example Audit Log Entry**:
```json
{"timestamp": "2026-05-22T15:03:29", "actor": "user123", "action": "edit_score_attempt", "target_score": 0, "result": "forbidden"}
```

---

### 7. Secure Error Handling

**Files**: `run.py`, `score_feature.py`

**Implementation**:
- Flask `abort()` returns standard HTTP status codes
- No stack traces or internal file paths exposed to user
- 400: Bad Request (validation failure)
- 403: Forbidden (authorization failure)
- 404: Not Found (resource not found)
- Custom descriptions provided without sensitive details

**Code Location**:
- `run.py` lines 259 (invalid username returns 400)
- `score_feature.py` lines 28, 145 (validation failures return 400)
- `score_feature.py` lines 189, 203 (edit/delete return 403)

**Security Principle**: "Design code to fail securely"

---

### 8. CSRF Protection

**Files**: All form submissions are POST methods; requires POST for state-changing operations

**Implementation**:
- State-changing operations (logout, edit, delete) use POST method
- SameSite cookie flag set to 'Lax'
- No form tokens added (can be enhanced with Flask-WTF in future)

**Code Location**:
- `run.py` line 309 (logout is POST)
- `score_feature.py` lines 178, 192 (edit/delete are POST)

**Security Principle**: "Treat browser requests as untrusted" + "Request integrity"

---

### 9. Data Storage Changes

**Files**: `run.py`, `score_feature.py`

**User Accounts** (`data/users.json`):
```json
{
  "username": {
    "password_hash": "<pbkdf2:sha256$...>",
    "role": "user",
    "created_at": "2026-05-22T15:03:29"
  }
}
```

**Score History** (`data/score_history/<username>.json`):
```json
[
  {"score_id": 0, "score": 28},
  {"score_id": 1, "score": 35}
]
```

**Audit Log** (`data/audit.log`):
```json
{"timestamp": "2026-05-22T15:03:29", "actor": "user1", "action": "login", "target_score": null, "result": "success"}
```

---

## Access Control Rules (ACR) Implementation

| Rule ID | Rule | Implementation | Status |
|---------|------|----------------|--------|
| ACR-01 | Use authenticated session user, not URL username | `login_required` decorator checks `session.get("username")` | ✅ |
| ACR-02 | Normal user may only view own score history | `owner_or_admin` decorator + `current_user_owns()` check | ✅ |
| ACR-03 | Users must never edit or delete scores | Routes return 403 for all users | ✅ |
| ACR-04 | Score modification routes check role=="admin" | `@admin_required` decorator on future admin routes | ✅ (documented) |
| ACR-05 | Scores generated by server, not accepted from browser | Server calculates score from game logic only | ✅ |

---

## Endpoint Specifications

### Authentication Endpoints

| Endpoint | Method | Purpose | Access | Status |
|----------|--------|---------|--------|--------|
| `/` | GET | Login/register form | Public | ✅ |
| `/` | POST | Process login/registration | Public | ✅ |
| `/logout` | POST | Clear session | Logged-in users | ✅ |

### Score Endpoints

| Endpoint | Method | Allowed Users | Purpose | Status |
|----------|--------|---------------|---------|--------|
| `/<username>/scores` | GET | Owner/admin | View score history | ✅ |
| `/scores/<username>/<id>/edit` | POST | (None) | Edit score | ❌ 403 |
| `/scores/<username>/<id>/delete` | POST | (None) | Delete score | ❌ 403 |
| `/<username>/game` | POST | Owner/admin | Submit game answer | ✅ |

---

## Testing Security Requirements

### Test Cases

1. **Authentication**: 
   - ✅ Register new user with valid credentials
   - ✅ Login with correct password
   - ❌ Login with incorrect password
   - ✅ Session persists across requests
   - ✅ Logout clears session

2. **Authorization**:
   - ✅ Logged-in user can view own score history
   - ❌ User cannot view another user's scores
   - ❌ User cannot access game without login
   - ❌ User receives 403 when attempting to edit score
   - ❌ User receives 403 when attempting to delete score

3. **Input Validation**:
   - ✅ Invalid username rejected (regex validation)
   - ✅ Short password rejected (<8 chars)
   - ❌ Invalid score values rejected
   - ❌ Path traversal attempts blocked

4. **Server-Side Authority**:
   - ✅ Server calculates score from game logic
   - ❌ Browser cannot submit custom score value
   - ✅ Score recorded only via record_completed_score()

5. **Audit Logging**:
   - ✅ Login attempts recorded
   - ✅ Edit/delete attempts recorded with "forbidden" result
   - ✅ Log includes timestamp, actor, action, result

---

## Configuration & Deployment

### Development Configuration
```python
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = False  # HTTP in development
```

### Production Configuration
```python
app.secret_key = os.environ.get('SECRET_KEY', '<use strong random key>')
app.config['SESSION_COOKIE_SECURE'] = True   # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True # Always True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Can use Strict
```

---

## Security Checklist

- [x] User authentication with password hashing
- [x] Session-based authorization
- [x] Role-based access control
- [x] Input validation on all untrusted inputs
- [x] Server-side score calculation
- [x] Audit logging for accountability
- [x] Secure error handling (no internal details exposed)
- [x] HTTP status codes (400, 403, 404)
- [x] Access control decorators on protected routes
- [x] Secure session cookie configuration
- [x] CSRF protection via POST for state-changing operations

---

## Future Enhancements

1. **CSRF Token Protection**: Implement Flask-WTF for explicit CSRF tokens
2. **Admin Score Management**: Uncomment admin routes in score_feature.py if needed
3. **2FA Authentication**: Add two-factor authentication for admin accounts
4. **Rate Limiting**: Add rate limiting on login attempts
5. **HTTPS Enforcement**: Use HTTPS in production with secure cookies
6. **Database Migration**: Replace JSON files with encrypted database
7. **Audit Log Archival**: Archive old audit logs to prevent unbounded growth

---

## References

### COMP3310 Security Principles Applied
- Treat all inputs as untrusted (input validation)
- Authentication and validate permissions on every request
- Role-based access control and least privilege
- Deny by default, fail securely
- Sensitive data protected at rest (password hashing)
- Accountability and repudiation protection (audit logging)
- Treat browser requests as untrusted (CSRF protection)

### Tools & Libraries
- Flask 2.0.3: Web framework
- Werkzeug 2.2.2: Password hashing (generate_password_hash, check_password_hash)
- Python pathlib: Safe file path handling
- Python json: Secure JSON storage
- Flask-WTF 1.0.1: (Available for CSRF token enhancement)

---

## Implementation Notes

All security comments are prefixed with one of:
- "Secure coding principle:" - Indicates which COMP3310 principle is applied
- "ACR-0X:" - Indicates which Access Control Rule is enforced
- "Requirement:" - Indicates NFSR-02 design requirement

Comments identify exactly where secure coding has been applied.

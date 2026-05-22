# Simple Flask Riddle Game - COMP3310 Secure Implementation

## Overview

This codebase implements a secure riddle game in Python and Flask with comprehensive security controls to prevent users from editing or deleting their scores.

**COMP3310 Part 2 Requirement**: Users must not be able to edit or delete their scores.

## Game Rules

The user is required to register or login to start the game. Once authenticated, you get asked 10 riddles.

- Maximum score per riddle: 3 points
- 3 guesses per riddle allowed
- Each wrong guess deducts 1 point from that riddle's score
- Scores are recorded to a protected score history file
- Scores cannot be edited or deleted after recording
- Successful completion adds score to the highscore leaderboard

## Security Features Implemented

### 1. User Authentication ✅
- Registration with password hashing (PBKDF2:SHA256 with salt)
- Login with password verification
- Session-based authentication
- Logout with session clearing

### 2. Authorization & Access Control ✅
- **ACR-01**: Use authenticated session user for all access decisions
- **ACR-02**: Users can only view their own score history
- **ACR-03**: Users cannot edit or delete scores (403 Forbidden)
- **ACR-04**: Admin-only routes documented for future use
- **ACR-05**: Scores calculated by server, not accepted from browser

### 3. Input Validation ✅
- Username format validation: `^[a-z0-9_]{3,30}$`
- Password minimum length: 8 characters
- Score value validation: integers only
- Path traversal protection

### 4. Secure Session Management ✅
- HTTPOnly cookies (prevent JavaScript access)
- SameSite=Lax flag (CSRF protection)
- Secure flag (for HTTPS in production)
- Session user required for all protected routes

### 5. Audit Logging ✅
- All authentication events logged (login, register, logout)
- All score modification attempts logged with "forbidden" result
- Timestamps, actor, action, and result recorded
- JSON format for easy analysis (`data/audit.log`)

### 6. Secure Error Handling ✅
- HTTP 400 for invalid input
- HTTP 403 for unauthorized access
- HTTP 404 for not found
- No stack traces or internal file paths exposed

### 7. Server-Side Score Authority ✅
- Scores calculated entirely by server-side game logic
- Browser cannot submit score values
- Only `record_completed_score()` can record scores
- Score integrity guaranteed

## Setup

To setup the basic website you will need to have the following installed:

- python3
- pip

### Installation Steps

Create and activate a virtual environment:

```bash
python -m venv env        # use `python3 -m venv env` on Linux/macOS
source env/bin/activate   # use `env\Scripts\activate` on Windows
pip install -r requirements.txt
```

## Run the Website

You can run the website by typing:

```bash
python run.py
```

You can now browse to http://localhost:8000/ to view the website.

### Features
- Register a new account or login
- View your secure score history
- Play the riddle game with protected score recording
- View the public highscores leaderboard
- Logout to clear your session

## Project Structure

```
├── run.py                          # Main Flask app with auth & game logic
├── score_feature.py                # Score recording & access control
├── test_security.py                # Security test stubs
├── SECURITY_IMPLEMENTATION.md      # Detailed security documentation
├── requirements.txt                # Python dependencies
├── data/
│   ├── users.json                  # User accounts (password hashes)
│   ├── audit.log                   # Audit trail (JSON lines)
│   ├── score_history/              # User score histories (JSON)
│   ├── -riddles.txt                # Game riddle questions
│   ├── -answers.txt                # Riddle answers
│   └── -highscores.txt             # Public highscore list
└── templates/
    ├── index.html                  # Login/register form
    ├── welcome.html                # User profile page
    ├── game.html                   # Game page
    ├── scores.html                 # Score history (read-only)
    ├── congratulations.html        # Completion page
    ├── gameover.html               # Game over page
    ├── highscores.html             # Leaderboard
    └── base.html                   # Template base
```

## Security Documentation

For detailed information about the security implementation, see:

- **SECURITY_IMPLEMENTATION.md** - Full security architecture and implementation details
- **test_security.py** - Test stubs for security requirements
- Comments in `run.py` and `score_feature.py` - Inline security documentation

## Security Testing

Security-focused test stubs are provided in `test_security.py`:

```bash
pytest test_security.py -v        # Run security tests
```

Tests target:
- Authentication & password hashing
- Authorization & access control (ACR-01 through ACR-05)
- Input validation
- Server-side score authority
- Audit logging
- Secure error handling
- CSRF protection

## Key Security Classes & Functions

### run.py
- `login_required` - Decorator for authenticated routes
- `admin_required` - Decorator for admin-only routes
- `owner_or_admin` - Decorator for owner/admin routes
- `validate_username_format()` - Username validation
- `validate_password()` - Password validation
- `audit_log()` - Audit trail recording
- `/logout` - Session clearing endpoint

### score_feature.py
- `validate_username()` - Username validation for paths
- `admin_required` - Admin-only decorator
- `current_user_owns()` - Permission check
- `view_scores()` - Read-only score history view
- `user_cannot_edit_score()` - Returns 403 Forbidden
- `user_cannot_delete_score()` - Returns 403 Forbidden

## Configuration

### Development
```python
app.secret_key = 'dev-key-change-in-production'
app.config['SESSION_COOKIE_SECURE'] = False  # HTTP
```

### Production
Set environment variable before running:
```bash
export SECRET_KEY='<use strong random key>'
```

Then update `run.py`:
```python
app.config['SESSION_COOKIE_SECURE'] = True   # HTTPS only
```

## Known Issues

There is a slight problem with beginning a game that doesn't always happen. Once the user clicks the 'Play' button, there is a possibility of getting a server error. To get past this, press the back button on the browser and then click 'Play' again.

## Security Checklist

- [x] User authentication with password hashing
- [x] Session-based authorization
- [x] Role-based access control (admin/user)
- [x] Input validation on all untrusted data
- [x] Server-side score calculation
- [x] Audit logging for all modifications
- [x] Secure error handling (400, 403, 404)
- [x] HTTP status codes (no internal errors)
- [x] Access control decorators on protected routes
- [x] Secure session cookies (HTTPOnly, SameSite)
- [x] CSRF protection via POST methods
- [x] Secure code comments identifying principles

## Secure Coding Principles Applied

All implementations include comments identifying which COMP3310 secure coding principle is applied:

1. **Treat all inputs as untrusted** - Input validation on usernames, passwords, scores
2. **Authenticate and validate permissions on every request** - `login_required` & authorization checks
3. **Role-based access control** - Admin and user roles
4. **Least privilege** - Users can only access their own data
5. **Deny by default** - All edit/delete return 403
6. **Data integrity** - Server-side score authority
7. **Sensitive data protected at rest** - Password hashing
8. **Accountability** - Audit logging
9. **Treat browser requests as untrusted** - CSRF protection via POST
10. **Design code to fail securely** - Safe error codes, no stack traces

## References

- COMP3310 Week 8: Secure Coding Principles
- NFSR-02: Design Specification for Secure Score Access Control
- Werkzeug Security: Password hashing and verification
- Flask Security: Session management and authentication


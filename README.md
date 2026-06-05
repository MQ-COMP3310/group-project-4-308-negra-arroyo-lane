# Simple Flask Riddle Game — COMP3310 Secure Implementation

**Group:** 308-negra-arroyo-lane
**Repository:** `group-project-4-308-negra-arroyo-lane`

---

## Overview

This codebase is a riddle game written in **Python** and **Flask**. It began as a deliberately insecure sample application and has been re-engineered with security as a first-class concern across the software development life cycle.

The game presents ten riddles, tracks the player's score, and records completed games to a public leaderboard. On top of the core game, this version adds **authenticated accounts, protected score history, read-only score sharing, an administrator management area, per-session background-colour customisation, and a leaderboard search**, each built to a documented security requirement and covered by automated tests.

**Part 2 requirement honoured throughout:** users can *view* and *share* their previous scores but can never *edit* or *delete* them — only an authenticated administrator can.

---

## Game Rules

- The user must register or log in before starting a game.
- Each game asks 10 riddles.
- Maximum score per riddle is 3 points.
- 3 guesses are allowed per riddle; each wrong guess deducts 1 point from that riddle's score.
- Scores are calculated **server-side** and written to a protected score-history file.
- Scores cannot be edited or deleted after recording (by a normal user).
- Completing a game adds the total to the public highscore leaderboard.

---

## Features

### Core game
- Play through ten riddles with a per-riddle scoring and guess limit.
- Public highscore leaderboard.

### Authentication (Part 2)
- Account **registration** and **login** with salted password hashing.
- **Session-based** identity — access decisions use the authenticated session user, never the raw URL username.
- **Logout** clears the session.

### Score history and sharing (Part 2)
- Logged-in users can view their **own** previous scores in a **read-only** page.
- Users can generate a **signed, unguessable share link** that lets a non-user view a score result without logging in.
- Shared pages expose **no** edit, delete, or admin controls.

### Administrator area (Part 2)
- Admin dashboard and management pages, gated behind an `admin` role.
- Edit/delete public highscores, edit/delete stored user score-history records, and add/edit/delete riddles and answers.
- All admin state-changing actions are CSRF-protected and audit-logged.

### Feature 1 — Background colour customisation (Part 3)
- A user can enter a hex colour code to change the background for their current session only.
- Input is validated server-side against a strict allowlist; invalid input silently falls back to the default colour.

### Feature 2 — Highscore leaderboard search (Part 3)
- A search box on the leaderboard filters entries by username.
- Input is sanitised server-side (denylist of dangerous characters, length cap); no results shows a "No results found" message.

---

## Setup and Installation

You will need:

- Python 3 (the project was tested on Python 3.13)
- `pip`

### Installation steps

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv env          # use python3 on Linux/macOS
source env/bin/activate     # use env\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## Running the Website

```bash
python run.py
```

Then browse to **http://localhost:8000/**.

### Default Accounts

The following accounts are seeded for testing:

| Role | Username | Password |
|---|---|---|
| User | `aaron` | `turkey111` |
| Admin | `turkey11` | `turkey111` |

---

## Using the Application

1. **Register / log in.** From the home page (`/`), create an account or log in. Passwords are stored as salted hashes; the verified username and role are kept in the server-side session.
2. **Play a game.** After logging in you are taken to your welcome page; start a game and answer the ten riddles. Scores are computed server-side as you progress.
3. **View your score history.** Visit `/<username>/scores` to see your own previous scores in read-only form. Attempting to open another user's scores returns **403 Forbidden** (unless you are an administrator).
4. **Share a result.** Request `/<username>/history?share=1` to generate a read-only share link of the form `/history/share/<token>`. The token is signed and unguessable, and the shared page works without login while hiding all admin controls.
5. **Change the background colour.** On any page, submit a hex code (e.g. `#1f3864`) via the colour control. The value is validated server-side and applied to your session only. Invalid values fall back to the default.
6. **Search the leaderboard.** On `/highscores`, type a username into the search box (or use `/highscores?search=<term>`). The list filters to matching usernames; an empty box shows the default top-10 leaderboard.
7. **Administrate (admin role only).** Administrators sign in and reach the dashboard at `/admin/`, where they can manage highscores, user score histories, users' guesses, and riddles/answers. Non-admins receive 403 on every `/admin/` route.
8. **Log out.** Use `/logout` to clear your session.

---

## Endpoint Reference

| Endpoint | Method | Access | Purpose |
|---|---|---|---|
| `/` | GET, POST | Public | Login / register |
| `/<username>` | GET, POST | Logged-in user | Welcome page |
| `/<username>/game` | GET, POST | Logged-in user (owner) | Play / submit answer |
| `/<username>/scores` | GET | Owner or admin | Read-only score history |
| `/<username>/history?share=1` | GET | Owner | Generate read-only share link |
| `/history/share/<token>` | GET | Public (with valid token) | View a shared score result |
| `/highscores` | GET | Public | Leaderboard (`?search=<term>` to filter) |
| `/settings/set_colour` | POST | Public | Set session background colour |
| `/logout` | GET/POST | Logged-in user | Clear session |
| `/admin/login` | GET, POST | Public | Administrator login |
| `/admin/` | GET | Admin only | Administrator dashboard |
| `/admin/highscores` | GET | Admin only | Highscore management page |
| `/admin/highscores/<id>` | POST | Admin only | Edit / delete a public highscore |
| `/admin/scores/<username>/<id>/edit` | POST | Admin only | Edit a stored score-history record |
| `/admin/scores/<username>/<id>/delete` | POST | Admin only | Delete a stored score-history record |
| `/admin/users` | GET | Admin only | View registered users |
| `/admin/users/<username>/guesses` | GET, POST | Admin only | View / delete a user's guesses |
| `/admin/riddles` | GET | Admin only | Riddle management page |
| `/admin/riddles/<id>` | POST | Admin only | Edit / delete a riddle and answer |
| `/admin/riddles/add` | POST | Admin only | Add a new riddle and answer |

---

## Project Structure

```
group-project-4-308-negra-arroyo-lane/
├── run.py                       # Main Flask app: auth, game logic, Feature 1 & 2 helpers
├── admin.py                     # Administrator routes and content-management logic
├── score_feature.py            # Score recording, history, sharing, and access control
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── Riddle Game.json            # Game data (riddle set)
├── Riddle Game Appended.json   # Game data (appended riddle set)
├── .gitignore
├── data/                        # Runtime data store
│   ├── users.json               # User accounts (username, salted password hash, role)
│   ├── audit.log                # Audit trail of admin score edits/deletes (JSON lines)
│   ├── score_history/           # Per-user score history (JSON, e.g. aaron.json)
│   ├── -riddles.txt             # Riddle questions
│   ├── -answers.txt             # Riddle answers
│   └── -highscores.txt          # Public highscore list
├── static/
│   ├── custom/                  # Project CSS/JS
│   ├── img/                     # Images
│   └── vendor/                  # Third-party assets
├── templates/
│   ├── base.html                # Shared layout
│   ├── index.html               # Login / register
│   ├── welcome.html             # User welcome page
│   ├── game.html                # Game page
│   ├── score.html               # Single score view
│   ├── scores.html              # Read-only score history
│   ├── history.html             # History + share link page
│   ├── congratulations.html     # Completion page
│   ├── gameover.html            # Game-over page
│   ├── highscores.html          # Leaderboard (with search)
│   ├── admin_login.html         # Admin login
│   ├── admin_dashboard.html     # Admin dashboard
│   ├── admin_highscores.html    # Manage highscores
│   ├── admin_users.html         # Manage users / guesses
│   └── admin_riddles.html       # Manage riddles / answers
└── tests/
    ├── conftest.py                      # Shared pytest fixtures (app, client)
    ├── AdminFeatureTest.py              # Admin capability tests (AC-A01–AC-A06)
    ├── test_score_history_sharing.py    # Score history + sharing tests (AC-01–AC-05)
    ├── tests1.py                        # Feature 1: background colour tests (AC-1–AC-5)
    └── tests2.py                        # Feature 2: leaderboard search tests (AC-1–AC-5)
```

---

## Testing

All security requirements are covered by automated `pytest` tests. There are **43 tests across four test files**, all passing.

### Prerequisites

```bash
pip install pytest
```

`tests/conftest.py` adds the project root to `sys.path` and provides the shared `app` and `client` fixtures, so tests can import `run`, `admin`, and `score_feature` directly.

### Running the tests

> **Note:** `tests1.py`, `tests2.py`, and `AdminFeatureTest.py` do not match pytest's default `test_*.py` discovery pattern, so they must be named explicitly (or you must broaden discovery — see below). Run all four files from the **project root**:

```bash
pytest tests/AdminFeatureTest.py tests/test_score_history_sharing.py tests/tests1.py tests/tests2.py -v
```

Run a single feature's tests:

```bash
pytest tests/AdminFeatureTest.py -v            # Admin capabilities
pytest tests/test_score_history_sharing.py -v  # Score history & sharing
pytest tests/tests1.py -v                       # Feature 1: background colour
pytest tests/tests2.py -v                       # Feature 2: leaderboard search
```

**Optional — collect everything with a plain `pytest`.** Add a `pytest.ini` in the project root so the non-standard filenames are discovered automatically:

```ini
[pytest]
python_files = test_*.py *_test.py AdminFeatureTest.py tests1.py tests2.py
testpaths = tests
```

Then simply run:

```bash
pytest -v
```

---

### Test Inventory

#### Admin capabilities — `tests/AdminFeatureTest.py` (14 tests)

Feature requirement: administrators must be able to edit and delete application content.

| Test | AC | Verifies |
|---|---|---|
| `test_ac_a01_admin_can_access_dashboard` | AC-A01 | Admin GET `/admin/` returns 200 |
| `test_ac_a01_admin_can_access_highscore_management_page` | AC-A01 | Admin GET `/admin/highscores` returns 200 |
| `test_ac_a01_admin_can_access_riddle_management_page` | AC-A01 | Admin GET `/admin/riddles` returns 200 |
| `test_ac_a02_admin_can_edit_public_highscore` | AC-A02 | Admin edit updates the highscore value |
| `test_ac_a02_admin_can_delete_public_highscore` | AC-A02 | Admin delete removes the highscore entry |
| `test_ac_a03_admin_can_edit_stored_user_score_history` | AC-A03 | Admin edit changes a stored score (10 → 50) |
| `test_ac_a03_admin_can_delete_stored_user_score_history` | AC-A03 | Admin delete removes a score and renumbers IDs |
| `test_ac_a04_admin_can_edit_riddle_and_answer` | AC-A04 | Admin edit updates both riddle and answer |
| `test_ac_a04_admin_can_delete_riddle_and_answer` | AC-A04 | Admin delete clears the riddle/answer pair |
| `test_ac_a04_admin_can_add_riddle_and_answer` | AC-A04 | Admin add saves a new riddle/answer |
| `test_ac_a05_invalid_highscore_input_rejected_before_file_modified` | AC-A05 | Non-numeric highscore → 400, file unchanged |
| `test_ac_a05_invalid_stored_score_input_rejected_before_file_modified` | AC-A05 | Non-numeric stored score → 400, file unchanged |
| `test_ac_a05_invalid_riddle_input_rejected_before_file_modified` | AC-A05 | Empty riddle → 400, files unchanged |
| `test_ac_a06_admin_state_changing_action_requires_csrf` | AC-A06 | POST without CSRF token → 400 |

#### Score history & sharing — `tests/test_score_history_sharing.py` (9 tests)

Feature requirement: logged-in users can view their own previous scores read-only and generate a shareable read-only link.

| Test | AC | Verifies |
|---|---|---|
| `test_ac_01_logged_in_user_can_view_own_previous_scores` | AC-01 | Owner sees own scores (200, score shown) |
| `test_ac_01_score_history_page_does_not_show_normal_user_edit_delete_controls` | AC-01 | Score page is read-only (no edit/delete/admin controls) |
| `test_ac_02_normal_user_cannot_view_another_users_score_history` | AC-02 | Other user → 403 Forbidden |
| `test_ac_02_admin_can_view_another_users_score_history` | AC-02 | Admin can view any user's scores (200) |
| `test_ac_03_user_can_generate_shareable_read_only_link` | AC-03 | `?share=1` returns a `/history/share/<token>` link |
| `test_ac_03_generated_share_link_can_be_opened_without_login` | AC-03 | Share link works after the session is cleared |
| `test_ac_04_shared_score_page_does_not_expose_admin_functionality` | AC-04 | Shared page hides admin/edit/delete controls |
| `test_ac_05_random_or_invalid_share_link_is_rejected` | AC-05 | Guessed token → invalid/expired message, no data leak |
| `test_ac_05_generated_share_link_contains_signed_unpredictable_token` | AC-05 | Token is signed/unguessable (not the username, >20 chars) |

#### Feature 1 — background colour — `tests/tests1.py` (10 tests)

| Test | AC | Verifies |
|---|---|---|
| `test_valid_six_digit_hex` | AC-1 | Valid 6-digit hex is accepted |
| `test_three_digit_hex` | AC-1 | Valid 3-digit hex is accepted |
| `test_CSS_rejection` | AC-2 | CSS injection attempt falls back to default |
| `test_hash_exists` | AC-2 | Input without leading `#` is rejected |
| `test_hex_chars` | AC-2 | Non-hex characters are rejected |
| `test_input_leng` | AC-3 | Over-length input is rejected |
| `test_blank_input` | AC-3 | Empty input restores the default colour |
| `test_colour_storage` | AC-4 | Valid colour POST is stored in the session |
| `test_invalid_storage` | AC-4 | Invalid colour POST stores the default in the session |
| `test_set_colour_redirects` | AC-5 | `set_colour` redirects (no error details exposed) |

#### Feature 2 — leaderboard search — `tests/tests2.py` (10 tests)

| Test | AC | Verifies |
|---|---|---|
| `test_valid` | AC-1 | Alphanumeric search term is accepted |
| `test_special_char` | AC-1 | Cosmetic characters (e.g. `_`) are allowed |
| `test_special_reject` | AC-2 | `<>` is rejected |
| `test_special_reject2` | AC-2 | `/` is rejected |
| `test_special_reject3` | AC-2 | `:;` is rejected |
| `test_max_leng` | AC-3 | Over-length search (31 chars) is rejected |
| `test_blank_input` | AC-3 | Empty input returns nothing |
| `test_search_filters_correctly` | AC-4 | Search returns the matching username |
| `test_no_results_found` | AC-4 | Non-existent username → "No results found" |
| `test_invalid_search_no_error_exposed` | AC-5 | Injection payload is not reflected to the page |

---

## Security Features Implemented

- **Authentication** with salted password hashing (Werkzeug `generate_password_hash` / `check_password_hash`).
- **Session-based authorisation** — decisions use the authenticated session user, not the URL username.
- **Role-based access control** (`user` vs `admin`) with admin-only routes.
- **Deny by default** — all score edit/delete paths return 403 for non-admins.
- **Server-side score authority** — final scores are computed and stored by server logic; the browser cannot submit a final score.
- **Input validation** — usernames, score IDs, colours, and search terms are validated/sanitised before use.
- **CSRF protection** on admin state-changing POST routes.
- **Signed share tokens** — read-only share links use an unguessable, signed token.
- **Audit logging** — admin score edits/deletes are logged with actor, action, target, timestamp, and result.
- **Secure error handling** — 400 / 403 / 404 responses with no stack traces or internal paths.

### Secure coding principles applied

Inline comments in `run.py`, `admin.py`, and `score_feature.py` identify where each COMP3310 principle is applied:

1. Treat all inputs as untrusted — input validation on usernames, passwords, scores, colours, and search terms.
2. Authenticate and validate permissions on every request.
3. Role-based access control (admin / user).
4. Least privilege — users can only access their own data.
5. Deny by default — edit/delete returns 403 for non-admins.
6. Data integrity — server-side score authority.
7. Sensitive data protected at rest — password hashing.
8. Accountability — audit logging.
9. Treat browser requests as untrusted — CSRF protection.
10. Design code to fail securely — safe error codes, no stack traces.

---

## Configuration

### Development
The application defaults to local development settings and runs on `127.0.0.1:8000`.

### Production (recommended)
Set a strong secret key from the environment rather than hard-coding it, disable debug mode, and enforce secure cookies:

```bash
export SECRET_KEY='<use a strong random key, e.g. python -c "import secrets; print(secrets.token_hex(32))">'
```

```python
# in run.py (production)
app.secret_key = os.environ['SECRET_KEY']
app.config['SESSION_COOKIE_SECURE'] = True    # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# run behind a production WSGI server (e.g. Gunicorn); do not use debug=True
```

---

## Known Issues

- Occasionally, clicking **Play** to begin a game can produce a server error. If this happens, use the browser's back button and click **Play** again.

---

## References and AI Assistance

- COMP3310 Week 8: Secure Coding Principles.
- Werkzeug Security — password hashing and verification.
- Flask — session management and authentication.
- NFSR-02 — design specification for secure score-access control (see the project report).

Generative AI tools were used in an assistance capacity only (e.g. resolving merge conflicts and debugging); all outputs were reviewed and verified before use. See the report's GAITs section for per-member declarations and model versions.

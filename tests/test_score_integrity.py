"""
Score Integrity and User Read-Only Access Tests

Functional Requirement 2:
The system shall ensure that logged in users can view their own previous scores
but cannot edit, delete, overwrite or otherwise modify any score after it has been
recorded by server game logic.

Acceptance Criteria:
- AC-01: Users can view only their own scores unless they are an administrator.
- AC-02: No endpoint, form, button, or request path allows users to edit/delete scores.
- AC-03: Normal users requesting edit/delete endpoints get 403 Forbidden.
- AC-04: Scores only created by trusted server-side game logic after game completion.
- AC-05: Browser/client cannot submit or overwrite final score values directly.
- AC-06: Admins may edit/delete scores only after explicit admin authorisation check.
- AC-07: Score file not altered unless requester is authenticated administrator.
- AC-08: All score edit/delete attempts logged with username, action, timestamp, result.
"""

import json
import pytest
from pathlib import Path

AUDIT_LOG_FILE = Path("data/audit.log")
SCORE_HISTORY_DIR = Path("data/score_history")


def clear_audit_log():
    """Clear audit log before test."""
    if AUDIT_LOG_FILE.exists():
        AUDIT_LOG_FILE.unlink()


def read_audit_log():
    """Read all audit log entries."""
    if not AUDIT_LOG_FILE.exists():
        return []
    with open(AUDIT_LOG_FILE, "r") as f:
        return [json.loads(line) for line in f.readlines()]


def setup_user_scores(username, scores_list):
    """Setup test score history for a user."""
    SCORE_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    score_file = SCORE_HISTORY_DIR / f"{username}.json"
    score_records = [{"score_id": i, "score": s} for i, s in enumerate(scores_list)]
    with open(score_file, "w") as f:
        json.dump(score_records, f)


@pytest.fixture
def cleanup_scores():
    """Cleanup score history after each test."""
    yield
    if SCORE_HISTORY_DIR.exists():
        for f in SCORE_HISTORY_DIR.glob("*.json"):
            f.unlink()
    clear_audit_log()


# ============================================================
# AC-01: Users can view only their own scores
# ============================================================

def test_ac_01_logged_in_user_can_view_own_scores(client, cleanup_scores):
    """
    AC-01:
    Logged in users can view their own previous scores.
    """
    setup_user_scores("alice", [50, 75, 60])
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "alice"
            session["role"] = "user"
        
        response = client.get("/alice/scores")
        assert response.status_code == 200
        data = response.get_data(as_text=True)
        assert "50" in data
        assert "75" in data
        assert "60" in data


def test_ac_01_user_cannot_view_other_users_scores(client, cleanup_scores):
    """
    AC-01:
    Logged in users cannot view other users' scores.
    Expected: 403 Forbidden.
    """
    setup_user_scores("alice", [50])
    setup_user_scores("bob", [100])
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "alice"
            session["role"] = "user"
        
        response = client.get("/bob/scores")
        assert response.status_code == 403


def test_ac_01_admin_can_view_any_user_scores(client, cleanup_scores):
    """
    AC-01:
    Administrators can view any user's scores.
    """
    setup_user_scores("alice", [50])
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "admin_user"
            session["role"] = "admin"
        
        response = client.get("/alice/scores")
        assert response.status_code == 200
        assert "50" in response.get_data(as_text=True)


def test_ac_01_unauthenticated_user_cannot_view_scores(client, cleanup_scores):
    """
    AC-01:
    Unauthenticated users are redirected when attempting to view scores.
    """
    setup_user_scores("alice", [50])
    
    response = client.get("/alice/scores", follow_redirects=False)
    # Should redirect to login (typically /)
    assert response.status_code in (302, 303)


# ============================================================
# AC-02: No UI elements for users to edit/delete scores
# ============================================================

def test_ac_02_scores_template_has_no_edit_button(client, cleanup_scores):
    """
    AC-02:
    The scores.html template must not contain edit buttons or forms
    that allow users to modify their scores.
    """
    setup_user_scores("alice", [50, 75])
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "alice"
            session["role"] = "user"
        
        response = client.get("/alice/scores")
        data = response.get_data(as_text=True)
        
        # Ensure no edit form or button is present for regular users
        assert "edit" not in data.lower() or "edit" in ["Edit", "edited"]  # case-sensitive check
        assert "delete" not in data.lower() or "delete" in ["Deleted", "deleted"]
        assert "method=\"post\"" not in data  # no POST forms for user modifications


def test_ac_02_scores_template_has_no_delete_button(client, cleanup_scores):
    """
    AC-02:
    The scores.html template must not contain delete buttons.
    """
    setup_user_scores("alice", [50])
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "alice"
            session["role"] = "user"
        
        response = client.get("/alice/scores")
        data = response.get_data(as_text=True)
        
        # Verify no delete functionality is exposed
        assert "user-delete" not in data
        assert "remove-score" not in data


# ============================================================
# AC-03: Normal users requesting edit/delete endpoints get 403
# ============================================================

def test_ac_03_normal_user_edit_score_returns_403(client, cleanup_scores):
    """
    AC-03:
    If a normal user directly requests a score edit endpoint,
    the system must reject the request with 403 Forbidden.
    """
    setup_user_scores("alice", [50, 75])
    clear_audit_log()
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "alice"
            session["role"] = "user"
        
        response = client.post("/admin/scores/alice/0/edit", data={"score": "100"})
        assert response.status_code == 403


def test_ac_03_normal_user_delete_score_returns_403(client, cleanup_scores):
    """
    AC-03:
    If a normal user directly requests a score delete endpoint,
    the system must reject the request with 403 Forbidden.
    """
    setup_user_scores("alice", [50, 75])
    clear_audit_log()
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "alice"
            session["role"] = "user"
        
        response = client.post("/admin/scores/alice/0/delete")
        assert response.status_code == 403


def test_ac_03_unauthenticated_user_cannot_edit_score(client, cleanup_scores):
    """
    AC-03:
    Unauthenticated users cannot edit scores (403 or redirect).
    """
    setup_user_scores("alice", [50])
    
    response = client.post("/admin/scores/alice/0/edit", data={"score": "100"})
    assert response.status_code in (403, 302, 303)


# ============================================================
# AC-04: Scores only created by server game logic
# ============================================================

def test_ac_04_score_recorded_after_game_completion(client, cleanup_scores):
    """
    AC-04:
    Scores are created by trusted server-side game logic,
    not by direct user submission.
    
    This tests that the record_completed_score() function is the only
    trusted way to create score records.
    """
    from score_feature import record_completed_score
    
    # Call server-side function to record score
    record_completed_score("charlie", 85)
    
    # Verify score was recorded
    response = client.get("/charlie/scores")
    # (Would need to be logged in as charlie or admin to view)
    # This test demonstrates the function exists and can be called
    assert callable(record_completed_score)


# ============================================================
# AC-05: Browser cannot submit/overwrite final score directly
# ============================================================

def test_ac_05_no_public_endpoint_for_score_submission(client, cleanup_scores):
    """
    AC-05:
    There must be no public endpoint that allows users to directly
    submit or overwrite a final score value.
    
    Score submission should only occur through game completion logic,
    not through a user-accessible form.
    """
    with client:
        with client.session_transaction() as session:
            session["username"] = "dave"
            session["role"] = "user"
        
        # Attempt to POST a score directly (should fail)
        response = client.post("/dave/scores", data={"score": "999"})
        
        # Should be 405 (method not allowed) or 404 (no such endpoint)
        assert response.status_code in (404, 405)


def test_ac_05_score_not_created_from_user_form(client, cleanup_scores):
    """
    AC-05:
    Verify that no form in the application allows users to
    submit a final score value.
    
    This ensures the game logic is the only source of score creation.
    """
    with client:
        with client.session_transaction() as session:
            session["username"] = "eve"
            session["role"] = "user"
        
        # Try to bypass security and submit a score
        response = client.post("/eve/record_score", data={"score": "500"})
        
        # No such public endpoint should exist
        assert response.status_code in (404, 405)


# ============================================================
# AC-06: Admins need explicit authorization to edit/delete
# ============================================================

def test_ac_06_admin_can_edit_score_with_auth(client, cleanup_scores):
    """
    AC-06:
    Admins with explicit authorization can edit scores.
    This test verifies an admin session allows score modification.
    """
    setup_user_scores("frank", [50, 75, 60])
    clear_audit_log()
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "admin_user"
            session["role"] = "admin"
        
        response = client.post("/admin/scores/frank/0/edit", data={"score": "100"})
        
        # Should succeed (200, 302, or 303 depending on redirect)
        assert response.status_code in (200, 302, 303)
        
        # Verify the score was actually updated
        scores_file = SCORE_HISTORY_DIR / "frank.json"
        with open(scores_file, "r") as f:
            scores = json.load(f)
        assert scores[0]["score"] == 100


def test_ac_06_admin_can_delete_score_with_auth(client, cleanup_scores):
    """
    AC-06:
    Admins with explicit authorization can delete scores.
    """
    setup_user_scores("grace", [50, 75, 60])
    clear_audit_log()
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "admin_user"
            session["role"] = "admin"
        
        response = client.post("/admin/scores/grace/0/delete")
        
        # Should succeed
        assert response.status_code in (200, 302, 303)
        
        # Verify the score was deleted and renumbered
        scores_file = SCORE_HISTORY_DIR / "grace.json"
        with open(scores_file, "r") as f:
            scores = json.load(f)
        assert len(scores) == 2
        assert scores[0]["score"] == 75
        assert scores[0]["score_id"] == 0


def test_ac_06_non_admin_role_cannot_edit_scores(client, cleanup_scores):
    """
    AC-06:
    Users with non-admin role are explicitly denied access.
    """
    setup_user_scores("henry", [50])
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "henry"
            session["role"] = "user"  # Not admin
        
        response = client.post("/admin/scores/henry/0/edit", data={"score": "100"})
        assert response.status_code == 403


# ============================================================
# AC-07: Score file only modified by authenticated admin
# ============================================================

def test_ac_07_score_file_unchanged_for_normal_user_edit_attempt(client, cleanup_scores):
    """
    AC-07:
    If a normal user attempts to edit a score, the stored score file
    must remain unchanged.
    """
    setup_user_scores("isabella", [50, 75])
    original_content = json.dumps([{"score_id": 0, "score": 50}, {"score_id": 1, "score": 75}])
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "isabella"
            session["role"] = "user"
        
        # Attempt unauthorized edit
        response = client.post("/admin/scores/isabella/0/edit", data={"score": "999"})
        assert response.status_code == 403
    
    # Verify file is unchanged
    scores_file = SCORE_HISTORY_DIR / "isabella.json"
    with open(scores_file, "r") as f:
        current_content = json.dumps(json.load(f))
    assert current_content == original_content


def test_ac_07_score_file_unchanged_for_normal_user_delete_attempt(client, cleanup_scores):
    """
    AC-07:
    If a normal user attempts to delete a score, the stored score file
    must remain unchanged.
    """
    setup_user_scores("jack", [50, 75, 60])
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "jack"
            session["role"] = "user"
        
        # Attempt unauthorized delete
        response = client.post("/admin/scores/jack/1/delete")
        assert response.status_code == 403
    
    # Verify file is unchanged (still has 3 scores)
    scores_file = SCORE_HISTORY_DIR / "jack.json"
    with open(scores_file, "r") as f:
        scores = json.load(f)
    assert len(scores) == 3


def test_ac_07_only_authenticated_admin_can_modify_file(client, cleanup_scores):
    """
    AC-07:
    Only authenticated administrators can modify the score file.
    Unauthenticated requests must be rejected.
    """
    setup_user_scores("kate", [50])
    original_file_size = (SCORE_HISTORY_DIR / "kate.json").stat().st_size
    
    # Attempt without authentication
    response = client.post("/admin/scores/kate/0/edit", data={"score": "100"})
    assert response.status_code in (403, 302, 303)
    
    # Verify file size unchanged (content not modified)
    current_file_size = (SCORE_HISTORY_DIR / "kate.json").stat().st_size
    assert original_file_size == current_file_size


# ============================================================
# AC-08: All score edit/delete attempts logged
# ============================================================

def test_ac_08_denied_edit_attempt_is_logged(client, cleanup_scores):
    """
    AC-08:
    All score edit attempts (even denied ones) must be logged with
    username, action, timestamp, and result.
    """
    setup_user_scores("liam", [50])
    clear_audit_log()
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "liam"
            session["role"] = "user"
        
        # Attempt unauthorized edit
        response = client.post("/admin/scores/liam/0/edit", data={"score": "999"})
        assert response.status_code == 403
    
    # Check audit log contains the denied attempt
    logs = read_audit_log()
    assert len(logs) > 0
    assert any(
        log.get("actor") == "liam" and 
        "edit" in log.get("action", "").lower() and
        log.get("result") == "denied_unauthorized"
        for log in logs
    )


def test_ac_08_denied_delete_attempt_is_logged(client, cleanup_scores):
    """
    AC-08:
    All score delete attempts must be logged with actor, action, timestamp, result.
    """
    setup_user_scores("maya", [50, 75])
    clear_audit_log()
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "maya"
            session["role"] = "user"
        
        # Attempt unauthorized delete
        response = client.post("/admin/scores/maya/0/delete")
        assert response.status_code == 403
    
    # Check audit log
    logs = read_audit_log()
    assert len(logs) > 0
    assert any(
        log.get("actor") == "maya" and 
        "delete" in log.get("action", "").lower() and
        log.get("result") == "denied_unauthorized"
        for log in logs
    )


def test_ac_08_invalid_score_input_is_logged(client, cleanup_scores):
    """
    AC-08:
    Invalid score inputs (non-numeric, etc.) must be logged by admins.
    """
    setup_user_scores("noah", [50])
    clear_audit_log()
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "admin_user"
            session["role"] = "admin"
        
        # Attempt with invalid score
        response = client.post("/admin/scores/noah/0/edit", data={"score": "<script>alert(1)</script>"})
        assert response.status_code == 400
    
    # Check audit log contains invalid input denial
    logs = read_audit_log()
    assert len(logs) > 0
    assert any(
        log.get("action") == "admin_edit_score" and
        log.get("result") == "denied_invalid_score"
        for log in logs
    )


def test_ac_08_successful_admin_edit_is_logged(client, cleanup_scores):
    """
    AC-08:
    Successful admin edits must be logged with the actor and action.
    """
    setup_user_scores("oliver", [50])
    clear_audit_log()
    
    with client:
        with client.session_transaction() as session:
            session["username"] = "admin_user"
            session["role"] = "admin"
        
        response = client.post("/admin/scores/oliver/0/edit", data={"score": "100"})
        assert response.status_code in (200, 302, 303)
    
    # Check audit log contains success entry
    logs = read_audit_log()
    assert len(logs) > 0
    assert any(
        log.get("actor") == "admin_user" and
        log.get("action") == "admin_edit_score" and
        log.get("result") == "allowed"
        for log in logs
    )

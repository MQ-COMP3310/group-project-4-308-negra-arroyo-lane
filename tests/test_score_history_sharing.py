"""
Score History and Share-Link Tests

Feature requirement:
Logged-in users can view their own previous scores in read-only form and generate
a shareable read-only link for score history/results.

Acceptance criteria covered:
AC-01: Logged in users must be able to view their own previous scores in read-only form.
AC-02: Users must not be able to view another user’s score history unless they are an administrator.
AC-03: Users must be able to generate a shareable read-only link for an individual score result.
AC-04: Shared score pages must not expose, edit or delete administrative functionality.
AC-05: Generated links should not be easily accessible to people who have not been shared the link.
"""

import json
import re
import pytest


@pytest.fixture
def normal_user_session(client):
    """
    Logs in as normal user aaron.
    """
    with client.session_transaction() as session:
        session["username"] = "aaron"
        session["role"] = "user"


@pytest.fixture
def other_user_session(client):
    """
    Logs in as a different normal user.
    """
    with client.session_transaction() as session:
        session["username"] = "bob"
        session["role"] = "user"


@pytest.fixture
def admin_session(client):
    """
    Logs in as admin user turkey11.
    """
    with client.session_transaction() as session:
        session["username"] = "turkey11"
        session["role"] = "admin"


def test_ac_01_logged_in_user_can_view_own_previous_scores(client, tmp_path, monkeypatch, normal_user_session):
    """
    AC-01:
    Logged-in users must be able to view their own previous scores in read-only form.

    What this test does:
    It creates a temporary score-history file for aaron, logs in as aaron,
    then requests /aaron/scores.

    Expected result:
    The response is 200 OK and contains the stored score.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 25}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.get("/aaron/scores")

    assert response.status_code == 200
    assert b"25" in response.data


def test_ac_01_score_history_page_does_not_show_normal_user_edit_delete_controls(
    client,
    tmp_path,
    monkeypatch,
    normal_user_session
):
    """
    AC-01:
    Score history must be read-only for normal logged-in users.

    What this test does:
    It loads aaron's score-history page as aaron and checks that admin modification
    controls are not visible.

    Expected result:
    The page does not contain edit/delete form actions for stored scores.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 25}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.get("/aaron/scores")

    assert response.status_code == 200
    assert b"admin_edit_score" not in response.data
    assert b"admin_delete_score" not in response.data
    assert b"/admin/scores/aaron/0/edit" not in response.data
    assert b"/admin/scores/aaron/0/delete" not in response.data


def test_ac_02_normal_user_cannot_view_another_users_score_history(
    client,
    tmp_path,
    monkeypatch,
    other_user_session
):
    """
    AC-02:
    Users must not be able to view another user's score history unless they are an administrator.

    What this test does:
    It logs in as bob and attempts to access /aaron/scores.

    Expected result:
    The request is rejected with 403 Forbidden.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 25}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.get("/aaron/scores")

    assert response.status_code == 403


def test_ac_02_admin_can_view_another_users_score_history(
    client,
    tmp_path,
    monkeypatch,
    admin_session
):
    """
    AC-02:
    Administrators are allowed to view another user's score history.

    What this test does:
    It logs in as admin turkey11 and accesses /aaron/scores.

    Expected result:
    The response is 200 OK and contains aaron's stored score.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 25}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.get("/aaron/scores")

    assert response.status_code == 200
    assert b"25" in response.data


def test_ac_03_user_can_generate_shareable_read_only_link(
    client,
    tmp_path,
    monkeypatch,
    normal_user_session
):
    """
    AC-03:
    Users must be able to generate a shareable read-only link for a score result/history page.

    What this test does:
    It logs in as aaron and requests /aaron/history?share=1.

    Expected result:
    The response contains a generated /history/share/<token> link.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 25}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.get("/aaron/history?share=1")

    assert response.status_code == 200
    assert b"/history/share/" in response.data


def test_ac_03_generated_share_link_can_be_opened_without_login(
    client,
    tmp_path,
    monkeypatch,
    normal_user_session
):
    """
    AC-03:
    A generated share link must allow read-only access to the shared result/history.

    What this test does:
    It generates a share link as aaron, clears the session, then opens the share link.

    Expected result:
    The shared page loads without requiring login and displays the score.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 25}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.get("/aaron/history?share=1")
    page_text = response.data.decode("utf-8")

    match = re.search(r"/history/share/[^\"']+", page_text)
    assert match is not None

    share_path = match.group(0)

    with client.session_transaction() as session:
        session.clear()

    shared_response = client.get(share_path)

    assert shared_response.status_code == 200
    assert b"25" in shared_response.data


def test_ac_04_shared_score_page_does_not_expose_admin_functionality(
    client,
    tmp_path,
    monkeypatch,
    normal_user_session
):
    """
    AC-04:
    Shared score pages must not expose edit/delete/admin functionality.

    What this test does:
    It generates a share link, opens it without a logged-in session, and checks
    that the shared page does not contain admin-only actions or admin endpoints.

    Expected result:
    No edit/delete/admin controls are shown.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 25}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.get("/aaron/history?share=1")
    page_text = response.data.decode("utf-8")

    match = re.search(r"/history/share/[^\"']+", page_text)
    assert match is not None

    share_path = match.group(0)

    with client.session_transaction() as session:
        session.clear()

    shared_response = client.get(share_path)

    assert shared_response.status_code == 200
    assert b"/admin/" not in shared_response.data
    assert b"Edit" not in shared_response.data
    assert b"Delete" not in shared_response.data
    assert b"admin_edit_score" not in shared_response.data
    assert b"admin_delete_score" not in shared_response.data


def test_ac_05_random_or_invalid_share_link_is_rejected(client):
    """
    AC-05:
    Generated links should not be easily accessible to people who have not been shared the link.

    What this test does:
    It tries to access a fake, guessed share token.

    Expected result:
    The application does not reveal score history and displays an invalid/expired link response.
    """
    response = client.get("/history/share/fake-guessed-token")

    assert response.status_code == 200
    assert b"Invalid or expired share link" in response.data
    assert b"25" not in response.data
    assert b"/admin/" not in response.data


def test_ac_05_generated_share_link_contains_signed_unpredictable_token(
    client,
    tmp_path,
    monkeypatch,
    normal_user_session
):
    """
    AC-05:
    Generated links should not be easily accessible to people who have not been shared the link.

    What this test does:
    It generates a share link and checks that the token is not simply the username
    or an obvious sequential value.

    Expected result:
    The link contains a signed token string, not /history/share/aaron.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 25}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.get("/aaron/history?share=1")
    page_text = response.data.decode("utf-8")

    assert "/history/share/aaron" not in page_text

    match = re.search(r"/history/share/([^\"']+)", page_text)
    assert match is not None

    token = match.group(1)

    assert len(token) > 20
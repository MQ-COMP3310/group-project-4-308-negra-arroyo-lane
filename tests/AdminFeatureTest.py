"""
Admin Capability Tests

Feature requirement:
Administrators must be able to edit and delete application content.

Acceptance criteria covered:
AC-A01: Admins can access admin dashboard and admin management pages.
AC-A02: Admins can edit and delete public highscores.
AC-A03: Admins can edit and delete stored user score history records.
AC-A04: Admins can edit, delete, and add riddles/answers.
AC-A05: Invalid admin input is rejected before files are modified.
AC-A06: Admin state-changing actions are CSRF protected.
"""

import json
import pytest


@pytest.fixture
def admin_session(client):
    """
    Creates an authenticated admin session.

    Used by AC-A01, AC-A02, AC-A03, AC-A04, and AC-A05 tests.
    """
    with client.session_transaction() as session:
        session["username"] = "turkey11"
        session["role"] = "admin"


def test_ac_a01_admin_can_access_dashboard(client, admin_session):
    """
    AC-A01:
    Admins can access the admin dashboard.

    This sends a GET request to /admin/ using an authenticated admin session.
    Expected result: 200 OK.
    """
    response = client.get("/admin/")
    assert response.status_code == 200


def test_ac_a01_admin_can_access_highscore_management_page(client, admin_session):
    """
    AC-A01:
    Admins can access admin management pages.

    This sends a GET request to /admin/highscores.
    Expected result: 200 OK.
    """
    response = client.get("/admin/highscores")
    assert response.status_code == 200


def test_ac_a01_admin_can_access_riddle_management_page(client, admin_session):
    """
    AC-A01:
    Admins can access admin management pages.

    This sends a GET request to /admin/riddles.
    Expected result: 200 OK.
    """
    response = client.get("/admin/riddles")
    assert response.status_code == 200


def test_ac_a02_admin_can_edit_public_highscore(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A02:
    Admins can edit public highscores.

    This replaces the highscore storage functions with temporary test versions,
    sends an admin edit request, and checks that the highscore value changes.
    """
    import admin

    highscore_file = tmp_path / "-highscores.txt"

    def fake_load_highscores():
        return [{"username": "aaron", "score": 10}]

    def fake_save_highscores(highscores):
        with open(highscore_file, "w") as f:
            for entry in highscores:
                f.write(f"{entry['username']}\n")
                f.write(f"{entry['score']}\n")

    monkeypatch.setattr(admin, "load_highscores", fake_load_highscores)
    monkeypatch.setattr(admin, "save_highscores", fake_save_highscores)

    response = client.post("/admin/highscores/0", data={
        "action": "edit",
        "username": "aaron",
        "score": "99"
    })

    assert response.status_code in (302, 303)
    assert "99" in highscore_file.read_text()


def test_ac_a02_admin_can_delete_public_highscore(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A02:
    Admins can delete public highscores.

    This creates one temporary highscore entry, sends an admin delete request,
    and checks that the saved highscore file is empty afterwards.
    """
    import admin

    highscore_file = tmp_path / "-highscores.txt"

    def fake_load_highscores():
        return [{"username": "aaron", "score": 10}]

    def fake_save_highscores(highscores):
        with open(highscore_file, "w") as f:
            for entry in highscores:
                f.write(f"{entry['username']}\n")
                f.write(f"{entry['score']}\n")

    monkeypatch.setattr(admin, "load_highscores", fake_load_highscores)
    monkeypatch.setattr(admin, "save_highscores", fake_save_highscores)

    response = client.post("/admin/highscores/0", data={
        "action": "delete"
    })

    assert response.status_code in (302, 303)
    assert highscore_file.read_text() == ""


def test_ac_a03_admin_can_edit_stored_user_score_history(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A03:
    Admins can edit stored user score history records.

    This creates a temporary score-history file for user aaron, sends an admin
    edit request, and checks that the stored score changes from 10 to 50.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 10}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.post("/admin/scores/aaron/0/edit", data={
        "score": "50"
    })

    assert response.status_code in (302, 303)

    scores = json.loads(score_file.read_text())
    assert scores[0]["score"] == 50


def test_ac_a03_admin_can_delete_stored_user_score_history(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A03:
    Admins can delete stored user score history records.

    This creates two temporary stored scores, deletes the first score as admin,
    and checks that the remaining score is preserved and renumbered.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    score_file.write_text(json.dumps([
        {"score_id": 0, "score": 10},
        {"score_id": 1, "score": 20}
    ]))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.post("/admin/scores/aaron/0/delete")

    assert response.status_code in (302, 303)

    scores = json.loads(score_file.read_text())
    assert len(scores) == 1
    assert scores[0]["score"] == 20
    assert scores[0]["score_id"] == 0


def test_ac_a04_admin_can_edit_riddle_and_answer(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A04:
    Admins can edit riddles/answers.

    This replaces riddle storage with temporary files, sends an admin edit
    request, and checks that both the riddle and answer are updated.
    """
    import admin

    riddles_file = tmp_path / "-riddles.txt"
    answers_file = tmp_path / "-answers.txt"

    def fake_load_riddles_answers():
        return ["Old riddle"], ["Old answer"]

    def fake_save_riddles_answers(riddles, answers):
        riddles_file.write_text("\n".join(riddles))
        answers_file.write_text("\n".join(answers))

    monkeypatch.setattr(admin, "load_riddles_answers", fake_load_riddles_answers)
    monkeypatch.setattr(admin, "save_riddles_answers", fake_save_riddles_answers)

    response = client.post("/admin/riddles/0", data={
        "action": "edit",
        "riddle": "New riddle",
        "answer": "New answer"
    })

    assert response.status_code in (302, 303)
    assert "New riddle" in riddles_file.read_text()
    assert "New answer" in answers_file.read_text()


def test_ac_a04_admin_can_delete_riddle_and_answer(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A04:
    Admins can delete riddles/answers.

    This creates one temporary riddle/answer pair, sends an admin delete
    request, and checks that both storage files are empty afterwards.
    """
    import admin

    riddles_file = tmp_path / "-riddles.txt"
    answers_file = tmp_path / "-answers.txt"

    def fake_load_riddles_answers():
        return ["Riddle one"], ["Answer one"]

    def fake_save_riddles_answers(riddles, answers):
        riddles_file.write_text("\n".join(riddles))
        answers_file.write_text("\n".join(answers))

    monkeypatch.setattr(admin, "load_riddles_answers", fake_load_riddles_answers)
    monkeypatch.setattr(admin, "save_riddles_answers", fake_save_riddles_answers)

    response = client.post("/admin/riddles/0", data={
        "action": "delete"
    })

    assert response.status_code in (302, 303)
    assert riddles_file.read_text() == ""
    assert answers_file.read_text() == ""


def test_ac_a04_admin_can_add_riddle_and_answer(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A04:
    Admins can add riddles/answers.

    This starts with empty temporary riddle/answer storage, sends an admin add
    request, and checks that the new riddle and answer are saved.
    """
    import admin

    riddles_file = tmp_path / "-riddles.txt"
    answers_file = tmp_path / "-answers.txt"

    def fake_load_riddles_answers():
        return [], []

    def fake_save_riddles_answers(riddles, answers):
        riddles_file.write_text("\n".join(riddles))
        answers_file.write_text("\n".join(answers))

    monkeypatch.setattr(admin, "load_riddles_answers", fake_load_riddles_answers)
    monkeypatch.setattr(admin, "save_riddles_answers", fake_save_riddles_answers)

    response = client.post("/admin/riddles/add", data={
        "new_riddle": "What has keys but no locks?",
        "new_answer": "Piano"
    })

    assert response.status_code in (302, 303)
    assert "What has keys but no locks?" in riddles_file.read_text()
    assert "Piano" in answers_file.read_text()


def test_ac_a05_invalid_highscore_input_rejected_before_file_modified(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A05:
    Invalid admin input is rejected before files are modified.

    This sends a malicious/non-numeric highscore value. The request should be
    rejected with 400 and the temporary highscore file should remain unchanged.
    """
    import admin

    highscore_file = tmp_path / "-highscores.txt"
    original_content = "aaron\n10\n"
    highscore_file.write_text(original_content)

    def fake_load_highscores():
        return [{"username": "aaron", "score": 10}]

    def fake_save_highscores(highscores):
        with open(highscore_file, "w") as f:
            for entry in highscores:
                f.write(f"{entry['username']}\n")
                f.write(f"{entry['score']}\n")

    monkeypatch.setattr(admin, "load_highscores", fake_load_highscores)
    monkeypatch.setattr(admin, "save_highscores", fake_save_highscores)

    response = client.post("/admin/highscores/0", data={
        "action": "edit",
        "username": "aaron",
        "score": "<script>alert(1)</script>"
    })

    assert response.status_code == 400
    assert highscore_file.read_text() == original_content


def test_ac_a05_invalid_stored_score_input_rejected_before_file_modified(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A05:
    Invalid admin input is rejected before files are modified.

    This sends a malicious/non-numeric stored score value. The request should be
    rejected with 400 and the stored score-history file should remain unchanged.
    """
    import score_feature

    score_file = tmp_path / "aaron.json"
    original_scores = [{"score_id": 0, "score": 10}]
    score_file.write_text(json.dumps(original_scores))

    monkeypatch.setattr(score_feature, "score_history_path", lambda username: score_file)

    response = client.post("/admin/scores/aaron/0/edit", data={
        "score": "<script>alert(1)</script>" 
    })

    assert response.status_code == 400
    assert json.loads(score_file.read_text()) == original_scores


def test_ac_a05_invalid_riddle_input_rejected_before_file_modified(client, tmp_path, monkeypatch, admin_session):
    """
    AC-A05:
    Invalid admin input is rejected before files are modified.

    This sends an empty riddle value. The request should be rejected with 400,
    and the existing riddle/answer files should remain unchanged.
    """
    import admin

    riddles_file = tmp_path / "-riddles.txt"
    answers_file = tmp_path / "-answers.txt"
    riddles_file.write_text("Old riddle")
    answers_file.write_text("Old answer")

    def fake_load_riddles_answers():
        return ["Old riddle"], ["Old answer"]

    def fake_save_riddles_answers(riddles, answers):
        riddles_file.write_text("\n".join(riddles))
        answers_file.write_text("\n".join(answers))

    monkeypatch.setattr(admin, "load_riddles_answers", fake_load_riddles_answers)
    monkeypatch.setattr(admin, "save_riddles_answers", fake_save_riddles_answers)

    response = client.post("/admin/riddles/0", data={
        "action": "edit",
        "riddle": "",
        "answer": "New answer"
    })

    assert response.status_code == 400
    assert riddles_file.read_text() == "Old riddle"
    assert answers_file.read_text() == "Old answer"


def test_ac_a06_admin_state_changing_action_requires_csrf(app, client, admin_session):
    """
    AC-A06:
    Admin state-changing actions are CSRF protected.

    This temporarily enables CSRF protection for the app and sends a POST
    request without a CSRF token. The request should be rejected.

    Expected result:
    400 Bad Request.
    """
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post("/admin/highscores/0", data={
        "action": "delete"
    })
    assert response.status_code == 400
    app.config["WTF_CSRF_ENABLED"] = False
import pytest
from run import app, sanitise_colour, DEFAULT_COLOUR

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# AC-1 - Test 1 | Valid 6 digit hex-code must be accepted
def test_valid_six_digit_hex():
    assert sanitise_colour('#ffffff') == '#ffffff'


# AC-1 - Test 2 | Valid 3 digit hex-code must be accepted
def test_three_digit_hex():
    assert sanitise_colour('#111') == '#111'


# AC-2 - Test 1 | Sanitise CSS injection attempt
def test_CSS_rejection():
    assert sanitise_colour('#fff; background-image: url(xxx.com)') == DEFAULT_COLOUR


# AC-2 - Test 2 | Input not starting with '#' must be rejected
def test_hash_exists():
    assert sanitise_colour('ffffff') == DEFAULT_COLOUR


# AC-2 - Test 3 | Non-hex characters rejected
def test_hex_chars():
    assert sanitise_colour('/https') == DEFAULT_COLOUR


# AC-3 - Test 1 | Input exceeding max length must be rejected
def test_input_leng():
    assert sanitise_colour('#abcdefg') == DEFAULT_COLOUR


# AC-3 - Test 2 | Empty input restores default
def test_blank_input():
    assert sanitise_colour('') == DEFAULT_COLOUR


# AC-4 - Test 1 | Valid colour (POST) must be stored in session
def test_colour_storage(client):
    client.post('/settings/set_colour', data={'bg_colour': '#ffffff'})
    with client.session_transaction() as sess:
        assert sess['bg_colour'] == '#ffffff'


# AC-4 - Test 2 | Invalid colour (POST) must be stored as default in session
def test_invalid_storage(client):
    client.post('/settings/set_colour', data={'bg_colour': 'javascript:alert(1)'})
    with client.session_transaction() as sess:
        assert sess['bg_colour'] == DEFAULT_COLOUR


# AC-5 - Test 1 | No error details exposed to user
def test_set_colour_redirects(client):
    response = client.post('/settings/set_colour', data={'bg_colour': '#ffffff'})
    assert response.status_code in (301, 302)

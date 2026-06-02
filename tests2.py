import pytest
from run import app, sanitise_search

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# AC-1 - Test 1 | Valid alphanumeric search term
def test_valid():
    assert sanitise_search('test') == 'test'


# AC-1 - Test 2 | Must allow search term with cosmetic special characters
def test_special_char():
    assert sanitise_search('test_special') == 'test_special'


# AC-2 - Test 1 | Must reject "<>"
def test_special_reject():
    assert sanitise_search('<script>') == ''


# AC-2 - Test 2 | Must reject "/""
def test_special_reject2():
    assert sanitise_search('/https') == ''


# AC-2 - Test 3 | Must reject ":;"
def test_special_reject3():
    assert sanitise_search(':evil;') == ''


# AC-3 - Test 1 | Input exceeding max length must be rejected
def test_max_leng():
    assert sanitise_search('x' * 31) == ''

# AC-3 - Test 2 | Empty input returns nothing
def test_blank_input():
    assert sanitise_search('') == ''


# AC-4 - Test 1 | Search only returns searched query
def test_search_filters_correctly(client):
    response = client.get('/highscores?search=Greg')
    assert b'Greg' in response.data


# AC-4 - Test 2 | Search shows as No Results when username not existent 
def test_no_results_found(client):
    response = client.get('/highscores?search=non_existent_user')
    assert b'No results found' in response.data


# AC-5 - Test 1 | Error does not show error details
def test_invalid_search_no_error_exposed(client):
    response = client.get('/highscores?search=<script>alert(1)</script>')
    assert b'<script>' not in response.data




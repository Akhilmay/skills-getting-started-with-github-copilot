import copy
import pytest

from fastapi.testclient import TestClient

from src.app import app, activities


# a shared client for exercising the FastAPI application
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset the modulelevel `activities` dict to its original state before
    every test.  This keeps tests independent and allows the
    ArrangeActAssert structure to be followed cleanly.
    """
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


def test_root_redirect():
    # Arrange: nothing special (fixture has run)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    # Arrange: initial state from fixture

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_success():
    # Arrange
    activity = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        json={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert new_email in activities[activity]["participants"]
    assert f"Signed up {new_email} for {activity}" in response.json()["message"]


def test_signup_already_signed():
    # Arrange
    activity = "Chess Club"
    existing = activities[activity]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        json={"email": existing},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_activity_not_found():
    # Arrange
    bogus = "NonExistent"

    # Act
    response = client.post(
        f"/activities/{bogus}/signup",
        json={"email": "whatever@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_success():
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]

    # Act
    response = client.request(
        "DELETE",
        f"/activities/{activity}/unregister",
        json={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]
    assert f"Unregistered {email} from {activity}" in response.json()["message"]


def test_unregister_not_signed():
    # Arrange
    activity = "Chess Club"
    email = "notjoined@mergington.edu"

    # Act
    response = client.request(
        "DELETE",
        f"/activities/{activity}/unregister",
        json={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_activity_not_found():
    # Arrange
    bogus = "GhostClub"

    # Act
    response = client.request(
        "DELETE",
        f"/activities/{bogus}/unregister",
        json={"email": "anyone@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

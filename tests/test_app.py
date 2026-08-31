from urllib.parse import quote

from src.app import activities


def test_root_redirects_to_static_index(client):
    # Arrange
    # (no setup needed, root route is static)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_known_activities(client):
    # Arrange
    # (activities dict is seeded by the app module)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert "Chess Club" in body
    chess_club = body["Chess Club"]
    assert set(chess_club.keys()) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }


def test_signup_adds_new_participant(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in activities[activity_name]["participants"]


def test_signup_duplicate_participant_is_rejected(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"
    participants_before = list(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities[activity_name]["participants"] == participants_before


def test_signup_unknown_activity_returns_404(client):
    # Arrange
    activity_name = "Underwater Basket Weaving"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_missing_email_returns_422(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup")

    # Assert
    assert response.status_code == 422


def test_signup_at_full_capacity_still_succeeds(client):
    # Arrange
    # Documents current app behavior: there is no capacity check on signup,
    # so filling an activity to max_participants does not block further signups.
    activity_name = "Chess Club"
    activity = activities[activity_name]
    max_participants = activity["max_participants"]
    while len(activity["participants"]) < max_participants:
        activity["participants"].append(f"filler{len(activity['participants'])}@mergington.edu")
    overflow_email = "overflow@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": overflow_email},
    )

    # Assert
    assert response.status_code == 200
    assert overflow_email in activity["participants"]
    assert len(activity["participants"]) == max_participants + 1


def test_signup_activity_name_with_special_characters(client):
    # Arrange
    activity_name = "Chess Club"  # contains a space, needs URL-encoding
    email = "special@mergington.edu"
    encoded_name = quote(activity_name)

    # Act
    response = client.post(
        f"/activities/{encoded_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]

import client


def test_sign_up():
    response = client.post(
        "/auth",
        json={
            "username": "harry",
            "email": "harry.tech2026@gmail.com",
            "password": "123456",
        },
    )
    assert response.status_code == 200
    assert response.json()["username"] == "harry"

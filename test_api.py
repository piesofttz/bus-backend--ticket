"""
Quick API smoke test for bus_backend.

Usage:
  1. Start the server: python manage.py runserver
  2. Run: python test_api.py

Notes:
  - Uses JWT auth (Authorization: Bearer <access_token>).
  - Attempts login with TEST_PHONE; if not registered it will register.
  - Verifies key public/authenticated endpoints including route detail by ID.
"""

import requests

BASE = "http://127.0.0.1:8000"
AUTH = f"{BASE}/api/auth"

# 9 digits after +255
TEST_PHONE = "699000001"


def _print(name, resp):
    print(f"\n{'=' * 60}\n{name}\nStatus: {resp.status_code}")
    try:
        data = resp.json()
        print("Response:", data)
        return data
    except Exception:
        print("Response: <non-json>", resp.text[:200])
        return None


def main():
    session = requests.Session()

    # Login or register
    resp = session.post(f"{AUTH}/login/", json={"phone_number": TEST_PHONE})
    if resp.status_code != 200:
        _print("REGISTER (auto)", session.post(f"{AUTH}/register/", json={
            "phone_number": TEST_PHONE,
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
        }))
        resp = session.post(f"{AUTH}/login/", json={"phone_number": TEST_PHONE})

    login_data = _print("LOGIN", resp)
    if not login_data or "access_token" not in login_data:
        print("Login failed; cannot continue.")
        return

    headers = {"Authorization": f"Bearer {login_data['access_token']}"}

    _print("CURRENT USER", session.get(f"{AUTH}/user/", headers=headers))

    routes_data = _print("LIST ROUTES", session.get(f"{AUTH}/routes/", headers=headers))
    route_id = None
    if isinstance(routes_data, list) and routes_data:
        route_id = routes_data[0].get("id")

    if route_id:
        _print(f"ROUTE DETAIL (id={route_id})", session.get(f"{AUTH}/routes/{route_id}/", headers=headers))
        _print(f"BUSES FOR ROUTE (route_id={route_id})", session.get(f"{AUTH}/routes/{route_id}/buses/", headers=headers))

    _print("ALL BUSES", session.get(f"{AUTH}/buses/", headers=headers))
    _print("MY BOOKINGS", session.get(f"{AUTH}/bookings/", headers=headers))

    print("\nSmoke test completed.")


if __name__ == "__main__":
    main()

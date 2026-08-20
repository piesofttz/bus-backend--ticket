import requests

BASE = "http://localhost:8000/api/auth"
session = requests.Session()


def test(name, resp):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"  Status: {resp.status_code}")
    try:
        print(f"  Response: {resp.json()}")
    except Exception:
        print(f"  Response: [PDF binary - {len(resp.content)} bytes]")
    print(f"{'='*50}")
    return resp


# 1. Register
test("1. REGISTER", session.post(f"{BASE}/register/", json={
    "username": "testuser",
    "password": "test1234",
    "email": "test@mail.com",
    "first_name": "John",
    "last_name": "Doe",
}))

# 2. Login
test("2. LOGIN", session.post(f"{BASE}/login/", json={
    "username": "testuser",
    "password": "test1234",
}))

# 3. Get User
test("3. GET USER", session.get(f"{BASE}/user/"))

# 4. Book Ticket
resp = test("4. BOOK TICKET", session.post(f"{BASE}/tickets/", json={
    "full_name": "John Doe",
    "phone_number": "0712345678",
    "route": "dar_to_mwanza",
    "seat_number": "12A",
    "travel_date": "2026-08-25",
}))

# 5. List Tickets
test("5. LIST TICKETS", session.get(f"{BASE}/tickets/"))

# 6. Get Ticket Detail
test("6. TICKET DETAIL", session.get(f"{BASE}/tickets/1/"))

# 7. Download PDF Receipt
pdf = test("7. PDF RECEIPT", session.get(f"{BASE}/tickets/1/receipt/"))
if pdf.status_code == 200 and len(pdf.content) > 100:
    with open("receipt.pdf", "wb") as f:
        f.write(pdf.content)
    print("  >> receipt.pdf saved!")

# 8. Delete Ticket
test("8. DELETE TICKET", session.delete(f"{BASE}/tickets/1/"))

# 9. Logout
test("9. LOGOUT", session.post(f"{BASE}/logout/"))

# API Testing Guide - Event Management API

**Base URL:** http://localhost:8001

---

## Browser-Accessible Endpoints (GET)

These can be opened directly in your browser:

### 1. List All Events (Public)
**Link:** http://localhost:8001/events/

Click to view all events in JSON format. No authentication needed.

---

## Command-Line Testing (curl)

Copy and paste these commands in your terminal to test each endpoint:

### User Registration

```bash
# Register a new user
curl -X POST http://localhost:8001/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123"
  }' | python -m json.tool
```

**Expected Response:** User object + JWT tokens (access & refresh)

---

### User Login

```bash
# Login with existing credentials
curl -X POST http://localhost:8001/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }' | python -m json.tool
```

**Expected Response:** User object + JWT tokens

---

### Create Event (Requires Authentication)

**Step 1:** Save your access token to a variable:
```bash
TOKEN=$(curl -s -X POST http://localhost:8001/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "password123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])")
```

**Step 2:** Create an event:
```bash
curl -X POST http://localhost:8001/events/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Django Meetup Nairobi",
    "description": "Learn Django REST Framework",
    "location": "iHub, Nairobi",
    "date": "2026-06-15T14:00:00Z",
    "max_attendees": 30
  }' | python -m json.tool
```

**Expected Response:** Complete event object with ID

---

### Get Single Event

```bash
# Replace {id} with actual event ID
curl http://localhost:8001/events/1/ | python -m json.tool
```

---

### Update Event (Organizer Only)

```bash
# You must be the organizer (creator) of the event
curl -X PUT http://localhost:8001/events/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Django Meetup Nairobi - UPDATED",
    "description": "Learn Django REST Framework - Now with workshops!",
    "location": "iHub, Nairobi",
    "date": "2026-06-15T14:00:00Z",
    "max_attendees": 50
  }' | python -m json.tool
```

---

### Register for Event

```bash
# Register authenticated user for an event
curl -X POST http://localhost:8001/events/1/register/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Expected Response:** Success message + registration details

---

### Delete Event (Organizer Only)

```bash
# Only the organizer can delete
curl -X DELETE http://localhost:8001/events/1/ \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

### Token Refresh

```bash
# First save your refresh token
REFRESH_TOKEN=$(curl -s -X POST http://localhost:8001/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "password123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['tokens']['refresh'])")

# Get new access token
curl -X POST http://localhost:8001/token/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH_TOKEN\"}" | python -m json.tool
```

---

## Complete Testing Flow

Run these commands in sequence to test the entire workflow:

```bash
# 1. Register first user
echo "=== Registering User 1 ==="
curl -s -X POST http://localhost:8001/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "password": "pass123"}' \
  | python -m json.tool

# 2. Register second user
echo -e "\n=== Registering User 2 ==="
curl -s -X POST http://localhost:8001/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@example.com", "password": "pass456"}' \
  | python -m json.tool

# 3. Alice logs in and gets token
echo -e "\n=== Alice Logging In ==="
ALICE_TOKEN=$(curl -s -X POST http://localhost:8001/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "pass123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])")
echo "Alice's token: ${ALICE_TOKEN:0:50}..."

# 4. Alice creates an event
echo -e "\n=== Alice Creates Event ==="
curl -s -X POST http://localhost:8001/events/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -d '{
    "title": "Python Workshop",
    "description": "Learn Python basics",
    "location": "Tech Hub",
    "date": "2026-07-01T10:00:00Z",
    "max_attendees": 20
  }' | python -m json.tool

# 5. Bob logs in
echo -e "\n=== Bob Logging In ==="
BOB_TOKEN=$(curl -s -X POST http://localhost:8001/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "bob@example.com", "password": "pass456"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])")
echo "Bob's token: ${BOB_TOKEN:0:50}..."

# 6. Bob registers for the event
echo -e "\n=== Bob Registers for Event ==="
curl -s -X POST http://localhost:8001/events/1/register/ \
  -H "Authorization: Bearer $BOB_TOKEN" | python -m json.tool

# 7. View all events (public)
echo -e "\n=== All Events (Public) ==="
curl -s http://localhost:8001/events/ | python -m json.tool

# 8. Bob tries to update Alice's event (should fail)
echo -e "\n=== Bob Tries to Update Alice's Event (Should Fail) ==="
curl -s -X PUT http://localhost:8001/events/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -d '{
    "title": "HACKED",
    "description": "Should not work",
    "location": "Tech Hub",
    "date": "2026-07-01T10:00:00Z"
  }' | python -m json.tool

# 9. Alice updates her own event (should succeed)
echo -e "\n=== Alice Updates Her Own Event ==="
curl -s -X PUT http://localhost:8001/events/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -d '{
    "title": "Python Workshop - UPDATED",
    "description": "Learn Python basics with hands-on coding",
    "location": "Tech Hub",
    "date": "2026-07-01T10:00:00Z",
    "max_attendees": 25
  }' | python -m json.tool

echo -e "\n=== Testing Complete ==="
```

---

## Using Postman / Thunder Client

If you prefer a GUI tool:

### Postman Setup

1. **Import Collection:**
   - Create new request for each endpoint
   - Set method (GET, POST, PUT, DELETE)
   - Set URL: http://localhost:8001/...
   - Add headers: `Content-Type: application/json`
   - For protected endpoints, add: `Authorization: Bearer <token>`

2. **Environment Variables:**
   - Create variable `base_url` = http://localhost:8001
   - Create variable `token` to store JWT token

### Thunder Client (VS Code Extension)

1. Install Thunder Client extension in VS Code
2. Create new request
3. Set method and URL
4. Add JSON body for POST/PUT requests
5. Save token from login response and use in subsequent requests

---

## Error Testing

### Test Validation Errors

```bash
# Missing required field
curl -X POST http://localhost:8001/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}' | python -m json.tool

# Invalid email format
curl -X POST http://localhost:8001/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email": "notanemail", "password": "pass123"}' | python -m json.tool

# Past date for event
TOKEN=$(curl -s -X POST http://localhost:8001/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "pass123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])")

curl -X POST http://localhost:8001/events/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Past Event",
    "description": "Should fail",
    "location": "Test",
    "date": "2020-01-01T10:00:00Z"
  }' | python -m json.tool
```

---

## Quick Reference

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/users/register/` | POST | No | Create account |
| `/users/login/` | POST | No | Login |
| `/token/refresh/` | POST | No | Refresh token |
| `/events/` | GET | No | List events |
| `/events/` | POST | Yes | Create event |
| `/events/{id}/` | GET | No | Get event |
| `/events/{id}/` | PUT | Yes (Organizer) | Update event |
| `/events/{id}/` | DELETE | Yes (Organizer) | Delete event |
| `/events/{id}/register/` | POST | Yes | Register for event |

---

## Tips

1. **Save tokens:** Always save access tokens after login/register to use in subsequent requests
2. **Token expiry:** Access tokens expire after 1 hour. Use refresh endpoint to get new one
3. **JSON formatting:** Pipe curl output to `python -m json.tool` for readable JSON
4. **Debugging:** Add `-v` flag to curl for verbose output: `curl -v ...`
5. **Headers:** Always include `Content-Type: application/json` for POST/PUT requests

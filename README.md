# Library Management System API

A full-featured backend REST API for managing a library — built with Django, Django REST Framework, JWT authentication, and PostgreSQL. All data is returned in JSON format for easy frontend consumption.

---

## Tech Stack

- Python 3.13
- Django 6.0.3
- Django REST Framework
- SimpleJWT (JWT authentication)
- **Cookie-based Auth** (HTTP-only cookies for enhanced security)
- PostgreSQL 18
- django-cors-headers
- python-decouple (environment variable management)

---

## Project Structure

```
LIBRARY MANAGEMENT SYSTEM/
├── .env                               # Secret credentials (never pushed to GitHub)
├── .gitignore                         # Files excluded from GitHub
├── manage.py                          # Django management entry point
├── requirements.txt                   # All installed Python packages
├── README.md                          # This file
│
├── library_management_system/         # Main Django project folder
│   ├── settings.py                    # All Django settings and configurations
│   ├── urls.py                        # Root URL router
│   ├── permissions.py                 # Custom role-based permission classes
│   ├── utils.py                       # success_response and error_response helpers
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                          # User auth, roles, membership
│   ├── models.py                      # Custom User model with roles
│   ├── serializers.py                 # Register, Login, User, ChangePassword serializers
│   ├── views.py                       # Auth views
│   └── urls.py
│
├── books/                             # Book catalogue, authors, categories
│   ├── models.py                      # Author, Category, Book models
│   ├── permissions.py                 # IsAdminOrLibrarian permission
│   ├── serializers.py                 # Book, Author, Category serializers
│   ├── views.py                       # Book CRUD with search and filter
│   └── urls.py
│
└── borrowing/                         # Borrow records, fines, reservations, reports
    ├── models.py                      # BorrowRecord, Fine, Reservation models
    ├── serializers.py                 # Borrow, Fine, Reservation serializers
    ├── views.py                       # All borrowing operations and reports
    └── urls.py
```

---

## Features Implemented

### Accounts App

- Custom User model with roles: `admin`, `librarian`, `member`
- **Cookie-based JWT authentication** (HTTP-only, Secure, SameSite=Lax)
- Tokens stored in browser cookies for automatic session handling
- Login with either **username or email** + password
- Secure **Logout** with token revocation in DB
- User profile view and update
- Change password with old password verification
- Admin can list all members with pagination
- Admin can suspend and activate member accounts
- Membership expiry tracking

### Books App

- Full CRUD for Books, Authors, Categories
- Search books by title, author name, or ISBN
- Filter by category and availability
- Paginated results (10 per page)
- Role-based access: public GET, librarian/admin POST/PATCH, admin DELETE
- Blocks deletion of books that have active borrow records
- Blocks deletion of authors that have associated books

### Borrowing App

- Issue books to members with 4-step validation
- Auto-decrement and increment available_copies on issue and return
- Auto-calculate fines on late returns ($0.50 per overdue day)
- Renew borrow period (once per record, 14 extra days)
- Reservation queue for unavailable books
- Mark fines as paid (librarian) or waive entirely (admin)
- Full borrow history with filters
- Overdue book detection and tracking

### Reports

- Dashboard summary (total books, members, active borrows, unpaid fines)
- Most popular books by borrow count (public)
- Overdue members report with days overdue and fine amounts

---

## User Roles & Permissions

| Action | Member | Librarian | Admin |
|---|---|---|---|
| Browse and search books | ✅ | ✅ | ✅ |
| Add / edit books | ❌ | ✅ | ✅ |
| Delete books | ❌ | ❌ | ✅ |
| Issue / return books | ❌ | ✅ | ✅ |
| Renew borrow period | ✅ | ✅ | ✅ |
| Make reservations | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| View own borrow history | ✅ | ✅ | ✅ |
| View any member's history | ❌ | ✅ | ✅ |
| View all members | ❌ | ❌ | ✅ |
| Suspend members | ❌ | ❌ | ✅ |
| Mark fines as paid | ❌ | ✅ | ✅ |
| Waive fines | ❌ | ❌ | ✅ |
| View reports and dashboard | ❌ | ❌ | ✅ |
| View popular books | ✅ | ✅ | ✅ |

---

## API Endpoints

### Authentication

```
POST   /api/auth/register/           Register new member account
POST   /api/auth/login/              Login (tokens sent in HTTP-only cookies)
POST   /api/auth/logout/             Logout (revokes token and clears cookies)
POST   /api/auth/refresh/            Refresh access token using refresh cookie
GET    /api/auth/profile/            View own profile
PATCH  /api/auth/profile/            Update own profile
POST   /api/auth/change-password/    Change own password
```

### Member Management

```
GET    /api/members/                 List all members (admin only)
POST   /api/members/<id>/suspend/    Suspend a member (admin only)
POST   /api/members/<id>/activate/   Activate a member (admin only)
```

### Books

```
GET    /api/books/                   List all books — public, supports search and filter
POST   /api/books/                   Add a book (librarian/admin)
GET    /api/books/<id>/              Book detail (public)
PATCH  /api/books/<id>/              Update book (librarian/admin)
DELETE /api/books/<id>/              Delete book (admin only)
GET    /api/authors/                 List authors (public)
POST   /api/authors/                 Add author (librarian/admin)
GET    /api/authors/<id>/            Author detail (public)
PATCH  /api/authors/<id>/            Update author (librarian/admin)
DELETE /api/authors/<id>/            Delete author (admin only)
GET    /api/categories/              List categories (public)
POST   /api/categories/              Add category (librarian/admin)
```

**Book search and filter query params:**

```
GET /api/books/?search=harry           Search by title, author, or ISBN
GET /api/books/?category=1             Filter by category ID
GET /api/books/?available=true         Show only available books
GET /api/books/?search=harry&page=2    Combine search with pagination
```

### Borrowing

```
POST   /api/borrow/issue/             Issue book to member (librarian/admin)
POST   /api/borrow/return/            Return a book (librarian/admin)
POST   /api/borrow/renew/             Renew borrow period
GET    /api/borrow/history/           Borrow history (own for member, any for librarian/admin)
GET    /api/borrow/overdue/           All overdue records (librarian/admin)
```

### Reservations

```
GET    /api/reservations/             View reservations (own for member, all for librarian/admin)
POST   /api/reservations/             Reserve an unavailable book (member)
DELETE /api/reservations/<id>/cancel/ Cancel a reservation
```

### Fines

```
GET    /api/fines/                    View fines (own for member, all for librarian/admin)
GET    /api/fines/?is_paid=false      Filter unpaid fines
POST   /api/fines/<id>/pay/           Mark fine as paid (librarian/admin)
POST   /api/fines/<id>/waive/         Waive fine completely (admin only)
```

### Reports

```
GET    /api/reports/summary/          Dashboard summary (admin only)
GET    /api/reports/popular-books/    Most borrowed books (public)
GET    /api/reports/overdue-members/  Members with overdue books (admin only)
```

---

## JSON Response Format

Every single endpoint returns this consistent structure:

**Success (Login):**

```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "user": {
            "id": 1,
            "username": "ahmad_member",
            "email": "ahmad@test.com",
            "role": "member",
            "is_suspended": false
        }
    }
}
```

> [!NOTE]
> For security, the `access_token` and `refresh_token` are now returned in **HTTP-only cookies**, not in the response body.

**Success (List endpoints):**

```json
{
    "success": true,
    "message": "Books retrieved successfully",
    "data": [ ... ],
    "pagination": {
        "count": 50,
        "next": "/api/books/?page=2",
        "previous": null,
        "current_page": 1,
        "total_pages": 5
    }
}
```

**Error:**

```json
{
    "success": false,
    "message": "Cannot issue book",
    "errors": {
        "member": ["This member is suspended"]
    }
}
```

The `pagination` key only appears on list endpoints. The `errors` key only appears on error responses.

---

## Local Setup Guide

### Prerequisites

- Python 3.10+
- PostgreSQL installed and running
- pgAdmin (optional, for visual DB management)
- Git

### Step 1 — Clone the repository

```bash
git clone https://github.com/Ahmed-Nawaz-11/library-management-system.git
cd library-management-system
```

### Step 2 — Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Create the PostgreSQL database

Open pgAdmin and create a database named `library_db`. Or run in psql:

```sql
CREATE DATABASE library_db;
```

### Step 5 — Create .env file

Create a `.env` file in the root directory (same level as manage.py):

```
SECRET_KEY=your-secret-key-here
DB_NAME=library_db
DB_USER=postgres
DB_PASSWORD=your-postgres-password
DB_HOST=127.0.0.1
DB_PORT=5432
```

### Step 6 — Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 7 — Create user accounts

```bash
python manage.py shell
```

```python
from accounts.models import User

# Create admin
admin = User.objects.create_user(
    username="admin_user",
    email="admin@library.com",
    password="Admin@1234"
)
admin.role = "admin"
admin.is_staff = True
admin.is_superuser = True
admin.save()

# Create librarian
librarian = User.objects.create_user(
    username="librarian1",
    email="lib@library.com",
    password="Lib@1234"
)
librarian.role = "librarian"
librarian.save()

exit()
```

### Step 8 — Run the server

```bash
python manage.py runserver
```

API is now live at `http://127.0.0.1:8000/`

---

## Testing with Postman

**Step 1 — Register a member:**

POST `/api/auth/register/`

```json
{
    "username": "ahmad_member",
    "email": "ahmad@test.com",
    "password": "Test@1234",
    "phone": "03001234567"
}
```

**Step 2 — Login with username or email (both work):**

POST `/api/auth/login/`

```json
{
    "username": "ahmad_member",
    "password": "Test@1234"
}
```

The server will set `access_token` and `refresh_token` as cookies.

**Step 3 — Use token for protected routes:**

- **In Browsers:** Cookies are sent automatically.
- **In Postman:**
    - Cookies are automatically captured and sent if you use the desktop client.
    - Alternatively, you can still use the **Authorization** tab → **Bearer Token** if you have a manual token, as the API supports a fallback to headers for development.

**Step 4 — Test Logout:**

POST `/api/auth/logout/` (Clears cookies and revokes session in DB).

**Step 5 — Test public book endpoint (no token needed):**

GET `/api/books/`

### Importable Postman Collection

We have generated a complete, ready-to-use Postman Collection containing all 9 API folders, fully configured for HTTP-only cookie authentication.

1. Navigate to the `docs/` folder in the project.
2. Import `LibraryManagementSystem.postman_collection.json` into Postman.
3. Once imported, you simply hit the `Login` endpoint with valid credentials.
4. Postman's Cookie Jar will automatically save the secure cookies and attach them to all subsequent protected requests!

---

## Database Models

### accounts.User

| Field | Type | Notes |
|---|---|---|
| username | CharField | unique |
| email | EmailField | unique |
| phone | CharField | optional |
| role | CharField | admin / librarian / member |
| membership_expiry | DateField | null allowed |
| is_suspended | BooleanField | default False |

### accounts.UserRefreshToken

| Field | Type | Notes |
|---|---|---|
| user | FK → User | |
| token | TextField | The actual refresh token string |
| created_at | DateTimeField | auto |
| expires_at | DateTimeField | when session expires |
| is_revoked | BooleanField | used for logout |

### books.Author

| Field | Type | Notes |
|---|---|---|
| name | CharField | |
| bio | TextField | optional |
| nationality | CharField | optional |

### books.Category

| Field | Type | Notes |
|---|---|---|
| name | CharField | unique |

### books.Book

| Field | Type | Notes |
|---|---|---|
| title | CharField | |
| isbn | CharField | unique |
| author | FK → Author | |
| category | FK → Category | |
| publisher | CharField | |
| publish_year | IntegerField | |
| total_copies | IntegerField | |
| available_copies | IntegerField | managed by system, read-only |
| cover_image | URLField | optional |
| created_at | DateTimeField | auto |

### borrowing.BorrowRecord

| Field | Type | Notes |
|---|---|---|
| member | FK → User | |
| book | FK → Book | |
| borrow_date | DateField | auto today |
| due_date | DateField | borrow + 14 days |
| return_date | DateField | null until returned |
| status | CharField | borrowed / returned / overdue |
| renewed | BooleanField | default False |

### borrowing.Fine

| Field | Type | Notes |
|---|---|---|
| borrow_record | OneToOne → BorrowRecord | |
| amount | DecimalField | overdue days x $0.50 |
| is_paid | BooleanField | default False |
| is_waived | BooleanField | default False |

### borrowing.Reservation

| Field | Type | Notes |
|---|---|---|
| member | FK → User | |
| book | FK → Book | |
| reserved_at | DateTimeField | auto |
| is_active | BooleanField | default True |
| expires_at | DateField | set when book becomes available |

---

## Security

- All sensitive credentials stored in `.env` file and never pushed to GitHub
- **Cookie-based Security**: Tokens are stored in HTTP-only, SameSite=Lax cookies to prevent XSS and CSRF.
- **Refresh Token Rotation & Revocation**: Refresh tokens are stored in the database and revoked on logout.
- JWT access tokens expire in 60 minutes
- JWT refresh tokens expire in 7 days
- Every endpoint has a specific permission class
- Wrong role returns `403 Forbidden`
- No token returns `401 Unauthorized`
- CORS configured with `ALLOW_CREDENTIALS=True` for secure cross-origin cookie handling

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT License — free to use and modify.

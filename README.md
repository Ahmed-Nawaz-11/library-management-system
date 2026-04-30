# Library Management System API

A full-featured backend REST API for managing a library — built with Django, Django REST Framework, JWT authentication, and PostgreSQL.

---

## Tech Stack

- Python 3.13
- Django 6.0.3
- Django REST Framework
- SimpleJWT (JWT authentication)
- PostgreSQL
- django-cors-headers

---

## Project Structure

```
LIBRARY MANAGEMENT SYSTEM/
├── library_management_system/    # Main Django project folder
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                     # User auth, roles, membership
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── books/                        # Book catalogue, authors, categories
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── borrowing/                    # Borrow records, fines, reservations
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── manage.py
└── requirements.txt
```

---

## Features Implemented

### Accounts App

- Custom User model with roles: `admin`, `librarian`, `member`
- JWT-based registration and login
- User profile view and update
- Change password
- Admin can list all members
- Admin can suspend / activate members
- Membership expiry tracking

### Books App

- Full CRUD for Books, Authors, Categories
- Search books by title, author, ISBN
- Filter by category and availability
- Paginated results (10 per page)
- Role-based access: public GET, librarian/admin POST/PATCH, admin DELETE
- Blocks deletion of books with active borrow records

### Borrowing App (Core Logic Ready)

- `BorrowRecord` — tracks every book issue and return
- `Fine` — auto-calculated on late returns
- `Reservation` — queue system for unavailable books
- **APIs**: Issue and Return functionalities are fully implemented with fines & reservations integrations.

---

## User Roles & Permissions

| Action | Member | Librarian | Admin |
|---|---|---|---|
| Browse books | ✅ | ✅ | ✅ |
| Add / edit books | ❌ | ✅ | ✅ |
| Delete books | ❌ | ❌ | ✅ |
| Issue / return books | ❌ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| View all members | ❌ | ❌ | ✅ |
| Suspend members | ❌ | ❌ | ✅ |
| Waive fines | ❌ | ❌ | ✅ |
| View reports | ❌ | ✅ | ✅ |

---

## API Endpoints

### Auth & Members

```
POST   /api/auth/register/           Register new member
POST   /api/auth/login/              Login and get JWT tokens
POST   /api/auth/refresh/            Refresh access token
GET    /api/auth/profile/            View own profile
PATCH  /api/auth/profile/            Update own profile
POST   /api/auth/change-password/    Change own password
GET    /api/members/                 List all members (admin only)
POST   /api/members/<id>/suspend/    Suspend a member (admin only)
POST   /api/members/<id>/activate/   Activate a member (admin only)
```

### Books

```
GET    /api/books/                   List all books (public, supports search & filter)
POST   /api/books/                   Add a book (librarian/admin)
GET    /api/books/<id>/              Book detail (public)
PATCH  /api/books/<id>/              Update book (librarian/admin)
DELETE /api/books/<id>/              Delete book (admin only)
GET    /api/authors/                 List authors (public)
POST   /api/authors/                 Add author (librarian/admin)
GET    /api/categories/              List categories (public)
POST   /api/categories/              Add category (librarian/admin)
```

### Borrowing

**Implemented:**
```
POST   /api/borrow/issue/            Issue book to member (librarian/admin)
POST   /api/borrow/return/           Return a book (librarian/admin)
```

**Coming soon:**
```
POST   /api/borrow/renew/            Renew borrow period (librarian/admin)
GET    /api/borrow/history/          Borrow history
GET    /api/borrow/overdue/          All overdue records (librarian/admin)
GET    /api/reservations/            List reservations
POST   /api/reservations/            Reserve a book (member)
GET    /api/fines/                   List fines
POST   /api/fines/<id>/pay/          Mark fine as paid (librarian/admin)
POST   /api/fines/<id>/waive/        Waive fine (admin only)
GET    /api/reports/summary/         Dashboard summary (admin)
GET    /api/reports/popular-books/   Most borrowed books (admin)
```

---

## JSON Response Format

Every endpoint returns this consistent structure:

**Success:**

```json
{
    "success": true,
    "message": "User registered successfully",
    "data": { ... },
    "pagination": {
        "count": 100,
        "next": "/api/books/?page=2",
        "previous": null,
        "current_page": 1,
        "total_pages": 10
    }
}
```

**Error:**

```json
{
    "success": false,
    "message": "Registration failed",
    "errors": {
        "username": ["This field is required."]
    }
}
```

---

## Local Setup Guide

### Prerequisites

- Python 3.10+
- PostgreSQL installed and running
- pgAdmin (optional, for visual DB management)

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/library-management-system.git
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

Open pgAdmin or psql and run:

```sql
CREATE DATABASE library_db;
```

### Step 5 — Configure environment variables

Create a `.env` file in the root directory:

```
SECRET_KEY=your-secret-key-here
DB_NAME=library_db
DB_USER=postgres
DB_PASSWORD=your-postgres-password
DB_HOST=127.0.0.1
DB_PORT=5432
```

> Note: Update `settings.py` to read from `.env` using `python-decouple` or `python-dotenv` if needed. For now you can directly update the `DATABASES` and `SECRET_KEY` values in `settings.py`.

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
admin = User.objects.create_user(username="admin_user", email="admin@library.com", password="Admin@1234")
admin.role = "admin"
admin.is_staff = True
admin.is_superuser = True
admin.save()

# Create librarian
librarian = User.objects.create_user(username="librarian1", email="lib@library.com", password="Lib@1234")
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

Import the collection or manually test endpoints:

1. Register: `POST /api/auth/register/`
2. Login: `POST /api/auth/login/` — copy the `access` token
3. Set Authorization → Bearer Token in Postman for protected routes
4. Test books: `GET /api/books/` (public, no token needed)

---

## Database Models

### accounts.User

| Field | Type | Notes |
|---|---|---|
| username | CharField | unique |
| email | EmailField | |
| phone | CharField | |
| role | CharField | admin / librarian / member |
| membership_expiry | DateField | null allowed |
| is_suspended | BooleanField | default False |

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
| available_copies | IntegerField | |
| cover_image | URLField | optional |

### borrowing.BorrowRecord

| Field | Type | Notes |
|---|---|---|
| member | FK → User | |
| book | FK → Book | |
| borrow_date | DateField | auto today |
| due_date | DateField | borrow + 14 days |
| return_date | DateField | null until returned |
| status | CharField | borrowed / returned / overdue |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT License — free to use and modify.

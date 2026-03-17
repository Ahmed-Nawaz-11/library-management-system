# Library Management REST API (Django + DRF)

## Objective

Build a REST API for a **Library Management System** using **Django and Django REST Framework**.

The goal is to practice:

* Django models
* Serializers
* API Views / ViewSets
* Authentication
* Business logic
* Database relationships

---

# Core Requirements

## 1. Author Management

Create a model for **Authors**.

### Fields

* id
* name
* email
* bio
* created_at

### Required APIs

```
POST   /api/authors/
GET    /api/authors/
GET    /api/authors/{id}/
PUT    /api/authors/{id}/
DELETE /api/authors/{id}/
```

---

# 2. Book Management

Create a model for **Books**.

### Fields

* id
* title
* isbn
* published_date
* author (ForeignKey → Author)
* total_copies
* available_copies

### Required APIs

```
POST   /api/books/
GET    /api/books/
GET    /api/books/{id}/
PUT    /api/books/{id}/
DELETE /api/books/{id}/
```

### Additional Features

#### Filter books by author

Example:

```
GET /api/books/?author=1
```

#### Search books by title

Example:

```
GET /api/books/?search=python
```

---

# 3. Borrow Book System

Create a **Borrow model**.

### Fields

* id
* user_name
* book
* borrow_date
* return_date
* status (borrowed / returned)

### Required APIs

```
POST   /api/borrow/
GET    /api/borrow/
GET    /api/borrow/{id}/
PUT    /api/borrow/{id}/
```

### Business Logic

When a book is **borrowed**

```
available_copies = available_copies - 1
```

When a book is **returned**

```
available_copies = available_copies + 1
```

Borrowing should only be allowed if:

```
available_copies > 0
```

---

# Authentication

Implement **JWT Authentication** using:

```
djangorestframework-simplejwt
```

### Required Endpoints

```
POST /api/token/
POST /api/token/refresh/
```

### Protected APIs

The following APIs must require authentication:

* Create Book
* Update Book
* Delete Book
* Borrow Book

---

# Additional Requirements

## 1. Validation

Borrowing a book should only be possible when **copies are available**.

---

## 2. Custom API

Create an endpoint that returns only **available books**.

```
GET /api/books/available/
```

---

# API Response Format

All APIs should return responses in the following structure:

```json
{
  "status": true,
  "message": "Request successful",
  "data": {}
}
```

---

# Suggested Project Structure

```
library_project/

├── authors/
├── books/
├── borrow/
├── users/

├── manage.py
└── library_project/
```

---

# Submission Requirements

The project must include:

* Django project setup
* Proper models
* Serializers
* API Views or ViewSets
* JWT authentication
* Database migrations
* Proper folder structure

---

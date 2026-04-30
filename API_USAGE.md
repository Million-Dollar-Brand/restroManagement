# API Usage Guide

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

### Get Access Token

**POST** `/auth/login`

Form data:
```
username: your_username
password: your_password
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Register New User

**POST** `/auth/register`

Body:
```json
{
  "email": "user@example.com",
  "username": "newuser",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

## Users API

### Get Current User Profile

**GET** `/users/me`

Headers: `Authorization: Bearer <token>`

### Update Current User

**PUT** `/users/me`

Headers: `Authorization: Bearer <token>`

Body (all fields optional):
```json
{
  "email": "newemail@example.com",
  "username": "newusername",
  "full_name": "Updated Name"
}
```

### Upload Avatar

**POST** `/users/me/avatar`

Headers: `Authorization: Bearer <token>`

Form data:
```
file: <image_file>
```

### Delete Current User

**DELETE** `/users/me`

Headers: `Authorization: Bearer <token>`

### Get Public User Profile

**GET** `/users/{user_id}`

## Products API

### List All Products

**GET** `/products/`

Query parameters:
- `skip` (default: 0)
- `limit` (default: 20, max: 100)
- `category` (filter by category)
- `available_only` (boolean, default: true)
- `search` (search in name/description)

Example:
```
GET /products/?category=electronics&limit=10&skip=0
```

### Get Single Product

**GET** `/products/{product_id}`

### Create Product (Admin Only)

**POST** `/products/`

Headers: `Authorization: Bearer <admin_token>`

Body:
```json
{
  "name": "iPhone 15",
  "description": "Latest iPhone model",
  "price": 999.99,
  "stock_quantity": 50,
  "category": "electronics",
  "is_available": true
}
```

### Update Product (Admin Only)

**PUT** `/products/{product_id}`

Headers: `Authorization: Bearer <admin_token>`

Body (all fields optional):
```json
{
  "price": 899.99,
  "stock_quantity": 100
}
```

### Delete Product (Admin Only)

**DELETE** `/products/{product_id}`

Headers: `Authorization: Bearer <admin_token>`

### Upload Product Image (Admin Only)

**POST** `/products/{product_id}/image`

Headers: `Authorization: Bearer <admin_token>`

Form data:
```
file: <image_file>
```

### Remove Product Image (Admin Only)

**DELETE** `/products/{product_id}/image`

Headers: `Authorization: Bearer <admin_token>`

## Testing with cURL

### Register
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'
```

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

### Get Profile
```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### List Products
```bash
curl -X GET "http://localhost:8000/products/"
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad request (validation error)
- `401` - Unauthorized
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `422` - Validation error

Error format:
```json
{
  "detail": "Error description"
}
```

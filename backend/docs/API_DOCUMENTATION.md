# Banking Application API Documentation

## Overview

This document describes the REST API for the Banking Application. The API provides endpoints for user authentication, bank account management, transactions, and fraud detection.

## Base URL

```
http://localhost:8000/api/v1/
```

## Authentication

The API uses JWT (JSON Web Token) authentication. To access protected endpoints, you need to:

1. Register or login to get an access token
2. Include the token in the Authorization header:
   ```
   Authorization: Bearer <access_token>
   ```

## Rate Limiting

Some endpoints have rate limiting to prevent abuse:
- Login: 5 requests per minute per IP
- Sensitive operations: 10 requests per minute per user

## Error Responses

All errors follow a consistent format:

```json
{
    "error": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
        "field": "Specific error details"
    }
}
```

## Endpoints

### Authentication

#### Register User
```
POST /auth/register/
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

**Response (201):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "date_joined": "2023-01-01T00:00:00Z"
}
```

#### Login
```
POST /auth/login/
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response (200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe"
    }
}
```

#### Refresh Token
```
POST /auth/refresh/
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### User Profile
```
GET /auth/profile/
```

**Response (200):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "date_joined": "2023-01-01T00:00:00Z",
    "is_active": true
}
```

### Bank Accounts

#### List Accounts
```
GET /accounts/
```

**Response (200):**
```json
[
    {
        "id": 1,
        "account_number": "1234567890",
        "account_type": "RETAIL",
        "currency": "USD",
        "balance": "1000.00",
        "is_active": true,
        "created_at": "2023-01-01T00:00:00Z"
    }
]
```

#### Create Account
```
POST /accounts/
```

**Request Body:**
```json
{
    "account_type": "RETAIL",
    "currency": "USD",
    "overdraft_limit": "100.00"
}
```

**Response (201):**
```json
{
    "id": 1,
    "account_number": "1234567890",
    "account_type": "RETAIL",
    "currency": "USD",
    "balance": "0.00",
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z"
}
```

#### Get Account Details
```
GET /accounts/{id}/
```

**Response (200):**
```json
{
    "id": 1,
    "account_number": "1234567890",
    "account_type": "RETAIL",
    "currency": "USD",
    "balance": "1000.00",
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "overdraft_limit": "100.00"
}
```

### Transactions

#### List Transactions
```
GET /transactions/
```

**Query Parameters:**
- `account_id`: Filter by account ID
- `transaction_type`: Filter by type (DEBIT, CREDIT)
- `status`: Filter by status (PENDING, COMPLETED, FAILED)
- `from_date`: Filter by start date (YYYY-MM-DD)
- `to_date`: Filter by end date (YYYY-MM-DD)

**Response (200):**
```json
[
    {
        "id": 1,
        "from_account": "1234567890",
        "to_account": "0987654321",
        "amount": "100.00",
        "currency": "USD",
        "transaction_type": "DEBIT",
        "status": "COMPLETED",
        "description": "Transfer to friend",
        "created_at": "2023-01-01T00:00:00Z",
        "completed_at": "2023-01-01T00:01:00Z"
    }
]
```

#### Get Transaction Details
```
GET /transactions/{id}/
```

**Response (200):**
```json
{
    "id": 1,
    "from_account": "1234567890",
    "to_account": "0987654321",
    "amount": "100.00",
    "currency": "USD",
    "transaction_type": "DEBIT",
    "status": "COMPLETED",
    "description": "Transfer to friend",
    "metadata": {},
    "created_at": "2023-01-01T00:00:00Z",
    "completed_at": "2023-01-01T00:01:00Z"
}
```

#### Create Transaction
```
POST /transactions/
```

**Request Body:**
```json
{
    "from_account_id": 1,
    "to_account_id": 2,
    "amount": "100.00",
    "currency": "USD",
    "description": "Transfer to friend",
    "idempotency_key": "unique-key-123"
}
```

**Response (201):**
```json
{
    "id": 1,
    "from_account": "1234567890",
    "to_account": "0987654321",
    "amount": "100.00",
    "currency": "USD",
    "transaction_type": "DEBIT",
    "status": "COMPLETED",
    "description": "Transfer to friend",
    "created_at": "2023-01-01T00:00:00Z",
    "completed_at": "2023-01-01T00:01:00Z"
}
```

### Account Operations

#### Transfer Money
```
POST /accounts/transfer/
```

**Request Body:**
```json
{
    "from_account_id": 1,
    "to_account_id": 2,
    "amount": "100.00",
    "currency": "USD",
    "description": "Transfer to friend"
}
```

**Response (201):**
```json
{
    "id": 1,
    "from_account": "1234567890",
    "to_account": "0987654321",
    "amount": "100.00",
    "currency": "USD",
    "status": "COMPLETED",
    "created_at": "2023-01-01T00:00:00Z"
}
```

#### Deposit Money
```
POST /accounts/deposit/
```

**Request Body:**
```json
{
    "account_id": 1,
    "amount": "500.00",
    "description": "Salary deposit"
}
```

**Response (200):**
```json
{
    "id": 2,
    "account": "1234567890",
    "amount": "500.00",
    "currency": "USD",
    "transaction_type": "CREDIT",
    "status": "COMPLETED",
    "created_at": "2023-01-01T00:00:00Z"
}
```

#### Withdraw Money
```
POST /accounts/withdraw/
```

**Request Body:**
```json
{
    "account_id": 1,
    "amount": "100.00",
    "description": "ATM withdrawal"
}
```

**Response (200):**
```json
{
    "id": 3,
    "account": "1234567890",
    "amount": "100.00",
    "currency": "USD",
    "transaction_type": "DEBIT",
    "status": "COMPLETED",
    "created_at": "2023-01-01T00:00:00Z"
}
```

### Fraud Events

#### List Fraud Events
```
GET /fraud/events/
```

**Response (200):**
```json
[
    {
        "id": 1,
        "transaction": 1,
        "risk_score": 85,
        "rule_triggered": "LARGE_AMOUNT",
        "description": "Large amount transaction detected",
        "status": "REVIEW_PENDING",
        "created_at": "2023-01-01T00:00:00Z",
        "resolved_at": null
    }
]
```

#### Get Fraud Event Details
```
GET /fraud/events/{id}/
```

**Response (200):**
```json
{
    "id": 1,
    "transaction": {
        "id": 1,
        "amount": "10000.00",
        "currency": "USD",
        "from_account": "1234567890",
        "to_account": "0987654321"
    },
    "risk_score": 85,
    "rule_triggered": "LARGE_AMOUNT",
    "description": "Large amount transaction detected",
    "status": "REVIEW_PENDING",
    "metadata": {
        "ip_address": "192.168.1.1",
        "device_id": "device123"
    },
    "created_at": "2023-01-01T00:00:00Z",
    "resolved_at": null
}
```

## Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_FAILED` | Invalid credentials |
| `PERMISSION_DENIED` | User doesn't have permission |
| `NOT_FOUND` | Resource not found |
| `INSUFFICIENT_FUNDS` | Not enough balance for operation |
| `ACCOUNT_FROZEN` | Account is frozen |
| `ACCOUNT_NOT_FOUND` | Bank account not found |
| `DUPLICATE_TRANSACTION` | Transaction already processed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SERVER_ERROR` | Internal server error |

## Security Features

- JWT authentication with configurable token lifetimes
- Rate limiting on sensitive endpoints
- CORS configuration for cross-origin requests
- Security headers (X-Frame-Options, X-Content-Type-Options)
- Input validation and sanitization
- Atomic transactions to prevent data corruption

## Testing

Run the API tests with:

```bash
python manage.py test apps.accounts.tests_api
python manage.py test apps.transactions.tests_api
python manage.py test apps.fraud.tests_api
```

## Development

### Running the API Server

```bash
python manage.py runserver
```

### API Documentation (Swagger)

If drf-spectacular is installed, you can access interactive API documentation at:

```
http://localhost:8000/api/docs/
```

### Environment Variables

Key environment variables for production:

```bash
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
JWT_SECRET_KEY=your-jwt-secret
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

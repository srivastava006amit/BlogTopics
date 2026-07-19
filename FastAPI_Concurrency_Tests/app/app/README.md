# FastAPI Concurrency Lab - Developer Guide

# Objective

The objective of this project is to understand how concurrent requests affect
shared data inside a FastAPI application.

The project intentionally starts with an unsafe implementation so that race
conditions can be reproduced and understood before implementing the correct
solution.

This project is **not** intended to build a production banking system.

Instead, it teaches:

- asynchronous request processing
- database transactions
- race conditions
- lost updates
- ACID properties
- idempotency
- locking strategies
- concurrency-safe architecture

---

# Business Scenario

Assume a bank account contains

```
Balance = ₹100
```

100 users simultaneously try to withdraw

```
₹1
```

Only one shared resource exists:

```
Account #1
```

Every request modifies the same database row.

This creates contention.

---

# Project Flow

```
                Client
                   │
                   │ POST /withdraw
                   ▼
              FastAPI Endpoint
                   │
                   ▼
         SQLAlchemy Async Session
                   │
                   ▼
             PostgreSQL Database
                   │
                   ▼
            Updated Account Balance
```

---

# Folder Structure

```
app/
│
├── database.py
├── models.py
├── main.py
└── README.md
```

---

# Responsibilities

## database.py

Responsible for

- creating database engine
- connection pool
- session factory
- dependency injection

Nothing related to business logic should exist here.

---

## models.py

Defines database schema.

Currently

```
Account
```

Future

```
Transaction
Payment
Reservation
IdempotencyKey
```

---

## main.py

Contains

- API endpoints
- startup initialization
- business logic

Current endpoint

```
POST /accounts/{id}/withdraw-unsafe
```

This endpoint is intentionally unsafe.

Later versions will replace it with

- atomic SQL update
- SELECT FOR UPDATE
- optimistic locking

---

# Current Endpoint

```
POST

/accounts/{id}/withdraw-unsafe
```

Workflow

```
Read Balance

↓

Wait (Artificial Delay)

↓

Modify Balance

↓

Commit
```

The delay increases the probability that multiple requests read the same balance.

---

# Why We Added asyncio.sleep()

```
current_balance = account.balance

await asyncio.sleep(0.05)

account.balance = current_balance - amount
```

Normally

```
Read

↓

Write
```

happens too quickly.

Adding sleep widens the race-condition window.

This allows concurrent requests to overlap.

---

# Expected Behaviour

Current version

```
Unsafe

Race conditions expected.
```

Future version

```
Safe

No race conditions.
```

---

# Running Application

Start PostgreSQL

```
docker start concurrency-postgres
```

Run FastAPI

```
uvicorn app.main:app --reload
```

Swagger

```
http://127.0.0.1:8000/docs
```

---

# Manual Testing

Reset account

```
POST

/accounts/1/reset
```

Read account

```
GET

/accounts/1
```

Withdraw

```
POST

/accounts/1/withdraw-unsafe
```

---

# Debugging Guide

## Verify startup

```
GET /accounts/1
```

Should return

```
Balance = 100
```

---

## Verify endpoint

Use Swagger

```
POST

/accounts/1/withdraw-unsafe
```

Watch

```
balance changes
```

---

## Enable SQL Logging

Inside

database.py

```
echo=True
```

Now every SQL statement is printed.

Useful for understanding

```
SELECT

UPDATE

COMMIT

ROLLBACK
```

---

## Add Breakpoints

Recommended locations

```
account = await session.get(...)

↓

current_balance = ...

↓

await asyncio.sleep()

↓

session.commit()
```

Observe

```
balance before

balance after
```

---

# Future Improvements

- Atomic UPDATE
- SELECT FOR UPDATE
- Optimistic Locking
- Idempotency Keys
- Transaction Table
- Retry Logic
- Distributed Locking
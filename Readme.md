# FastAPI Concurrency Lab

## Overview

FastAPI Concurrency Lab is a learning project that demonstrates how race conditions occur in asynchronous FastAPI applications when multiple requests modify the same shared resource simultaneously.

The project intentionally implements an **unsafe withdrawal endpoint** to reproduce data corruption caused by concurrent requests. It also includes a custom asynchronous concurrency test that verifies whether the final database state matches the expected business outcome.

The primary purpose of this project is to understand **why asynchronous code alone does not guarantee concurrency correctness**.

---

# Learning Objectives

This project demonstrates the following concepts:

* FastAPI asynchronous endpoints
* SQLAlchemy Async ORM
* PostgreSQL integration
* Dependency Injection
* AsyncSession lifecycle
* HTTPX asynchronous client
* Concurrent request generation using `asyncio`
* Race conditions
* Lost update problem
* Business invariant verification
* Difference between HTTP success and data correctness

---

# Business Scenario

An account is initialized with a balance of **₹100**.

The application exposes a withdrawal endpoint that deducts money from the account.

A concurrency test generates **100 simultaneous withdrawal requests**, each attempting to withdraw **₹1** from the same account.

Since every request modifies the same database row, this creates contention and exposes race conditions in the unsafe implementation.

---

# Project Structure

```text
fastapi-concurrency-lab/
│
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── models.py
│   └── main.py
│
├── tests/
│   └── concurrency_test.py
│
└── README.md
```

---

# Architecture

```text
                Client
                   │
                   │ HTTP Request
                   ▼
             FastAPI Endpoint
                   │
                   ▼
        SQLAlchemy AsyncSession
                   │
                   ▼
         PostgreSQL Database
                   │
                   ▼
            Updated Account Data
```

---

# Components

## database.py

Responsible for:

* Creating the SQLAlchemy asynchronous engine
* Configuring the database connection pool
* Creating the `AsyncSession` factory
* Providing the session dependency for FastAPI endpoints

No business logic is implemented in this module.

---

## models.py

Defines the database schema.

Current model:

```text
Account
```

Fields:

* id
* balance

---

## main.py

Contains:

* FastAPI application
* Startup initialization
* REST endpoints
* Business logic

Implemented endpoints:

```text
POST /accounts/{id}/withdraw-unsafe

GET  /accounts/{id}

POST /accounts/{id}/reset
```

---

## concurrency_test.py

Implements a custom asynchronous concurrency test.

Responsibilities:

* Reset the account state
* Create concurrent tasks
* Synchronize task execution
* Execute concurrent HTTP requests
* Collect responses
* Read final database state
* Compare expected and actual results

---

# Current Withdrawal Logic

The withdrawal endpoint performs the following operations:

```text
Read Account

↓

Read Current Balance

↓

Artificial Delay

↓

Update Balance

↓

Commit Transaction
```

An artificial delay is intentionally introduced after reading the balance to increase the probability of multiple requests reading the same value before any transaction commits.

This exposes the race condition.

---

# Test Execution Flow

```text
Reset Account Balance

↓

Create 100 Async Tasks

↓

Pause Every Task

↓

Release All Tasks Together

↓

Execute Concurrent Requests

↓

Collect HTTP Responses

↓

Read Final Account Balance

↓

Calculate Expected Balance

↓

Compare Expected vs Actual
```

---

# Why asyncio.Event() Is Used

Every request waits on the same synchronization event before sending the HTTP request.

Without synchronization:

```text
Request 1

↓

Request 2

↓

Request 3
```

Requests begin at different times.

With synchronization:

```text
Request 1

Request 2

Request 3

↓

Released Together
```

This significantly increases the likelihood of concurrent database access.

---

# Why asyncio.gather() Is Used

All created tasks are executed concurrently.

`asyncio.gather()` waits until every task finishes before continuing.

This guarantees that the final database state is verified only after every withdrawal request has completed.

---

# Business Invariant

The correctness of the application is verified using the following invariant:

```text
Initial Balance

=

Final Balance

+

Successful Withdrawals
```

If this equation is violated, a race condition has occurred.

---

# Running the Project

## 1. Start PostgreSQL

```bash
docker start concurrency-postgres
```

---

## 2. Start FastAPI

```bash
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## 3. Run the Concurrency Test

Open another terminal.

```bash
python tests/concurrency_test.py
```

---

# Manual API Testing

Reset account:

```http
POST /accounts/1/reset
```

Read account:

```http
GET /accounts/1
```

Withdraw:

```http
POST /accounts/1/withdraw-unsafe
```

Example request body:

```json
{
    "amount": "1.00"
}
```

---

# Debugging Guide

## Verify Initial State

Before running the test:

```http
GET /accounts/1
```

Expected:

```text
Balance = 100
```

---

## Enable SQL Logging

In `database.py`:

```python
create_async_engine(
    DATABASE_URL,
    echo=True,
)
```

This displays every SQL statement executed by SQLAlchemy.

Useful for observing:

* SELECT
* UPDATE
* COMMIT
* ROLLBACK

---

## Recommended Breakpoints

Useful locations for debugging:

```python
account = await session.get(...)
```

```python
current_balance = account.balance
```

```python
await asyncio.sleep(...)
```

```python
await session.commit()
```

Observe how multiple requests read the same balance before any transaction commits.

---

## Experiment with Artificial Delay

Modify:

```python
await asyncio.sleep(0.05)
```

Try different values:

```text
0.01
0.05
0.10
0.20
```

Longer delays increase the likelihood of concurrent overlap.

---

## Experiment with Request Count

Modify:

```python
REQUEST_COUNT = 100
```

Try:

```text
50

100

200

500
```

Observe how contention changes.

---

# Expected Result

Example output:

```text
Requests attempted:    100

Successful responses:  100

Expected balance:      0.00

Actual balance:        97.00

RACE CONDITION DETECTED
```

Although every request returned HTTP 200, the final balance is incorrect.

This demonstrates that successful HTTP responses do not guarantee correct concurrent behavior.

---

# Key Takeaways

* `async` enables concurrent request handling but does not prevent race conditions.
* Multiple requests can read the same shared state before any transaction commits.
* Business correctness must always be verified using database state rather than HTTP responses alone.
* A concurrency test should validate both request outcomes and the final persisted data.
* Database state is the authoritative source for determining whether concurrent operations executed correctly.

# FastAPI Concurrency Lab - Test Guide

# Objective

The objective of this test suite is NOT performance testing.

The objective is

```
Prove whether concurrent requests corrupt shared data.
```

This is called

```
Correctness Testing
```

Later, these tests will become part of a larger volume/load test suite.

---

# Test Philosophy

Incorrect approach

```
100 requests returned 200

↓

Everything works
```

Correct approach

```
100 requests returned 200

↓

Database State Verified

↓

No Data Corruption
```

The database is always the source of truth.

---

# Current Test

```
concurrency_test.py
```

Scenario

```
Initial Balance

100

↓

100 concurrent withdrawals

↓

Each withdraws ₹1

↓

Expected Balance = 0
```

---

# Test Flow

```
Reset Account

↓

Create Async Tasks

↓

Synchronize Tasks

↓

Release Together

↓

Collect Results

↓

Read Final Balance

↓

Compare Expected vs Actual
```

---

# Why We Use asyncio.Event()

Without Event

```
Request 1

↓

Request 2

↓

Request 3
```

Requests start at different times.

With Event

```
Request 1

Request 2

Request 3

↓

Released Together
```

This greatly increases the probability of race conditions.

---

# Why We Use asyncio.gather()

```
Task1

Task2

Task3

↓

Wait for All
```

Without gather

the program could exit before all requests finish.

---

# Test Responsibilities

## Reset Data

Every test starts from

```
Balance = 100
```

This makes results repeatable.

---

## Create Tasks

```
100 withdrawal requests
```

Each task simulates one user.

---

## Synchronize

All tasks wait at

```
asyncio.Event()
```

---

## Execute

Tasks perform

```
POST /withdraw-unsafe
```

---

## Collect

Store

```
HTTP Status

Exceptions
```

---

## Verify

Compute

```
Expected Balance
```

Read

```
Actual Balance
```

Compare

```
Expected

vs

Actual
```

Mismatch

↓

Race Condition

---

# Running Test

Start FastAPI

```
uvicorn app.main:app --reload
```

Open another terminal

```
python tests/concurrency_test.py
```

---

# Expected Output

Unsafe implementation

Example

```
Successful Requests

100

Expected Balance

0

Actual Balance

97
```

Race Condition Detected

---

# Debugging Guide

## Print Each Request

Inside

withdraw_once()

print

```
Request Started

Request Finished
```

Observe execution order.

---

## SQL Logging

Enable

```
echo=True
```

Observe

```
SELECT

UPDATE

COMMIT
```

Notice multiple SELECTs reading identical balances.

---

## Add Delay

Experiment with

```
await asyncio.sleep()
```

Try

```
0.01

0.05

0.2

0.5
```

Observe

How race-condition frequency changes.

---

## Increase Requests

Try

```
50

100

200

500
```

Observe

Data corruption frequency.

---

## Multi-worker Test

Run

```
uvicorn app.main:app --workers 4
```

Repeat the test.

Observe

```
Behaviour changes
```

---

# Success Criteria

Current Version

Race Condition

Expected

Future Version

No Race Condition

Invariant

```
Initial Balance

=

Final Balance

+

Successful Withdrawals
```

must always hold.

---

# Future Test Cases

- Atomic UPDATE
- SELECT FOR UPDATE
- Optimistic Locking
- Idempotency
- Duplicate Request Test
- Connection Pool Exhaustion
- Deadlock Detection
- Locust Integration
- Sustained Volume Testing
- Distributed Multi-worker Testing
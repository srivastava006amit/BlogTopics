from __future__ import annotations

import asyncio
from collections import Counter
from decimal import Decimal

import httpx


BASE_URL = "http://127.0.0.1:8000"
ACCOUNT_ID = 1
REQUEST_COUNT = 100
WITHDRAWAL_AMOUNT = Decimal("1.00")


async def withdraw_once(
    client: httpx.AsyncClient,
    request_number: int,
    start_event: asyncio.Event,
) -> tuple[int, int]:
    await start_event.wait()

    response = await client.post(
        f"/accounts/{ACCOUNT_ID}/withdraw-unsafe",
        json={
            "amount": str(WITHDRAWAL_AMOUNT),
        },
    )

    return request_number, response.status_code


async def main() -> None:
    limits = httpx.Limits(
        max_connections=REQUEST_COUNT,
        max_keepalive_connections=REQUEST_COUNT,
    )

    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(
        base_url=BASE_URL,
        limits=limits,
        timeout=timeout,
    ) as client:
        reset_response = await client.post(
            f"/accounts/{ACCOUNT_ID}/reset"
        )
        reset_response.raise_for_status()

        start_event = asyncio.Event()

        tasks = [
            asyncio.create_task(
                withdraw_once(
                    client=client,
                    request_number=request_number,
                    start_event=start_event,
                )
            )
            for request_number in range(REQUEST_COUNT)
        ]

        # All prepared tasks are released together.
        start_event.set()

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        status_codes: list[int] = []
        exceptions: list[BaseException] = []

        for result in results:
            if isinstance(result, BaseException):
                exceptions.append(result)
            else:
                _, status_code = result
                status_codes.append(status_code)

        account_response = await client.get(
            f"/accounts/{ACCOUNT_ID}"
        )
        account_response.raise_for_status()

        final_balance = Decimal(
            str(account_response.json()["balance"])
        )

    counts = Counter(status_codes)
    successful_requests = counts[200]

    expected_balance = (
        Decimal("100.00")
        - successful_requests * WITHDRAWAL_AMOUNT
    )

    print()
    print("=== Concurrency Test Result ===")
    print(f"Requests attempted:    {REQUEST_COUNT}")
    print(f"Successful responses:  {successful_requests}")
    print(f"Status-code counts:    {dict(counts)}")
    print(f"Client exceptions:     {len(exceptions)}")
    print(f"Expected balance:      {expected_balance}")
    print(f"Actual balance:        {final_balance}")

    if final_balance != expected_balance:
        print()
        print("RACE CONDITION DETECTED")
        print(
            "Successful responses do not match the amount "
            "actually deducted."
        )
    else:
        print()
        print("No inconsistency observed in this run.")


if __name__ == "__main__":
    asyncio.run(main())
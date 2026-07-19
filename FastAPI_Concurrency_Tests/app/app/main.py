import asyncio
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionFactory, engine, get_session
from app.models import Account, Base


class WithdrawRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class WithdrawResponse(BaseModel):
    account_id: int
    withdrawn: Decimal
    remaining_balance: Decimal


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with SessionFactory() as session:
        account = await session.get(Account, 1)

        if account is None:
            session.add(
                Account(
                    id=1,
                    balance=Decimal("100.00"),
                )
            )
            await session.commit()

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.post(
    "/accounts/{account_id}/withdraw-unsafe",
    response_model=WithdrawResponse,
)
async def withdraw_unsafe(
    account_id: int,
    request: WithdrawRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WithdrawResponse:
    account = await session.get(Account, account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    if account.balance < request.amount:
        raise HTTPException(
            status_code=409,
            detail="Insufficient balance",
        )

    current_balance = account.balance

    # Deliberately widen the race-condition window.
    await asyncio.sleep(0.05)

    account.balance = current_balance - request.amount

    await session.commit()
    await session.refresh(account)

    return WithdrawResponse(
        account_id=account.id,
        withdrawn=request.amount,
        remaining_balance=account.balance,
    )


@app.get("/accounts/{account_id}")
async def get_account(
    account_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, object]:
    account = await session.get(Account, account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return {
        "account_id": account.id,
        "balance": account.balance,
    }


@app.post("/accounts/{account_id}/reset")
async def reset_account(
    account_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, object]:
    account = await session.get(Account, account_id)

    if account is None:
        account = Account(
            id=account_id,
            balance=Decimal("100.00"),
        )
        session.add(account)
    else:
        account.balance = Decimal("100.00")

    await session.commit()

    return {
        "account_id": account.id,
        "balance": account.balance,
    }
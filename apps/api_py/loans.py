from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_conn

router = APIRouter(prefix="/loans", tags=["loans"])

class LoanCreate(BaseModel):
    itemId: str
    borrowerName: str
    borrowerPhone: str
    startDate: str
    expectedReturnDate: str
    notes: Optional[str] = None

@router.get("")
def list_loans():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM "Loan" ORDER BY "createdAt" DESC;')
            return cur.fetchall()
    finally:
        conn.close()

@router.post("", status_code=201)
def create_loan(payload: LoanCreate):
    conn = get_conn()
    try:
        new_id = str(uuid4())
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "Loan"
                  ("id", "itemId", "borrowerName", "borrowerPhone", "startDate", "expectedReturnDate", "notes", "updatedAt")
                VALUES
                  (%s, %s, %s, %s, %s, %s, %s,NOW())
                RETURNING *;
                ''',
                (
                    new_id,
                    payload.itemId,
                    payload.borrowerName,
                    payload.borrowerPhone,
                    payload.startDate,
                    payload.expectedReturnDate,
                    payload.notes
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, detail=str(e))
    finally:
        conn.close()

@router.patch("/{loan_id}/return")
def return_loan(loan_id: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            SQL_UPDATE = '''
                UPDATE "Loan"
                  SET "status" = 'RETURNED'::"LoanStatus", "actualReturnDate" = NOW(), "updatedAt" = NOW()
                WHERE "id" = %s
                RETURNING *;
                '''
            cur.execute(SQL_UPDATE, (loan_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(404, "Loan not found")
            conn.commit()
            return row
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, detail=str(e))
    finally:
            conn.close()



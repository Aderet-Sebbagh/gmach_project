from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_conn
from datetime import datetime

from auth_deps import get_current_user, require_admin

router = APIRouter(prefix="/loans", tags=["loans"])

class LoanCreate(BaseModel):
    itemId: str
    borrowerName: str
    borrowerPhone: str
    startDate: datetime
    expectedReturnDate: datetime
    notes: Optional[str] = None

@router.get("")
def list_loans(status: Optional[str] = None, fromDate: Optional[datetime] = None, toDate: Optional[datetime] = None, admin = Depends(require_admin)):
    if fromDate is None and toDate is not None or fromDate is not None and toDate is None:
        raise HTTPException(status_code=400, detail="Provide both fromDate and toDate, or neither")
    if fromDate is not None and toDate is not None and fromDate > toDate:
       raise HTTPException(status_code=400, detail="Invalid date range: fromDate must be <= toDate")
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if status is not None and fromDate is not None and toDate is not None:
                cur.execute('''
                        SELECT *
                        FROM "Loan"
                        WHERE "status" = %s AND "startDate" <= %s AND %s <= "expectedReturnDate"
                        ORDER BY "createdAt" DESC;
                        '''
                        , (status, toDate, fromDate)
                        )
            elif status is not None:
                cur.execute('''
                        SELECT *
                        FROM "Loan"
                        WHERE "status" = %s
                        ORDER BY "createdAt" DESC;
                        '''
                        , (status,)
                        )
            elif fromDate is not None and toDate is not None:
                cur.execute('''
                        SELECT *
                        FROM "Loan"
                        WHERE "startDate" <= %s AND %s <= "expectedReturnDate" AND "status" = 'ACTIVE'::"LoanStatus"
                        ORDER BY "startDate" ASC;
                        '''
                        , (toDate, fromDate)
                        )
            else:
                cur.execute('''
                            SELECT *
                            FROM "Loan"
                            ORDER BY "createdAt" DESC;
                            '''
                            )
            return cur.fetchall()
    finally:
        conn.close()

@router.post("", status_code=201)
def create_loan(payload: LoanCreate, user = Depends(get_current_user)):
    conn = get_conn()
    try:
        new_id = str(uuid4())
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT COUNT(*) AS cnt 
                FROM "Loan" 
                WHERE "itemId" = %s AND "status" = 'ACTIVE'::"LoanStatus" AND DATE("startDate") <= DATE(%s) AND DATE(%s) <= DATE("expectedReturnDate")
                ''',
                (payload.itemId, payload.expectedReturnDate, payload.startDate)
                )
            row = cur.fetchone()
            active_overlap_count = int(row["cnt"])
            cur.execute(
                '''
                SELECT "quantity" 
                FROM "Item" 
                WHERE "id" = %s
                ''', (payload.itemId,))
            item_row = cur.fetchone()
            if item_row is None:
                raise HTTPException(status_code=404, detail="Item not found")
            quantity = item_row["quantity"]
            if active_overlap_count >= quantity:
                raise HTTPException(status_code=409, detail=f"Item not available in requested dates ({active_overlap_count} active overlapping loans of {quantity})")
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
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, detail=str(e))


@router.patch("/{loan_id}/return")
def return_loan(loan_id: str, admin = Depends(require_admin)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                    UPDATE "Loan"
                    SET "status" = 'RETURNED'::"LoanStatus", "actualReturnDate" = NOW(), "updatedAt" = NOW()
                    WHERE "id" = %s
                    RETURNING *;
                    '''
                    , (loan_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Loan not found")
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

@router.patch("/{loan_id}/cancel")
def cancel_loan(loan_id: str, admin = Depends(require_admin)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE "Loan"
                SET "status" = 'CANCELED'::"LoanStatus", "updatedAt" = NOW()
                WHERE "id" = %s AND "status" != 'RETURNED'::"LoanStatus"
                RETURNING *;
                ''', (loan_id,))
            row = cur.fetchone()
            if row is None:
                cur.execute('''
                            SELECT "status" 
                            FROM "Loan" 
                            WHERE "id" = %s
                            ''', (loan_id,))
                status_row = cur.fetchone()
                if status_row is None:
                    raise HTTPException(status_code=404, detail="Loan not found")
                raise HTTPException(status_code=409, detail="Cannot cancel a returned loan")
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

@router.get("/{loan_id}")
def get_loan(loan_id: str, admin = Depends(require_admin)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                    SELECT * FROM "Loan"
                    WHERE "id" = %s
                    ''', (loan_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Loan not found")
            return row
    finally:
        conn.close()

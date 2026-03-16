from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db import get_conn
from datetime import datetime
from auth_deps import get_current_user, require_admin

router = APIRouter(prefix="/calendar", tags=["calendar"])

@router.get("")
def list_calendar(fromDate: datetime, toDate: datetime, user = Depends(get_current_user)):
    if fromDate > toDate:
        raise HTTPException(status_code=400, detail="Invalid date range: fromDate must be <= toDate")
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT * FROM "Loan" 
                WHERE "startDate" <= %s AND %s <= "expectedReturnDate" AND "status" = 'ACTIVE'::"LoanStatus"
                ORDER BY "startDate" ASC
                ''',
                (toDate, fromDate)
            )
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()
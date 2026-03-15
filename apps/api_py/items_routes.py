from fastapi import APIRouter, HTTPException
from db import get_conn
from datetime import datetime

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/{item_id}/availability")
def item_availability(item_id: str, startDate: datetime, expectedReturnDate: datetime):
    if startDate > expectedReturnDate:
        raise HTTPException(status_code=400, detail="Invalid date range: startDate must be <= expectedReturnDate")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT "quantity" FROM "Item" 
                WHERE "id" = %s 
                '''
                , (item_id,)
            )
            item_row = cur.fetchone()
            if item_row is None:
                raise HTTPException(status_code=404, detail="item_row is None")
            else:
                quantity = item_row["quantity"]
            cur.execute(
                '''
                SELECT  COUNT(*) AS cnt FROM "Loan" 
                WHERE "itemId" = %s AND "status" = 'ACTIVE'::"LoanStatus" AND
                 DATE("startDate") <= DATE(%s) AND DATE(%s) <= DATE("expectedReturnDate")
                '''
                , (item_id, expectedReturnDate, startDate)
            )
            row = cur.fetchone()
            activeOverlaps = int(row["cnt"])
            availableCount = max(quantity - activeOverlaps, 0)
            return {"itemId": item_id, "quantity": quantity, "activeOverlaps": activeOverlaps, "availableCount": availableCount}
    finally:
        conn.close()
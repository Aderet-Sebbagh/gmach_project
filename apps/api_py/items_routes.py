from fastapi import APIRouter, HTTPException, Depends
from db import get_conn
from datetime import datetime
from auth_deps import get_current_user, require_admin
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import uuid4


router = APIRouter(prefix="/items", tags=["items"])

class ItemCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    quantity: int = 1
    imageUrl: Optional[str] = None
    notes: Optional[str] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    imageUrl: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
def list_items(user = Depends(get_current_user)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM "Item" ORDER BY "createdAt" DESC;')
            return cur.fetchall()
    finally:
        conn.close()

@router.post("", status_code=201)
def create_item(payload: ItemCreate, admin = Depends(require_admin)):
    conn = get_conn()
    try:
        new_id = str(uuid4())
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO "Item"
                  ("id","name","category","description","quantity","imageUrl","notes","createdAt","updatedAt")
                VALUES
                  (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING *;
                ''',
                (
                    new_id,
                    payload.name,
                    payload.category,
                    payload.description,
                    payload.quantity,
                    payload.imageUrl,
                    payload.notes,
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.put("/{item_id}")
def update_item(item_id: str, payload: ItemUpdate, admin = Depends(require_admin)):
    # keep only provided fields (exclude None)
    data: Dict[str, Any] = payload.model_dump(exclude_unset=True)

    if not data:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    allowed_fields = {"name", "category", "description", "quantity", "imageUrl", "notes"}
    unknown = set(data.keys()) - allowed_fields
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown fields: {sorted(list(unknown))}")

    # build dynamic UPDATE ... SET "field"=%s, ... , "updatedAt"=NOW()
    set_clauses = []
    values = []
    for key, value in data.items():
        set_clauses.append(f'"{key}" = %s')
        values.append(value)

    set_sql = ", ".join(set_clauses) + ', "updatedAt" = NOW()'
    values.append(item_id)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f'UPDATE "Item" SET {set_sql} WHERE "id" = %s RETURNING *;',
                tuple(values),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Item not found")
            conn.commit()
            return row
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: str, admin = Depends(require_admin)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "Item" WHERE "id" = %s;', (item_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Item not found")
            conn.commit()
            return
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/available")
def available_items(startDate: datetime, expectedReturnDate: datetime, user = Depends(get_current_user)):
    if startDate > expectedReturnDate:
        raise HTTPException(status_code=400, detail="Invalid date range: startDate must be <= expectedReturnDate")
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT i.*, i."quantity" - COALESCE(COUNT(l."id"), 0) AS "availableCount"
                FROM "Item" i
                LEFT JOIN "Loan" l ON l."itemId" = i."id" AND l."status" = 'ACTIVE'::"LoanStatus" 
                AND DATE(l."startDate") <= DATE(%s) AND DATE(%s) <= DATE(l."expectedReturnDate") 
                GROUP BY i."id" 
                HAVING (i."quantity" - COALESCE(COUNT(l."id"),0)) > 0 
                ORDER BY i."createdAt" DESC
                ''', (expectedReturnDate, startDate))
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()

@router.get("/{item_id}/availability")
def item_availability(item_id: str, startDate: datetime, expectedReturnDate: datetime,user = Depends(get_current_user)):
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
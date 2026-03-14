from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from db import get_conn

app = FastAPI(title="gmach_project API (Python)")

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

@app.get("/health")
def health():
    return {"ok": True, "service": "gmach api (python)"}

@app.get("/items")
def list_items():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM "Item" ORDER BY "createdAt" DESC;')
            return cur.fetchall()
    finally:
        conn.close()

@app.post("/items", status_code=201)
def create_item(payload: ItemCreate):
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

@app.put("/items/{item_id}")
def update_item(item_id: str, payload: ItemUpdate):
    # keep only provided fields (exclude None)
    data: Dict[str, Any] = payload.model_dump(exclude_none=True)

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

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: str):
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

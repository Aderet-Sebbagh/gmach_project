import hashlib
import hmac
import secrets
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import uuid4
from db import get_conn

from auth_deps import get_current_user, get_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    phone: str
    password: str

def hash_password(password) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{dk.hex()}"

def verify_password(password, stored):
    salt_hex, hash_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(dk.hex(), hash_hex)

@router.post("/login")
def login(payload: LoginRequest):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                    SELECT * FROM "User" WHERE "phone" = %s;
                    '''
                    , (payload.phone,))
            user = cur.fetchone()
            if user is None:
                raise HTTPException(status_code=401, detail="Invalid phone or password")
            stored = user["passwordHash"]
            if stored is None:
                raise HTTPException(status_code=403, detail="User has no password set")
            if not verify_password(payload.password, stored):
                raise HTTPException(status_code=401, detail="Invalid phone or password")
            token = str(uuid4())
            expires_at = datetime.utcnow() + timedelta(days=7)
            cur.execute('''
                        INSERT INTO "Session" ("token", "userId", "expiresAt")
                        VALUES (%s, %s, %s)
                        '''
                        , (token, user["id"], expires_at))
            conn.commit()
            return {"token": token, "userId": user["id"], "role": user["role"], "expiresAt": expires_at}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, detail=str(e))
    finally:
        conn.close()

@router.get("/me")
def me(user = Depends(get_current_user)):
    return {"id": user["id"], "name": user["name"], "phone": user["phone"], "role": user["role"]}

@router.post("/logout")
def logout(token = Depends(get_token)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                    DELETE FROM "Session" WHERE "token" = %s;
                    '''
                    , (token,))
            conn.commit()
            return {"ok": True}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, detail=str(e))
    finally:
        conn.close()

@router.get("/ping")
# def login(payload: LoginRequest):
def ping():
    return {"ok": True}
    # conn = get_conn()
    # try:
    #     with conn.cursor() as cur:
    #         cur.execute('''
    #                 SELECT user
    #                 FROM
    #                 ''', (loan_id,))
    #         password = cur.fetchone()
    #         if password is None:
    #             raise HTTPException(status_code=403, detail="User has no password set")
    #         verify_password(password, stored=)
    #         INSERT Session(token, userId, expiredAt)
    #         conn.commit()
    #         return {"token": token, "userId": userId, "expiredAt": expiredAt}
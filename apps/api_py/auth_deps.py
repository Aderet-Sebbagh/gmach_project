from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db import get_conn

security = HTTPBearer()

def get_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    return creds.credentials


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    # if not authorization:
    #     raise HTTPException(status_code=401, detail="Authorization missing")
    # if not authorization.startswith("Bearer "):
    #     raise HTTPException(status_code=401, detail="Authorization must start with 'Bearer'")
    token = creds.credentials
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                    SELECT u.* FROM "Session" s 
                    JOIN "User" u ON u."id" = s."userId" 
                    WHERE s."token" = %s AND s."expiresAt" > NOW();
                    '''
                    , (token,)
                    )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    finally:
        conn.close()

def require_admin(user = Depends(get_current_user)):
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="User role not ADMIN")
    return user

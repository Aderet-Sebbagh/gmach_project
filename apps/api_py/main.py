from fastapi import FastAPI

app = FastAPI(title="gmach_project API (Python)")

@app.get("/health")
def health():
    return {"ok": True, "service": "gmach api (python)"}

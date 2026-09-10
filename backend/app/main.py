import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI(title="Expense Flow", version="0.1.0")
logger = logging.getLogger("expense")


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 409):
        self.code, self.message, self.status = code, message, status


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={
        "code": exc.code, "message": exc.message, "operation_id": str(uuid4())
    })


@app.exception_handler(RequestValidationError)
def handle_validation(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "code": "validation", "message": "Revise os campos informados.",
        "fields": [".".join(str(p) for p in e["loc"]) for e in exc.errors()],
        "operation_id": str(uuid4()),
    })


@app.get("/health")
def health():
    return {"status": "ok"}

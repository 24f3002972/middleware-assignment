from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uuid
import time

app = FastAPI()

# --------------------------------------------------
# CHANGE THIS
# --------------------------------------------------

EMAIL = "24f3002972@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-eek0ih.example.com"

# Also allow the exam page origin.
# Replace this with the origin shown in the assignment page if different.
EXAM_ORIGIN = "https://exam.sanand.workers.dev"

RATE_LIMIT = 12
WINDOW = 10

# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
        EXAM_ORIGIN,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# --------------------------------------------------
# Rate limiter storage
# --------------------------------------------------

clients = {}

# --------------------------------------------------
# Middleware
# --------------------------------------------------

@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):
    # Request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Rate limiting
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    if client not in clients:
        clients[client] = []

    clients[client] = [t for t in clients[client] if now - t < WINDOW]

    if len(clients[client]) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        # IMPORTANT: include the request ID even on errors
        response.headers["X-Request-ID"] = request_id
        return response

    clients[client].append(now)

    response = await call_next(request)

    # IMPORTANT: always set the response header
    response.headers["X-Request-ID"] = request_id

    return response


# --------------------------------------------------
# Endpoint
# --------------------------------------------------

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }

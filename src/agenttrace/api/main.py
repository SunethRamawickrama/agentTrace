from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agenttrace.api.routes import router
from agenttrace.api.trace_store import load_traces


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_traces()
    yield


app = FastAPI(title="agentTrace API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

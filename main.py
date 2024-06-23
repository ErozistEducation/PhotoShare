import os
import re
from fastapi import FastAPI
from fastapi import FastAPI, Depends, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
from contextlib import asynccontextmanager

import uvicorn
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.routes import contacts,users
from src.database.db import get_db
from src.routes import auth
from src.conf.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    r = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )
    await FastAPILimiter.init(r)
    yield
    await r.close()

app = FastAPI(lifespan=lifespan)

# app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(contacts.router, prefix='/api')


@app.get("/")
def read_root():
    return {"message": "Contacts API"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
    
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="info")
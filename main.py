from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from config import Config
from util.mongo import *
from util.api import *
from api import account
from api import lic
from api import demo
import uvicorn
import os

def joba_initialize():
    os.makedirs(Config.LOG_DIR, exist_ok = True)
    
    connect_mongo()

def joba_finalize():
    disconnect_mongo()

joba_initialize()

app = FastAPI()

app.add_middleware(MSMiddleware)

app.include_router(account.router, prefix = "/account")
app.include_router(lic.router, prefix = "/lic")
app.include_router(demo.router, prefix = "/demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

def main():
    try:
        uvicorn.run(app = "main:app", host = Config.HOST, port = Config.PORT, reload = Config.RELOAD)
    finally:
        joba_finalize()

@app.get("/")
async def root():
    return {
        "status": 200,
        "version": Config.EXTENSION_VER,
        "gstore": Config.EXTENSION_LINK,
        "notice": Config.NOTICE
    }

if __name__ == "__main__":
    main()

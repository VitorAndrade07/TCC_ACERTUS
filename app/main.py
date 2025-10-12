from typing import Union

from fastapi import FastAPI

from fastapi import FastAPI
from routes.routes import router as routes

app = FastAPI()

app.include_router(routes)
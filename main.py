from fastapi import FastAPI

from apps import models, routes
from apps.services.auth import generate_fake_users
from config.celery_utils import create_celery
from config.db import engine
from config.settings import settings

app = FastAPI(
    name=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)
app.celery_app = create_celery()

celery = app.celery_app


@app.on_event('startup')
async def startup_event():
    models.Base.metadata.drop_all(engine)
    models.Base.metadata.create_all(engine)
    app.include_router(routes.post)
    app.include_router(routes.auth)
    await generate_fake_users()

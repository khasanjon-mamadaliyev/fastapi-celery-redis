import os

import redis
from dotenv import load_dotenv

load_dotenv('.env')


class Settings:
    PROJECT_NAME: str = "FastApi api"
    PROJECT_DESCRIPTION: str = "New project"
    PROJECT_VERSION: str = "1.0.0"
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    PG_URL: str = f'{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}'
    DATABASE_URL: str = f"postgresql+psycopg2://{PG_URL}"
    CELERY_BROKER_URL: str = os.getenv('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND: str = f'db+postgresql://{PG_URL}'

    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # in min
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # in min
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 120  # in min

    REDIS_VERIFY_TIME: int = 120  # in sec
    REDIS_CLIENT = redis.Redis(host='localhost', port=6379, decode_responses=True)

    TEST_USER_EMAIL: str = 'test@example.com'
    SMTP_HOST: str = os.getenv('SMTP_HOST')
    SMTP_PORT: str = os.getenv('SMTP_PORT')
    SMTP_EMAIL: str = os.getenv('SMTP_EMAIL')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD')


settings = Settings()

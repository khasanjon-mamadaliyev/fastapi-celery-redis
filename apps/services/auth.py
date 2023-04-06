from datetime import datetime, timedelta

from faker import Faker
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from apps import cache_redis, models, schemas
from apps.hashing import Hasher
from celery_tasks.email_sender import send_verification_email
from config.authentication import oauth2_scheme
from config.db import get_db
from config.settings import settings


async def register_worker(form: schemas.Register, db: Session):
    # save database
    form = form.dict(exclude_none=True)
    user = models.Users(**form)  # noqa
    db.add(user)
    db.commit()

    # redis
    code: int = cache_redis.generate_verification_code()
    time = settings.REDIS_VERIFY_TIME
    cache_redis.cache_redis(user.email, code, time)
    print(code)

    # send email
    send_verification_email.delay(user, code)

    return user


async def verify_email_worker(form: schemas.VerifyEmail, db: Session):
    email, code = form.email, form.code
    # get code from redis cache
    cache_code = cache_redis.cache.get(email)
    # check is code verify time
    if cache_code is not None:
        # check code equal
        if cache_code == code:
            user = db.query(models.Users).filter_by(email=email).first()
            user.is_active = True
            db.commit()
            return HTTPException(200, "Successfully verification !")
        return HTTPException(400, "Verification code error !")
    return HTTPException(400, "Verification code is outdated !")


async def send_again_verify_code_worker(form: schemas.VerifyAgain):
    db = next(get_db())
    email = form.email
    # code
    code = cache_redis.generate_verification_code()
    # redis
    time = settings.REDIS_VERIFY_TIME
    cache_redis.cache_redis(email, code, time)
    user = db.query(models.Users).filter_by(email=email).first()
    print(code, 'again code')

    send_verification_email.delay(user, code)
    return HTTPException(200, "Successfully send again verify code")


def login_create_token(form: OAuth2PasswordRequestForm, db: Session):
    result: dict = authenticate_user(db, form.username, form.password)
    if result.get('error'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get('result'),
            headers={'WWW-Authenticate': 'Bearer'}
        )
    user = result['user']
    access_token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)
    response = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }
    return response


def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        response = {
            'error': True,
            'result': 'Email not available'
        }
        return response
    if not Hasher.check_hash(password, user.password):
        response = {
            'error': True,
            'result': 'Incorrect password'
        }
        return response
    response = {
        'error': False,
        'user': user
    }
    return response


def get_user(db: Session, email: str):
    user = db.query(models.Users).filter_by(email=email).first()
    if user:
        return user


def create_access_token(email: str):
    expires_data = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if expires_data:
        expire = datetime.utcnow() + expires_data
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        'type': 'access',
        'sub': email,
        'exp': expire
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY)
    return encoded_jwt


def create_refresh_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    payload = {
        'sub': email,
        'type': 'refresh',
        'exp': expire
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY)
    return encoded_jwt


def get_access_token_by_refresh_token(
        db: Session,
        refresh_token: str
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY)
        email: str = payload.get('sub')
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, email)
    access_token = create_access_token(user.email)
    if user is None:
        raise credentials_exception
    return access_token


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY)
        email: str = payload.get('sub')
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, email)
    if user is None:
        raise credentials_exception
    db.close()
    return user


def get_current_activate_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Inactive user'
        )
    return current_user


def get_current_user_admin(current_user: schemas.User = Depends(get_current_activate_user)):
    if not current_user.status.name == 'ADMIN':
        raise HTTPException(400, "You must be an admin to post !")
    return current_user


def get_current_user_vip_client(current_user: schemas.User = Depends(get_current_activate_user)):
    if not current_user.status.name == 'VIP_CLIENT':
        raise HTTPException(400, "You must be a VIP CLIENT !")
    return current_user


async def generate_fake_users():
    faker = Faker()
    db = next(get_db())
    users = []
    for _ in range(10):  # CLIENT
        users.append(
            models.Users(
                name=faker.name(),
                status='CLIENT',
                email=faker.email(),
                is_active=True,
                password=Hasher.make_hash('1')
            )
        )
    for _ in range(5):  # VIP CLIENT
        users.append(
            models.Users(
                name=faker.name(),
                status='VIP_CLIENT',
                email=faker.email(),
                is_active=True,
                password=Hasher.make_hash('1')
            )
        )
    for _ in range(4):  # ADMIN
        users.append(
            models.Users(
                name=faker.name(),
                status='ADMIN',
                email=faker.email(),
                is_active=True,
                password=Hasher.make_hash('1')
            )
        )
    db.add_all(users)
    db.commit()
    db.close()

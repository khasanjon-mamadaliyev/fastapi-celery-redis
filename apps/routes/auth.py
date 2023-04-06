from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from apps import schemas
from apps.services.auth import (get_access_token_by_refresh_token,
                                get_current_activate_user, login_create_token,
                                register_worker, send_again_verify_code_worker,
                                verify_email_worker)
from config.db import get_db

auth = APIRouter(tags=['auth'])


@auth.post('/register', summary='Register with email')
async def register(form: schemas.Register = Depends(schemas.Register.as_form), db: Session = Depends(get_db)):
    user = await register_worker(form, db)
    return user


@auth.post('/verify-email', summary='Check email with verification code !')
async def verify_email(
        form: schemas.VerifyEmail = Depends(schemas.VerifyEmail.as_form),
        db: Session = Depends(get_db)
):
    response = await verify_email_worker(form, db)
    return response


@auth.post('/again-send-code', summary='Again send verification code !')
async def send_again_verify_code(
        form: schemas.VerifyAgain = Depends(schemas.VerifyAgain.as_form)
):
    response = await send_again_verify_code_worker(form)
    return response


@auth.post('/token', response_model=schemas.Login)
def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    result = login_create_token(form_data, db)
    return result


@auth.post('/refresh-token', response_model=schemas.ResponseRefreshToken, summary='get access token')
def refresh_token(
        form: schemas.RefreshToken,
        db: Session = Depends(get_db)
):
    access_token = get_access_token_by_refresh_token(db, form.refresh_token)
    response = {
        'access_token': access_token,
        'token_type': 'bearer'
    }
    return response


@auth.get('/user')
def read_user_me(current_user: schemas.User = Depends(get_current_activate_user)):
    return current_user

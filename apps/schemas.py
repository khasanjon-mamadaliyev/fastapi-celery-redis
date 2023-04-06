import re

from fastapi import Form, HTTPException
from pydantic import BaseModel, root_validator, validator
from sqlalchemy.orm import Session

from apps import models
from apps.hashing import Hasher
from config.db import get_db


class Register(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str

    class Config:
        orm_mode = True

    @root_validator()
    def validation(cls, values):
        db = next(get_db())
        email = values['email']
        password = values['password']
        confirm_password = values['confirm_password']

        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if not re.search(regex, email):
            raise HTTPException(400, "Must be a valid email address")

        if password != confirm_password:
            raise HTTPException(400, "Password did not match !")

        user = db.query(models.Users).filter_by(email=email).first()
        if user:
            raise HTTPException(400, "Email is already registered !")
        values['password'] = Hasher.make_hash(password)
        values['confirm_password'] = None

        return values

    @classmethod
    def as_form(
            cls,
            name: str = Form(),
            email: str = Form(),
            password: str = Form(),
            confirm_password: str = Form()
    ):
        return cls(
            name=name,
            email=email,
            password=password,
            confirm_password=confirm_password,
        )


class VerifyEmail(BaseModel):
    email: str
    code: str

    class Config:
        orm_mode = True

    @validator('email')
    def validate_email(cls, value):
        db: Session = next(get_db())
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if not re.search(regex, value):
            raise HTTPException(400, 'Must be a valid email address')
        user = db.query(models.Users).filter_by(email=value).first()
        if not user:
            raise HTTPException(400, "Email address doesn't exists !")
        if user.is_active:
            raise HTTPException(400, "Already confirmed !")
        db.close()
        return value

    @classmethod
    def as_form(
            cls,
            email: str = Form(...),
            code: str = Form(...)
    ):
        return cls(email=email, code=code)


class VerifyAgain(BaseModel):
    email: str

    class Config:
        orm_mode = True

    @validator('email')
    def validate_email(cls, value):
        db: Session = next(get_db())
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if not re.search(regex, value):
            raise HTTPException(400, "Must be a valid email address")
        user = db.query(models.Users).filter_by(email=value).first()
        if not user:
            raise HTTPException(400, "Email address doesn't exists !")
        if user.is_active:
            raise HTTPException(400, "Already confirmed !")
        db.close()
        return value

    @classmethod
    def as_form(
            cls,
            email: str = Form(...),
    ):
        return cls(
            email=email,
        )


class Login(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class ResponseRefreshToken(BaseModel):
    access_token: str


class RefreshToken(BaseModel):
    refresh_token: str


class User(BaseModel):
    name: str
    email: str
    is_active: bool
    status: str


class RegisterModel(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str

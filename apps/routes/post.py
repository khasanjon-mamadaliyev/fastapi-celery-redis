from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps import schemas
from apps.services.auth import (get_current_user_admin,
                                get_current_user_vip_client)
from apps.services.post import (add_post_worker, delete_post_worker,
                                get_posts_premium_worker, get_posts_worker)
from config.db import get_db

post = APIRouter(tags=['post'])


@post.post('/add', summary='added n posts')
async def add_post(n: int, current_user: schemas.User = Depends(get_current_user_admin)):
    response = await add_post_worker(n)
    return response


@post.get('/read', summary='read post')
async def read_post(db: Session = Depends(get_db)):
    posts = await get_posts_worker(db)
    return posts


@post.get('/read-premium', summary='read premium post for VIP CLIENT')
async def read_premium_post(
        current_user: schemas.User = Depends(get_current_user_vip_client),
        db: Session = Depends(get_db)
):
    posts = await get_posts_premium_worker(db)
    return posts


@post.delete('/delete/{pk}', summary='delete posts if is ADMIN')
async def delete_post(
        pk: int,
        current_user: schemas.User = Depends(get_current_user_admin),
        db: Session = Depends(get_db)
):
    response = await delete_post_worker(pk, current_user, db)
    return response

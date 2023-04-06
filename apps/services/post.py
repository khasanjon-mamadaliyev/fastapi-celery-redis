from fastapi.responses import UJSONResponse
from sqlalchemy.orm import Session

from apps import models, schemas
from celery_tasks.post import generate_posts


async def add_post_worker(n: int):
    generate_posts.delay(n)
    return UJSONResponse({'message': f"Successfully added {n} posts"})


async def get_posts_premium_worker(db: Session):
    posts = db.query(models.Post).filter_by(is_premium=True).all()
    return posts


async def delete_post_worker(
        pk: int,
        user: schemas.User,
        db: Session
):
    db.query(models.Post).filter_by(id=pk, author_id=user.id).delete()  # noqa
    db.commit()
    return UJSONResponse({'message': 'Successfully deleted post'})


async def get_posts_worker(db: Session):
    posts = db.query(models.Post).filter_by(is_premium=False).all()
    return posts

"""分类接口"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.response import success
from app.models.user import User
from app.schemas.category import CategoryIn
from app.services import taxonomy_service

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("", summary="分类列表（含文章数）")
def list_categories(db: Session = Depends(get_db)):
    return success(taxonomy_service.list_categories(db))


@router.post("", summary="新建分类")
def create(
    payload: CategoryIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    cat = taxonomy_service.create_category(
        db, payload.name, payload.slug, payload.description, payload.sort_order
    )
    return success({"id": cat.id, "name": cat.name, "slug": cat.slug}, msg="分类已创建")


@router.put("/{cat_id}", summary="更新分类")
def update(
    cat_id: int,
    payload: CategoryIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    cat = taxonomy_service.update_category(
        db, cat_id, payload.name, payload.slug, payload.description, payload.sort_order
    )
    return success({"id": cat.id, "name": cat.name, "slug": cat.slug}, msg="分类已更新")


@router.delete("/{cat_id}", summary="删除分类")
def delete(
    cat_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    taxonomy_service.delete_category(db, cat_id)
    return success(msg="分类已删除")

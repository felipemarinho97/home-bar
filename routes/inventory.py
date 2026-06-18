"""Backoffice inventory management."""

import os
import shutil
from pathlib import Path
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from auth import check_backoffice
from models import InventoryItem, InventoryPhoto
from schemas import (
    InventoryItemOut, InventoryItemCreate, InventoryItemUpdate,
    InventoryPhotoOut,
)

UPLOAD_DIR = Path("uploads")

router = APIRouter(prefix="/admin/inventory", tags=["admin-inventory"])


@router.get("", response_model=list[InventoryItemOut])
def list_inventory(
    category: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(check_backoffice),
):
    q = db.query(InventoryItem)
    if category:
        q = q.filter(InventoryItem.category == category)
    return q.order_by(InventoryItem.name).all()


@router.post("", response_model=InventoryItemOut, status_code=201)
def create_inventory_item(
    body: InventoryItemCreate,
    db: Session = Depends(get_db),
    _=Depends(check_backoffice),
):
    item = InventoryItem(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=InventoryItemOut)
def get_inventory_item(item_id: int, db: Session = Depends(get_db), _=Depends(check_backoffice)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.put("/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(
    item_id: int,
    body: InventoryItemUpdate,
    db: Session = Depends(get_db),
    _=Depends(check_backoffice),
):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=200)
def remove_inventory_item(item_id: int, db: Session = Depends(get_db), _=Depends(check_backoffice)):
    """Sets quantity to 0 instead of deleting."""
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    item.quantity = 0
    db.commit()
    return {"detail": "Item quantity set to 0"}


@router.post("/{item_id}/photo", response_model=InventoryPhotoOut)
def upload_inventory_photo(
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(check_backoffice),
):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"inventory_{item_id}_{date.today().isoformat()}_{os.urandom(4).hex()}{ext}"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    photo = InventoryPhoto(inventory_item_id=item_id, url=f"/uploads/{filename}")
    db.add(photo)

    if not item.photo_url:
        item.photo_url = f"/uploads/{filename}"

    db.commit()
    db.refresh(photo)
    return photo


@router.delete("/{item_id}/photo/{photo_id}", status_code=204)
def delete_inventory_photo(
    item_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    _=Depends(check_backoffice),
):
    photo = db.get(InventoryPhoto, photo_id)
    if not photo or photo.inventory_item_id != item_id:
        raise HTTPException(status_code=404, detail="Photo not found")

    filepath = UPLOAD_DIR / Path(photo.url).name
    if filepath.exists():
        filepath.unlink()

    db.delete(photo)

    item = db.get(InventoryItem, item_id)
    if item and item.photo_url == photo.url:
        item.photo_url = None

    db.commit()

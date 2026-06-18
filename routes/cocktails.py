import os
import shutil
from pathlib import Path
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from auth import check_backoffice
from models import (
    Cocktail, CocktailIngredient, CocktailGlass, CocktailAccessory, CocktailPhoto,
)
from schemas import (
    CocktailOut, CocktailCreate, CocktailUpdate,
    CocktailIngredientOut, CocktailGlassOut, CocktailAccessoryOut, CocktailPhotoOut,
)

UPLOAD_DIR = Path("uploads")

router = APIRouter(prefix="/admin/cocktails", tags=["admin-cocktails"])


def _cocktail_to_out(cocktail: Cocktail) -> CocktailOut:
    return CocktailOut(
        id=cocktail.id,
        name=cocktail.name,
        method=cocktail.method,
        garnish=cocktail.garnish,
        base_spirit=cocktail.base_spirit,
        tags=cocktail.tags or [],
        ingredients=[
            CocktailIngredientOut(
                id=ci.id,
                ingredient_type_id=ci.ingredient_type_id,
                ingredient_type_name=ci.ingredient_type.name if ci.ingredient_type else None,
                amount=ci.amount,
                unit=ci.unit,
                substitute_type_ids=ci.substitute_type_ids or [],
            )
            for ci in cocktail.ingredients
        ],
        glasses=[
            CocktailGlassOut(
                id=cg.id,
                inventory_item_id=cg.inventory_item_id,
                inventory_item_name=cg.inventory_item.name if cg.inventory_item else None,
            )
            for cg in cocktail.glasses
        ],
        accessories=[
            CocktailAccessoryOut(
                id=ca.id,
                inventory_item_id=ca.inventory_item_id,
                inventory_item_name=ca.inventory_item.name if ca.inventory_item else None,
            )
            for ca in cocktail.accessories
        ],
        photos=[
            CocktailPhotoOut(
                id=cp.id,
                cocktail_id=cp.cocktail_id,
                url=cp.url,
                is_primary=cp.is_primary,
            )
            for cp in cocktail.photos
        ],
    )


@router.get("", response_model=list[CocktailOut])
def list_cocktails(db: Session = Depends(get_db), _=Depends(check_backoffice)):
    cocktails = db.query(Cocktail).order_by(Cocktail.name).all()
    return [_cocktail_to_out(c) for c in cocktails]


@router.get("/{cocktail_id}", response_model=CocktailOut)
def get_cocktail(cocktail_id: int, db: Session = Depends(get_db), _=Depends(check_backoffice)):
    cocktail = db.get(Cocktail, cocktail_id)
    if not cocktail:
        raise HTTPException(status_code=404, detail="Cocktail not found")
    return _cocktail_to_out(cocktail)


@router.post("", response_model=CocktailOut, status_code=201)
def create_cocktail(body: CocktailCreate, db: Session = Depends(get_db), _=Depends(check_backoffice)):
    cocktail = Cocktail(
        name=body.name,
        method=body.method,
        garnish=body.garnish,
        base_spirit=body.base_spirit,
        tags=body.tags or [],
    )
    db.add(cocktail)
    db.flush()

    for ing in body.ingredients:
        db.add(CocktailIngredient(
            cocktail_id=cocktail.id,
            ingredient_type_id=ing.ingredient_type_id,
            amount=ing.amount,
            unit=ing.unit,
            substitute_type_ids=ing.substitute_type_ids or [],
        ))

    for gl in body.glasses:
        db.add(CocktailGlass(
            cocktail_id=cocktail.id,
            inventory_item_id=gl.inventory_item_id,
        ))

    for acc in body.accessories:
        db.add(CocktailAccessory(
            cocktail_id=cocktail.id,
            inventory_item_id=acc.inventory_item_id,
        ))

    db.commit()
    db.refresh(cocktail)
    return _cocktail_to_out(cocktail)


@router.put("/{cocktail_id}", response_model=CocktailOut)
def update_cocktail(
    cocktail_id: int,
    body: CocktailUpdate,
    db: Session = Depends(get_db),
    _=Depends(check_backoffice),
):
    cocktail = db.get(Cocktail, cocktail_id)
    if not cocktail:
        raise HTTPException(status_code=404, detail="Cocktail not found")

    if body.name is not None:
        cocktail.name = body.name
    if body.method is not None:
        cocktail.method = body.method
    if body.garnish is not None:
        cocktail.garnish = body.garnish
    if body.base_spirit is not None:
        cocktail.base_spirit = body.base_spirit
    if body.tags is not None:
        cocktail.tags = body.tags
    if body.ingredients is not None:
        db.query(CocktailIngredient).filter(CocktailIngredient.cocktail_id == cocktail_id).delete()
        for ing in body.ingredients:
            db.add(CocktailIngredient(
                cocktail_id=cocktail_id,
                ingredient_type_id=ing.ingredient_type_id,
                amount=ing.amount,
                unit=ing.unit,
                substitute_type_ids=ing.substitute_type_ids or [],
            ))

    if body.glasses is not None:
        db.query(CocktailGlass).filter(CocktailGlass.cocktail_id == cocktail_id).delete()
        for gl in body.glasses:
            db.add(CocktailGlass(
                cocktail_id=cocktail_id,
                inventory_item_id=gl.inventory_item_id,
            ))

    if body.accessories is not None:
        db.query(CocktailAccessory).filter(CocktailAccessory.cocktail_id == cocktail_id).delete()
        for acc in body.accessories:
            db.add(CocktailAccessory(
                cocktail_id=cocktail_id,
                inventory_item_id=acc.inventory_item_id,
            ))

    db.commit()
    db.refresh(cocktail)
    return _cocktail_to_out(cocktail)


@router.delete("/{cocktail_id}", status_code=204)
def delete_cocktail(cocktail_id: int, db: Session = Depends(get_db), _=Depends(check_backoffice)):
    cocktail = db.get(Cocktail, cocktail_id)
    if not cocktail:
        raise HTTPException(status_code=404, detail="Cocktail not found")

    for photo in cocktail.photos:
        filepath = UPLOAD_DIR / Path(photo.url).name
        if filepath.exists():
            filepath.unlink()

    db.delete(cocktail)
    db.commit()


@router.post("/{cocktail_id}/photo", response_model=CocktailPhotoOut)
def upload_cocktail_photo(
    cocktail_id: int,
    file: UploadFile = File(...),
    is_primary: bool = False,
    db: Session = Depends(get_db),
    _=Depends(check_backoffice),
):
    cocktail = db.get(Cocktail, cocktail_id)
    if not cocktail:
        raise HTTPException(status_code=404, detail="Cocktail not found")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"cocktail_{cocktail_id}_{date.today().isoformat()}_{os.urandom(4).hex()}{ext}"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if is_primary:
        db.query(CocktailPhoto).filter(
            CocktailPhoto.cocktail_id == cocktail_id,
            CocktailPhoto.is_primary == True,
        ).update({"is_primary": False})

    photo = CocktailPhoto(
        cocktail_id=cocktail_id,
        url=f"/uploads/{filename}",
        is_primary=is_primary,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@router.delete("/{cocktail_id}/photo/{photo_id}", status_code=204)
def delete_cocktail_photo(
    cocktail_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    _=Depends(check_backoffice),
):
    photo = db.get(CocktailPhoto, photo_id)
    if not photo or photo.cocktail_id != cocktail_id:
        raise HTTPException(status_code=404, detail="Photo not found")

    filepath = UPLOAD_DIR / Path(photo.url).name
    if filepath.exists():
        filepath.unlink()

    db.delete(photo)
    db.commit()

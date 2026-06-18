from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Cocktail, CocktailPhoto
from schemas import CocktailOut, CocktailListOut, CocktailIngredientOut, CocktailGlassOut, CocktailAccessoryOut, CocktailPhotoOut
from availability import is_cocktail_available, get_available_cocktail_ids

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/cocktails/available", response_model=list[CocktailListOut])
def list_available_cocktails(db: Session = Depends(get_db)):
    available_ids = get_available_cocktail_ids(db)
    if not available_ids:
        return []

    cocktails = db.query(Cocktail).filter(Cocktail.id.in_(available_ids)).all()

    result = []
    for c in cocktails:
        primary_photo = db.query(CocktailPhoto).filter(
            CocktailPhoto.cocktail_id == c.id,
            CocktailPhoto.is_primary == True,
        ).first()
        if not primary_photo:
            primary_photo = db.query(CocktailPhoto).filter(
                CocktailPhoto.cocktail_id == c.id,
            ).first()

        result.append(CocktailListOut(
            id=c.id,
            name=c.name,
            base_spirit=c.base_spirit,
            tags=c.tags or [],
            primary_photo_url=primary_photo.url if primary_photo else None,
        ))

    return result


@router.get("/cocktails/{cocktail_id}", response_model=CocktailOut)
def get_cocktail_detail(cocktail_id: int, db: Session = Depends(get_db)):
    cocktail = db.get(Cocktail, cocktail_id)
    if not cocktail:
        raise HTTPException(status_code=404, detail="Cocktail not found")

    ingredients_out = []
    for ci in cocktail.ingredients:
        ingredients_out.append(CocktailIngredientOut(
            id=ci.id,
            ingredient_type_id=ci.ingredient_type_id,
            ingredient_type_name=ci.ingredient_type.name if ci.ingredient_type else None,
            amount=ci.amount,
            unit=ci.unit,
            substitute_type_ids=ci.substitute_type_ids or [],
        ))

    glasses_out = []
    for cg in cocktail.glasses:
        glasses_out.append(CocktailGlassOut(
            id=cg.id,
            inventory_item_id=cg.inventory_item_id,
            inventory_item_name=cg.inventory_item.name if cg.inventory_item else None,
        ))

    accessories_out = []
    for ca in cocktail.accessories:
        accessories_out.append(CocktailAccessoryOut(
            id=ca.id,
            inventory_item_id=ca.inventory_item_id,
            inventory_item_name=ca.inventory_item.name if ca.inventory_item else None,
        ))

    photos_out = []
    for cp in cocktail.photos:
        photos_out.append(CocktailPhotoOut(
            id=cp.id,
            cocktail_id=cp.cocktail_id,
            url=cp.url,
            is_primary=cp.is_primary,
        ))

    return CocktailOut(
        id=cocktail.id,
        name=cocktail.name,
        method=cocktail.method,
        garnish=cocktail.garnish,
        base_spirit=cocktail.base_spirit,
        tags=cocktail.tags or [],
        ingredients=ingredients_out,
        glasses=glasses_out,
        accessories=accessories_out,
        photos=photos_out,
    )


@router.get("/cocktails/{cocktail_id}/availability")
def check_availability(cocktail_id: int, db: Session = Depends(get_db)):
    cocktail = db.get(Cocktail, cocktail_id)
    if not cocktail:
        raise HTTPException(status_code=404, detail="Cocktail not found")
    return {"is_available": is_cocktail_available(db, cocktail_id)}

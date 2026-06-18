from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import check_backoffice
from models import IngredientType
from schemas import IngredientTypeCreate, IngredientTypeUpdate, IngredientTypeOut

router = APIRouter(prefix="/admin/ingredient-types", tags=["admin-ingredient-types"])


@router.get("", response_model=list[IngredientTypeOut])
def list_ingredient_types(db: Session = Depends(get_db), _=Depends(check_backoffice)):
    return db.query(IngredientType).order_by(IngredientType.name).all()


@router.post("", response_model=IngredientTypeOut, status_code=201)
def create_ingredient_type(body: IngredientTypeCreate, db: Session = Depends(get_db), _=Depends(check_backoffice)):
    existing = db.query(IngredientType).filter(IngredientType.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ingredient type with this name already exists")
    item = IngredientType(name=body.name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{type_id}", response_model=IngredientTypeOut)
def update_ingredient_type(type_id: int, body: IngredientTypeUpdate, db: Session = Depends(get_db), _=Depends(check_backoffice)):
    item = db.get(IngredientType, type_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient type not found")
    if body.name is not None:
        existing = db.query(IngredientType).filter(
            IngredientType.name == body.name,
            IngredientType.id != type_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Another ingredient type already has this name")
        item.name = body.name
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{type_id}", status_code=204)
def delete_ingredient_type(type_id: int, db: Session = Depends(get_db), _=Depends(check_backoffice)):
    item = db.get(IngredientType, type_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ingredient type not found")
    db.delete(item)
    db.commit()

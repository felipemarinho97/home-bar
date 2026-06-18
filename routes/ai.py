from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db
from auth import check_backoffice
from models import InventoryItem, Cocktail
from ai_service import generate_method, generate_tags, suggest_cocktails, filter_duplicates


class CocktailAIData(BaseModel):
    name: str
    base_spirit: Optional[str] = None
    garnish: Optional[str] = None
    ingredients: List[dict] = []
    glasses: List[dict] = []


class MethodResponse(BaseModel):
    method: str


class TagsResponse(BaseModel):
    tags: List[str]


router = APIRouter(prefix="/admin/ai", tags=["admin-ai"])


@router.post("/generate-method", response_model=MethodResponse)
def ai_generate_method(body: CocktailAIData, _=Depends(check_backoffice)):
    try:
        method = generate_method(body.model_dump())
        return MethodResponse(method=method)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-tags", response_model=TagsResponse)
def ai_generate_tags(body: CocktailAIData, _=Depends(check_backoffice)):
    try:
        tags = generate_tags(body.model_dump())
        return TagsResponse(tags=tags)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class SuggestedCocktail(BaseModel):
    name: str
    base_spirit: Optional[str] = None
    ingredients: List[dict] = []
    glass: Optional[str] = None
    method: Optional[str] = None
    garnish: Optional[str] = None
    tags: Optional[List[str]] = []


class SuggestResponse(BaseModel):
    suggestions: List[SuggestedCocktail]


@router.post("/suggest-cocktails", response_model=SuggestResponse)
def ai_suggest_cocktails(db: Session = Depends(get_db), _=Depends(check_backoffice)):
    today = date.today()

    items = db.query(InventoryItem).filter(
        InventoryItem.quantity > 0,
        or_(
            InventoryItem.expiry_date.is_(None),
            InventoryItem.expiry_date > today,
        ),
    ).all()

    if not items:
        raise HTTPException(status_code=400, detail="No items in stock. Add items to inventory first.")

    item_dicts = []
    for item in items:
        d = {
            "name": item.name,
            "category": item.category,
            "ingredient_type": None,
        }
        if item.ingredient_type:
            d["ingredient_type"] = {"name": item.ingredient_type.name}
        item_dicts.append(d)

    try:
        suggestions = suggest_cocktails(item_dicts)

        existing = db.query(Cocktail.name).all()
        existing_names = [row[0] for row in existing]

        if existing_names:
            suggestions = filter_duplicates(suggestions, existing_names)

        return SuggestResponse(suggestions=suggestions)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

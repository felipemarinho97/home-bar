from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from auth import check_backoffice
from ai_service import generate_method, generate_tags


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

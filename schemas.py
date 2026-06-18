from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class IngredientTypeBase(BaseModel):
    name: str

class IngredientTypeCreate(IngredientTypeBase):
    pass

class IngredientTypeUpdate(BaseModel):
    name: Optional[str] = None

class IngredientTypeOut(IngredientTypeBase):
    id: int

    class Config:
        from_attributes = True


class InventoryItemBase(BaseModel):
    name: str
    category: str
    size_ml: Optional[int] = None
    quantity: int = 0
    expiry_date: Optional[date] = None
    photo_url: Optional[str] = None
    ingredient_type_id: Optional[int] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    size_ml: Optional[int] = None
    quantity: Optional[int] = None
    expiry_date: Optional[date] = None
    photo_url: Optional[str] = None
    ingredient_type_id: Optional[int] = None

class InventoryPhotoOut(BaseModel):
    id: int
    inventory_item_id: int
    url: str

    class Config:
        from_attributes = True

class InventoryItemOut(InventoryItemBase):
    id: int
    is_in_stock: bool = False
    is_expired: bool = False
    ingredient_type: Optional[IngredientTypeOut] = None
    photos: List[InventoryPhotoOut] = []

    class Config:
        from_attributes = True


class CocktailIngredientCreate(BaseModel):
    ingredient_type_id: int
    amount: Optional[float] = None
    unit: str = "ml"
    substitute_type_ids: Optional[List[int]] = []

class CocktailIngredientOut(BaseModel):
    id: int
    ingredient_type_id: int
    ingredient_type_name: Optional[str] = None
    amount: Optional[float] = None
    unit: str
    substitute_type_ids: Optional[List[int]] = []

    class Config:
        from_attributes = True

class CocktailGlassCreate(BaseModel):
    inventory_item_id: int

class CocktailGlassOut(BaseModel):
    id: int
    inventory_item_id: int
    inventory_item_name: Optional[str] = None

    class Config:
        from_attributes = True

class CocktailAccessoryCreate(BaseModel):
    inventory_item_id: int

class CocktailAccessoryOut(BaseModel):
    id: int
    inventory_item_id: int
    inventory_item_name: Optional[str] = None

    class Config:
        from_attributes = True

class CocktailPhotoOut(BaseModel):
    id: int
    cocktail_id: int
    url: str
    is_primary: bool

    class Config:
        from_attributes = True

class CocktailCreate(BaseModel):
    name: str
    method: Optional[str] = None
    garnish: Optional[str] = None
    base_spirit: Optional[str] = None
    tags: Optional[List[str]] = []
    ingredients: List[CocktailIngredientCreate] = []
    glasses: List[CocktailGlassCreate] = []
    accessories: List[CocktailAccessoryCreate] = []

class CocktailUpdate(BaseModel):
    name: Optional[str] = None
    method: Optional[str] = None
    garnish: Optional[str] = None
    base_spirit: Optional[str] = None
    tags: Optional[List[str]] = None
    ingredients: Optional[List[CocktailIngredientCreate]] = None
    glasses: Optional[List[CocktailGlassCreate]] = None
    accessories: Optional[List[CocktailAccessoryCreate]] = None

class CocktailOut(BaseModel):
    id: int
    name: str
    method: Optional[str] = None
    garnish: Optional[str] = None
    base_spirit: Optional[str] = None
    tags: Optional[List[str]] = []
    ingredients: List[CocktailIngredientOut] = []
    glasses: List[CocktailGlassOut] = []
    accessories: List[CocktailAccessoryOut] = []
    photos: List[CocktailPhotoOut] = []

    class Config:
        from_attributes = True

class CocktailListOut(BaseModel):
    id: int
    name: str
    base_spirit: Optional[str] = None
    tags: Optional[List[str]] = []
    primary_photo_url: Optional[str] = None

    class Config:
        from_attributes = True

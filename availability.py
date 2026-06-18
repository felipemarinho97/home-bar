import json
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, exists, select

from models import (
    Cocktail, CocktailIngredient, CocktailGlass, CocktailAccessory,
    InventoryItem,
)


def is_cocktail_available(db: Session, cocktail_id: int) -> bool:
    cocktail = db.get(Cocktail, cocktail_id)
    if not cocktail:
        return False

    today = date.today()

    def in_stock_condition():
        return and_(
            InventoryItem.quantity > 0,
            or_(
                InventoryItem.expiry_date.is_(None),
                InventoryItem.expiry_date > today,
            ),
        )

    for ci in cocktail.ingredients:
        sub_ids = ci.substitute_type_ids or []
        matching = db.query(
            exists(
                select(InventoryItem.id)
                .where(
                    in_stock_condition(),
                    InventoryItem.ingredient_type_id.in_([ci.ingredient_type_id] + sub_ids),
                )
            )
        ).scalar()

        if not matching:
            return False

    has_glass = db.query(
        exists(
            select(CocktailGlass.id)
            .join(InventoryItem, InventoryItem.id == CocktailGlass.inventory_item_id)
            .where(
                CocktailGlass.cocktail_id == cocktail_id,
                in_stock_condition(),
            )
        )
    ).scalar()

    if not has_glass:
        return False

    all_accessories_ok = not db.query(
        exists(select(CocktailAccessory.id).where(
            CocktailAccessory.cocktail_id == cocktail_id,
            ~exists(
                select(InventoryItem.id)
                .where(
                    InventoryItem.id == CocktailAccessory.inventory_item_id,
                    in_stock_condition(),
                )
            ),
        ))
    ).scalar()

    return all_accessories_ok


def get_available_cocktail_ids(db: Session) -> set[int]:
    all_cocktails = db.query(Cocktail.id).all()
    available = set()
    for (cid,) in all_cocktails:
        if is_cocktail_available(db, cid):
            available.add(cid)
    return available

from sqlalchemy import (
    Column, Integer, String, Float, Date, Boolean,
    ForeignKey, Text, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class IngredientType(Base):
    __tablename__ = "ingredient_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    inventory_items = relationship("InventoryItem", back_populates="ingredient_type")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    size_ml = Column(Integer, nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    expiry_date = Column(Date, nullable=True)
    photo_url = Column(String, nullable=True)
    ingredient_type_id = Column(Integer, ForeignKey("ingredient_types.id"), nullable=True)

    ingredient_type = relationship("IngredientType", back_populates="inventory_items")
    photos = relationship("InventoryPhoto", back_populates="inventory_item", cascade="all, delete-orphan")

    @property
    def is_in_stock(self) -> bool:
        from datetime import date
        if self.quantity <= 0:
            return False
        if self.expiry_date and self.expiry_date <= date.today():
            return False
        return True

    @property
    def is_expired(self) -> bool:
        from datetime import date
        return self.expiry_date is not None and self.expiry_date <= date.today()


class InventoryPhoto(Base):
    __tablename__ = "inventory_photos"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)

    inventory_item = relationship("InventoryItem", back_populates="photos")


class Cocktail(Base):
    __tablename__ = "cocktails"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    method = Column(Text, nullable=True)
    garnish = Column(String, nullable=True)
    base_spirit = Column(String, nullable=True)
    tags = Column(JSON, nullable=True, default=list)

    ingredients = relationship("CocktailIngredient", back_populates="cocktail", cascade="all, delete-orphan")
    glasses = relationship("CocktailGlass", back_populates="cocktail", cascade="all, delete-orphan")
    accessories = relationship("CocktailAccessory", back_populates="cocktail", cascade="all, delete-orphan")
    photos = relationship("CocktailPhoto", back_populates="cocktail", cascade="all, delete-orphan")


class CocktailIngredient(Base):
    __tablename__ = "cocktail_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    cocktail_id = Column(Integer, ForeignKey("cocktails.id", ondelete="CASCADE"), nullable=False)
    ingredient_type_id = Column(Integer, ForeignKey("ingredient_types.id"), nullable=False)
    amount = Column(Float, nullable=True)
    unit = Column(String, nullable=False, default="ml")
    substitute_type_ids = Column(JSON, nullable=True, default=list)

    cocktail = relationship("Cocktail", back_populates="ingredients")
    ingredient_type = relationship("IngredientType")


class CocktailGlass(Base):
    __tablename__ = "cocktail_glasses"

    id = Column(Integer, primary_key=True, index=True)
    cocktail_id = Column(Integer, ForeignKey("cocktails.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)

    cocktail = relationship("Cocktail", back_populates="glasses")
    inventory_item = relationship("InventoryItem")


class CocktailAccessory(Base):
    __tablename__ = "cocktail_accessories"

    id = Column(Integer, primary_key=True, index=True)
    cocktail_id = Column(Integer, ForeignKey("cocktails.id", ondelete="CASCADE"), nullable=False)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)

    cocktail = relationship("Cocktail", back_populates="accessories")
    inventory_item = relationship("InventoryItem")


class CocktailPhoto(Base):
    __tablename__ = "cocktail_photos"

    id = Column(Integer, primary_key=True, index=True)
    cocktail_id = Column(Integer, ForeignKey("cocktails.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)

    cocktail = relationship("Cocktail", back_populates="photos")

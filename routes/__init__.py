from .public import router as public_router
from .ingredient_types import router as ingredient_types_router
from .inventory import router as inventory_router
from .cocktails import router as cocktails_router
from .ai import router as ai_router

routers = [public_router, ingredient_types_router, inventory_router, cocktails_router, ai_router]

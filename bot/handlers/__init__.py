from handlers.admin import router as admin_router
from handlers.commands import router as commands_router
from handlers.order import router as order_router

__all__ = ["commands_router", "order_router", "admin_router"]

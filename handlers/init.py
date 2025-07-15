from aiogram import Router

from .admin_init import router as admin_init_router
from .categories import router as categories_router
from .products import router as products_router
from .back import router as back_router
from .config_handlers import router as config_router
from .admin_photos import router as admin_photos_router
from .sos import router as sos_router

router = Router()
router.include_router(admin_init_router)
router.include_router(categories_router)
router.include_router(products_router)
router.include_router(back_router)
router.include_router(config_router)
router.include_router(admin_photos_router)
router.include_router(sos_router)

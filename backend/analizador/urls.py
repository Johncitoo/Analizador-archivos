from rest_framework.routers import DefaultRouter

from .views import ArchivoAnalizadoViewSet

router = DefaultRouter()
router.register("archivos", ArchivoAnalizadoViewSet, basename="archivo")

urlpatterns = router.urls

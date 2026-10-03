from rest_framework.routers import DefaultRouter

from .views import ArchivoAnalizadoViewSet

# El router crea solo las rutas del ViewSet:
#   /archivos/              GET (lista) y POST (subir)
#   /archivos/<id>/         GET (detalle)
#   /archivos/estadisticas/ GET
router = DefaultRouter()
router.register("archivos", ArchivoAnalizadoViewSet, basename="archivo")

urlpatterns = router.urls

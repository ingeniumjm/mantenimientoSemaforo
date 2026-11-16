from django.urls import path
from .views import (InterseccionesView, DevolverActualizarEliminarInterseccionView,
                    SemaforosView, DevolverActualizarEliminarSemaforoView,
                    ReportesView, DevolverActualizarEliminarReporteView,
                    MantenimientosView, DevolverActualizarEliminarMantenimientoView,
                    crearUrlParaSubirArchivo,
                    crearMedia,
                    registroUsuario,
                    perfilUsuario,
                    loginManual)

from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    # as_view convi erte la vista creada con DRF a una vista que la pueda entender Django y pueda servirla
    path('intersecciones', InterseccionesView.as_view()),
    # si le vamos a poner otro parametro que no se llame 'id' entonces el looup_field indicando el mismo nombre
    path('interseccion/<id>',DevolverActualizarEliminarInterseccionView.as_view()),
    path('semaforos', SemaforosView.as_view()),
    path('semaforo/<id>', DevolverActualizarEliminarSemaforoView.as_view()),
    path('reportes', ReportesView.as_view()),
    path('reporte/<id>', DevolverActualizarEliminarReporteView.as_view()),
    path('mantenimientos', MantenimientosView.as_view()),
    path('mantenimiento/<id>', DevolverActualizarEliminarMantenimientoView.as_view()),
    path('generar-url',crearUrlParaSubirArchivo),
    path('media',crearMedia),
    path('registro', registroUsuario),
    path('perfil',perfilUsuario),
    path('login-libreria', TokenObtainPairView.as_view()),
    path('login', loginManual),
]

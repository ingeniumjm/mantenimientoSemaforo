from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
# se usa para capturar los filtros por id (UUID) con formato invalido
from django.core.exceptions import ValidationError
# nos brindara el proceso automatico de una determinada operacion
from rest_framework.generics import (CreateAPIView, # crear
                                    DestroyAPIView, # eliminar
                                    ListAPIView, # devolver todos
                                    ListCreateAPIView, # devolver todos y creacion
                                    RetrieveAPIView, # devolver solo uno
                                    RetrieveDestroyAPIView, # devolver solo uno y ademas poder eliminar
                                    RetrieveUpdateAPIView, # eliminar y ademas poder actualizar
                                    RetrieveUpdateDestroyAPIView, # devolver solo uno y ademas poder actualizarlo o eliminarlo
                                    UpdateAPIView) # actualizar

from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import (
                                        IsAuthenticated, # Obligara a que si no hay una token y esta sea valida no permitira ingresar al endpoint
                                        IsAdminUser, # Validara que el usuario que quiera consultar sea is_superuser y sino no podra continuar
                                        IsAuthenticatedOrReadOnly, # Validara que si el metodo es GET normal podra continuar pero si no es GET la JWT sera obligatoria y tiene que ser valida
                                        AllowAny # Permitira que cualquiera pueda consultar cualquier metodo sin la necesidad de enviar una JWT, esto es el valor predeterminado
                                        )

from .models import Interseccion, Semaforo, ReporteFalla, Mantenimiento,Media,Usuario
from .serializers import (InterseccionSerializer,
                          SemaforoSerializer,
                          ReporteFallaSerializer,
                          MantenimientoSerializer,GenerarUrlAWSSerializer,MediaSerializer,
                          UsuarioSerializer,LoginSerializer)
from boto3 import client 
from os import getenv
from urllib.parse import unquote
from uuid import uuid4
from rest_framework_simplejwt.tokens import RefreshToken


class InterseccionesView(APIView):
    # al usar una APIView es muy similar al Resource de flask-restful en el cual se puede colocar los metodos http como metos de la clase

    def get(self,request):
        # SELECT * FROM interseciones WRERE eliminado = FALSE
        intersecciones = Interseccion.objects.filter(eliminado=False).all()
        # Si se pasa un conjunto de instancias estamos en la obligacion de colocar many=True para que el serializador pueda iterar y transforma cada una de las instancias
        dataSerializada = InterseccionSerializer(instance=intersecciones, many=True)
        # en django no se puede retornar directamente un diccionario sino que tiene que crearse la instancia de la clase Response
        return Response({
            "content": dataSerializada.data
        })
    def post(self,request:Request):
        print(request.data)
        serializador =InterseccionSerializer(data=request.data)

        if serializador.is_valid():
            print(serializador.validated_data)
            # El serializado al estar vinculado con un modelo internamente jala la forma de guardarlo en la bd con el metodo save
            serializador.save()
            return Response(data={
                "message":"Interseccion creada exitosamente",
                "content": serializador.data
            },status=status.HTTP_201_CREATED
            )


        else:
            return Response(data={
                "message": "Error al crear la interseccion",
                "content": serializador.errors
            }, status=status.HTTP_400_BAD_REQUEST)

# GET | PUT | DELETE
# Si mi vista generica deja de ser generica entonces la puedo convertir en un viewset en el cual
# post > create
# get > retrieve
# get > list (si se va a retornar varios registros)
# put > update
# delete > destroy
# patch > partial_update
class DevolverActualizarEliminarInterseccionView(RetrieveUpdateDestroyAPIView):
    # SELECT * FROM categorias
    # Es la forma en la cual la vista se comunicara con la bd
    queryset = Interseccion.objects.all()
    
    # Es la forma en la cual la vista se comunicara con la data enviada por el cliente y la data enviada hacia el cliente
    serializer_class = InterseccionSerializer
    
    # lookup_field sirve para indicar el parametro que se usara para identificar la PK (llave primaria)
    lookup_field = 'id'

    # Devolver solo una categoria
    def retrieve(self, request, id):
        # al usar el retrieve | update | destroy siempre lo enviara como 2do parametro
        interseccionEncontrada = Interseccion.objects.filter(eliminado=False, id = id).first()
        
        if not interseccionEncontrada:
            return Response(data={
                "message":"Interseccion no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        dataSerializada = self.serializer_class(instance= interseccionEncontrada)

        return Response(data={
            "content": dataSerializada.data
        })

    def update(self, request, id):
        interseccionEncontrada = Interseccion.objects.filter(eliminado=False, id = id).first()
        if not interseccionEncontrada:
            return Response(data={
                "message":"Interseccion no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        serializador = self.serializer_class(data=request.data)
        if serializador.is_valid():
            serializador.update(interseccionEncontrada,serializador.validated_data)

            return Response(data={
                "message":"Interseccion actualizada exitosamente",
                "content": serializador.data
            })

        else:
            return Response(data={
                "message":"Error al actualizar la interseccion",
                "content": serializador.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, id):
        interseccionEncontrada = Interseccion.objects.filter(eliminado=False, id = id).first()
        if not interseccionEncontrada:
            return Response(data={
                "message":"Intersecion no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        # Regla de negocio: no se puede eliminar una interseccion si tiene semaforos
        if interseccionEncontrada.semaforos.filter(eliminado=False).exists():
            return Response(data={
                "message": "No se puede eliminar la interseccion porque tiene semaforos"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cambiamos el estado de eliminado a verdadero
        interseccionEncontrada.eliminado = True
        interseccionEncontrada.save()

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class SemaforosView(APIView):

    def get(self, request):
        # SELECT * FROM semaforos WHERE eliminado = FALSE
        semaforos = Semaforo.objects.filter(eliminado=False).all()
        # filtros por query params: ?interseccion=<uuid>&estado=<estado>
        interseccion_id = request.query_params.get('interseccion')
        estado = request.query_params.get('estado')
        if interseccion_id:
            try:
                semaforos = semaforos.filter(interseccion_id=interseccion_id)
            except (ValidationError, ValueError):
                return Response(data={
                    "message": "Identificador de interseccion invalido"
                }, status=status.HTTP_400_BAD_REQUEST)
        if estado:
            semaforos = semaforos.filter(estado=estado)
        dataSerializada = SemaforoSerializer(instance=semaforos, many=True)
        return Response({
            "content": dataSerializada.data
        })

    def post(self, request: Request):
        serializador = SemaforoSerializer(data=request.data)

        if serializador.is_valid():
            serializador.save()
            return Response(data={
                "message": "Semaforo creado exitosamente",
                "content": serializador.data
            }, status=status.HTTP_201_CREATED)

        else:
            return Response(data={
                "message": "Error al crear el semaforo",
                "content": serializador.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class DevolverActualizarEliminarSemaforoView(RetrieveUpdateDestroyAPIView):
    queryset = Semaforo.objects.all()
    serializer_class = SemaforoSerializer
    lookup_field = 'id'

    def retrieve(self, request, id):
        semaforoEncontrado = Semaforo.objects.filter(eliminado=False, id=id).first()

        if not semaforoEncontrado:
            return Response(data={
                "message": "Semaforo no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        dataSerializada = self.serializer_class(instance=semaforoEncontrado)

        return Response(data={
            "content": dataSerializada.data
        })

    def update(self, request, id):
        semaforoEncontrado = Semaforo.objects.filter(eliminado=False, id=id).first()
        if not semaforoEncontrado:
            return Response(data={
                "message": "Semaforo no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        serializador = self.serializer_class(data=request.data)
        if serializador.is_valid():
            serializador.update(semaforoEncontrado, serializador.validated_data)

            return Response(data={
                "message": "Semaforo actualizado exitosamente",
                "content": serializador.data
            })

        else:
            return Response(data={
                "message": "Error al actualizar el semaforo",
                "content": serializador.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, id):
        semaforoEncontrado = Semaforo.objects.filter(eliminado=False, id=id).first()
        if not semaforoEncontrado:
            return Response(data={
                "message": "Semaforo no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        # Regla de negocio: no se puede eliminar un semaforo si tiene reportes
        if semaforoEncontrado.reportes.filter(eliminado=False).exists():
            return Response(data={
                "message": "No se puede eliminar el semaforo porque tiene reportes"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cambiamos el estado de eliminado a verdadero
        semaforoEncontrado.eliminado = True
        semaforoEncontrado.save()

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class ReportesView(APIView):

    def get(self, request):
        # SELECT * FROM reportesFallas WHERE eliminado = FALSE
        reportes = ReporteFalla.objects.filter(eliminado=False).all()
        # filtros por query params: ?semaforo=<uuid>&estado=<estado>
        # el filtro por semaforo sirve como historial de reportes de un semaforo
        semaforo_id = request.query_params.get('semaforo')
        estado = request.query_params.get('estado')
        if semaforo_id:
            try:
                reportes = reportes.filter(semaforo_id=semaforo_id)
            except (ValidationError, ValueError):
                return Response(data={
                    "message": "Identificador de semaforo invalido"
                }, status=status.HTTP_400_BAD_REQUEST)
        if estado:
            reportes = reportes.filter(estado=estado)
        dataSerializada = ReporteFallaSerializer(instance=reportes, many=True)
        return Response({
            "content": dataSerializada.data
        })

    def post(self, request: Request):
        serializador = ReporteFallaSerializer(data=request.data)

        if serializador.is_valid():
            # un reporte nuevo no puede tener mantenimientos, por eso no se puede crear como resuelto
            if serializador.validated_data.get('estado', 'pendiente') == 'resuelto':
                return Response(data={
                    "message": "No se puede crear un reporte como resuelto sin mantenimientos"
                }, status=status.HTTP_400_BAD_REQUEST)
            serializador.save()
            return Response(data={
                "message": "Reporte creado exitosamente",
                "content": serializador.data
            }, status=status.HTTP_201_CREATED)

        else:
            return Response(data={
                "message": "Error al crear el reporte",
                "content": serializador.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class DevolverActualizarEliminarReporteView(RetrieveUpdateDestroyAPIView):
    queryset = ReporteFalla.objects.all()
    serializer_class = ReporteFallaSerializer
    lookup_field = 'id'

    def retrieve(self, request, id):
        reporteEncontrado = ReporteFalla.objects.filter(eliminado=False, id=id).first()

        if not reporteEncontrado:
            return Response(data={
                "message": "Reporte no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        dataSerializada = self.serializer_class(instance=reporteEncontrado)

        return Response(data={
            "content": dataSerializada.data
        })

    def update(self, request, id):
        reporteEncontrado = ReporteFalla.objects.filter(eliminado=False, id=id).first()
        if not reporteEncontrado:
            return Response(data={
                "message": "Reporte no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        serializador = self.serializer_class(data=request.data)
        if serializador.is_valid():
            # Regla de negocio: no se puede marcar como resuelto sin al menos un mantenimiento
            estado_nuevo = serializador.validated_data.get('estado', reporteEncontrado.estado)
            if estado_nuevo == 'resuelto' and not reporteEncontrado.mantenimientos.filter(eliminado=False).exists():
                return Response(data={
                    "message": "No se puede marcar el reporte como resuelto sin al menos un mantenimiento"
                }, status=status.HTTP_400_BAD_REQUEST)

            serializador.update(reporteEncontrado, serializador.validated_data)

            return Response(data={
                "message": "Reporte actualizado exitosamente",
                "content": serializador.data
            })

        else:
            return Response(data={
                "message": "Error al actualizar el reporte",
                "content": serializador.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, id):
        reporteEncontrado = ReporteFalla.objects.filter(eliminado=False, id=id).first()
        if not reporteEncontrado:
            return Response(data={
                "message": "Reporte no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        # Regla de negocio: no se puede eliminar un reporte si tiene mantenimientos
        if reporteEncontrado.mantenimientos.filter(eliminado=False).exists():
            return Response(data={
                "message": "No se puede eliminar el reporte porque tiene mantenimientos"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cambiamos el estado de eliminado a verdadero
        reporteEncontrado.eliminado = True
        reporteEncontrado.save()

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


class MantenimientosView(APIView):

    def get(self, request):
        # SELECT * FROM mantenimientos WHERE eliminado = FALSE
        mantenimientos = Mantenimiento.objects.filter(eliminado=False).all()
        # filtro por query param: ?reporte=<uuid>
        reporte_id = request.query_params.get('reporte')
        if reporte_id:
            try:
                mantenimientos = mantenimientos.filter(reporte_id=reporte_id)
            except (ValidationError, ValueError):
                return Response(data={
                    "message": "Identificador de reporte invalido"
                }, status=status.HTTP_400_BAD_REQUEST)
        dataSerializada = MantenimientoSerializer(instance=mantenimientos, many=True)
        return Response({
            "content": dataSerializada.data
        })

    def post(self, request: Request):
        serializador = MantenimientoSerializer(data=request.data)

        if serializador.is_valid():
            serializador.save()
            return Response(data={
                "message": "Mantenimiento creado exitosamente",
                "content": serializador.data
            }, status=status.HTTP_201_CREATED)

        else:
            return Response(data={
                "message": "Error al crear el mantenimiento",
                "content": serializador.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class DevolverActualizarEliminarMantenimientoView(RetrieveUpdateDestroyAPIView):
    queryset = Mantenimiento.objects.all()
    serializer_class = MantenimientoSerializer
    lookup_field = 'id'

    def retrieve(self, request, id):
        mantenimientoEncontrado = Mantenimiento.objects.filter(eliminado=False, id=id).first()

        if not mantenimientoEncontrado:
            return Response(data={
                "message": "Mantenimiento no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        dataSerializada = self.serializer_class(instance=mantenimientoEncontrado)

        return Response(data={
            "content": dataSerializada.data
        })

    def update(self, request, id):
        mantenimientoEncontrado = Mantenimiento.objects.filter(eliminado=False, id=id).first()
        if not mantenimientoEncontrado:
            return Response(data={
                "message": "Mantenimiento no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        serializador = self.serializer_class(data=request.data)
        if serializador.is_valid():
            serializador.update(mantenimientoEncontrado, serializador.validated_data)

            return Response(data={
                "message": "Mantenimiento actualizado exitosamente",
                "content": serializador.data
            })

        else:
            return Response(data={
                "message": "Error al actualizar el mantenimiento",
                "content": serializador.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, id):
        mantenimientoEncontrado = Mantenimiento.objects.filter(eliminado=False, id=id).first()
        if not mantenimientoEncontrado:
            return Response(data={
                "message": "Mantenimiento no existe"
            }, status=status.HTTP_404_NOT_FOUND)

        # Cambiamos el estado de eliminado a verdadero
        mantenimientoEncontrado.eliminado = True
        mantenimientoEncontrado.save()

        return Response(data=None, status=status.HTTP_204_NO_CONTENT)

@api_view(http_method_names=['POST'])

def crearUrlParaSubirArchivo(request:Request):
    # https://docs.aws.amazon.com/boto3/latest/guide/def crearUrlParaSubirArchivo(request:Request):
    # https://docs.aws.amazon.com/boto3/latest/guide/s3-presigned-urls.html
    # https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/generate_presigned_url.html
    serializador = GenerarUrlAWSSerializer(data=request.data)
    if serializador.is_valid():
        fileName = serializador.validated_data.get("fileName")
        ext = serializador.validated_data.get("ext")
        contentType = serializador.validated_data.get("contentType")
        folder = serializador.validated_data.get("folder", "/")
        
        s3 = client('s3')
        nombre = str(uuid4()) + '_' + fileName
        
        url = s3.generate_presigned_url(
            ClientMethod = 'put_object',
            Params={
                "Bucket":getenv('BUCKET_NAME'),
                "Key": folder + nombre +'.'+ ext,
                "ContentType":contentType
            },
            ExpiresIn=150
        )

        return Response(data={
            "content": {
                "url":unquote(url),
                "nombre": nombre,
                "ext": ext,
                "mimeType": contentType,
                "ruta": folder
            }
        })
    else:
        return Response(data={
            "message":"Error al generar la URL",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(http_method_names=['POST'])
def crearMedia(request:Request):
    serializador = MediaSerializer(data= request.data)
    if serializador.is_valid():
        serializador.save()

        return Response(data={
            "message":"Archivo creado exitosamente",
            "content": {
                "id":serializador.data.get("id")
            }
        }, status=status.HTTP_201_CREATED)

    else:
        return Response(data={
            "message":"Error al crear el archivo",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST) 

@api_view(http_method_names=['POST'])
def registroUsuario(request: Request):
    serializador = UsuarioSerializer(data=request.data)

    if serializador.is_valid():

        nombre = serializador.validated_data.get('nombre')
        apellidos = serializador.validated_data.get('apellidos')
        correo = serializador.validated_data.get('correo')
        sexo = serializador.validated_data.get('sexo')
        password = serializador.validated_data.get('password')
        nuevoUsuario = Usuario(nombre=nombre,apellidos=apellidos,correo=correo,sexo=sexo)

        # EL modelo auth_user tiene un metodo set_password que genera el hash de la contraseña y lo guarda en el campo de password
        nuevoUsuario.set_password(password)
        nuevoUsuario.save()

        return Response(data={
            "message":"Usuario registrado exitosamente"
        },status=status.HTTP_201_CREATED)

    else:
        return Response(data={
            "message":"Error al crear el usuario",
            "content":serializador.errors
        }, status = status.HTTP_400_BAD_REQUEST)

@api_view(http_method_names=['POST'])
def loginManual(request:Request):
    serializador = LoginSerializer(data=request.data)

    if serializador.is_valid():
        correo = serializador.validated_data.get('correo')
        password = serializador.validated_data.get('password')
        usuarioEncontrado = Usuario.objects.filter(correo = correo).first()
        # Aca se deberian agregar mas filtros como si esta habilitado, si tiene los permisos necesarios, etc.
        if not usuarioEncontrado:
            return Response(data={
                "message":"El usuario no existe"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Este metodo es un metodo propio del auth_user que al heredar en la clase de usuario podemos utilizarlo
        esLaPassword = usuarioEncontrado.check_password(password)
        if esLaPassword:
            # Para generar tokens necesito llamar a la clase RefreshToken y esta me retornara token de acceso y de refresco para la sesion
            token = RefreshToken.for_user(usuarioEncontrado)
            return Response(data={
                "content": {
                    "access": str(token.access_token),
                    "refresh": str(token),
                }
            })
        else:
            return Response(data={
                "message":"Credenciales invalidas"
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={
            "message":"error al hacer el login",
            "content":serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# DRF tiene un formato de poder requerir o no la autenticacion en los metodos que sea necesario mediante el decorador permission_clases o dentro de las vistas usando el atributo permissions_classes
@api_view(http_method_names=['GET'])
@permission_classes([IsAuthenticated])
def perfilUsuario(request: Request):
    usuarioActual = request.user
    serializador = UsuarioSerializer(instance= usuarioActual)
    return Response(data={
        "content":serializador.data
    })                    
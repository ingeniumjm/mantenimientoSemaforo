from rest_framework.serializers import ModelSerializer,Serializer
from rest_framework import serializers
from .models import Interseccion, Semaforo, ReporteFalla, Mantenimiento,Media,Usuario

# https://www.django-rest-framework.org/api-guide/serializers/#modelserializer
class InterseccionSerializer(ModelSerializer):

    class Meta:
        model = Interseccion
        # siempre debemos colocar una de los siguientes atributos
        # fields | exclude
        # sirve para indicar al serializador que campos (atributos) vamos a utilizar para hacer la validacion
        # fields = ["id", "nombre"]
        # Pero si se va a utilizar todos los campos del modelo
        # fields = "__all__"
        # Todos los campos menos el nombre
        exclude = ["eliminado"]
        # el id lo genera el servidor, por eso se marca como solo lectura
        extra_kwargs = {"id": {"read_only": True}}

class SemaforoSerializer(ModelSerializer):

    class Meta:
        model = Semaforo
        # todos los campos del modelo menos eliminado
        exclude = ["eliminado"]
        # los ids de relacion se envian y reciben de forma plana (solo su UUID)
        # el id lo genera el servidor, por eso se marca como solo lectura
        extra_kwargs = {"id": {"read_only": True}}

class ReporteFallaSerializer(ModelSerializer):

    class Meta:
        model = ReporteFalla
        # todos los campos del modelo menos eliminado
        exclude = ["eliminado"]
        # los ids de relacion se envian y reciben de forma plana (solo su UUID)
        # el id lo genera el servidor, por eso se marca como solo lectura
        extra_kwargs = {"id": {"read_only": True}}

class MantenimientoSerializer(ModelSerializer):

    class Meta:
        model = Mantenimiento
        # todos los campos del modelo menos eliminado
        exclude = ["eliminado"]
        # los ids de relacion se envian y reciben de forma plana (solo su UUID)
        # el id lo genera el servidor, por eso se marca como solo lectura
        extra_kwargs = {"id": {"read_only": True}}

class GenerarUrlAWSSerializer(Serializer):
    # Crearemos manualmente todas las columnas a validar
    # https://www.iana.org/assignments/media-types
    # https://www.django-rest-framework.org/api-guide/fields/
    contentTypeValidas = ["image/jpeg", "image/png", "application/pdf"]
    extensionesValidas = ["png","jpg", "jpeg", "pdf"]

    # trim_whitespace  > Remueve los espacios al comienzo y al final 
    fileName = serializers.CharField(trim_whitespace=True, max_length=100, required=True)
    ext = serializers.ChoiceField(choices=extensionesValidas, error_messages={
        "invalid_choise":"Ext invalida, use 'image/jpeg', 'image/png' o 'application/pdf'"
        }, required=True)
    contentType = serializers.ChoiceField(choices=contentTypeValidas, required=True)
    # El tamaño maximo permitido y este debera ser enviado en bytes
    # 1 byte x 1024 > 1 kb x 1024 > 1 mb x 1024 > 1 gb x 1024 > 1 tb
    # El valor maximo 10mb y el minimo 5kb
    size = serializers.FloatField(max_value=10*1024*1024, min_value = 5*1024, required=True)
    folder = serializers.CharField(required=False)   

class MediaSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'      

class UsuarioSerializer(ModelSerializer):
    class Meta:
        model = Usuario
        exclude = ['is_staff','is_superuser', 'is_active', 'user_permissions', 'last_login', 'groups']

        # Si queremos condicionar un atributo a que sea solo lectura o solo escritura entonces se recomienda usar los extra_kwargs
        extra_kwargs = {
            'password':{
                'write_only':True
            }
        }

class LoginSerializer(Serializer):
    correo = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)        
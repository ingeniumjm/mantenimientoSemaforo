from django.db import models
from uuid import uuid4
# AbstractUser te permite agregar nuevas columnas a la configuracion inicial del auth_user (name, last_name, password, email, is_superuser, is_staff, is_active, last_login)
# AbstractBaseUser te permite modificar por completo las columnas y propiedades el auth_user
# PermissionsMixin sirve para configurar como estara relacionada la nueva tabla de auth_user con relacion a los permisos (auth_groups, auth_user_permissions)
# BaseUserManager es el administrador sobre algunos comandos de la terminal como por ejemplo cuando se manda a a llamar al createsuperuser este manejara ese comportamiento
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class Interseccion (models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    nombre = models.CharField(max_length=100, null=False)
    distrito = models.CharField(max_length=100, null=False)
    direccion = models.CharField(max_length=100, null=False)
    habilitado = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = 'intersecciones'

    def __str__(self):
        return self.nombre

class Semaforo(models.Model):

    TIPO_CHOICES = [
        ('vehicular', 'Vehicular'),
        ('peatonal', 'Peatonal'),
    ]
    ESTADO_CHOICES = [
        ('operativo', 'Operativo'),
        ('con_falla', 'Con falla'),
        ('fuera_de_servicio', 'Fuera de servicio'),
    ]

    id = models.UUIDField(default=uuid4, primary_key=True)
    codigo = models.CharField(max_length=100, null=False, unique=True)
    tipo = models.CharField(max_length=20, null=False,choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, null=False,choices=ESTADO_CHOICES, default='operativo')
    # on_delete=models.CASCADE quiere decir si se borra una interseccion se borra todos los semaforos de esa interseccion
    interseccion = models.ForeignKey(to=Interseccion, on_delete=models.CASCADE, related_name='semaforos', db_column='interseccion_id')
    habilitado = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)
    class Meta:
        db_table = 'semaforos'

    def __str__(self):
        return self.codigo

class ReporteFalla(models.Model):

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_atencion', 'En atención'),
        ('resuelto', 'Resuelto'),
    ]
    id = models.UUIDField(default=uuid4, primary_key=True)
    semaforo = models.ForeignKey(to=Semaforo, on_delete=models.CASCADE, related_name='reportes')
    descripcion = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    habilitado = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)
    class Meta:
        db_table = 'reportesFallas'

    def __str__(self):
        return f'Reporte {self.id} - {self.semaforo.codigo}'

class Mantenimiento(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    reporte = models.ForeignKey(to=ReporteFalla, on_delete=models.CASCADE, related_name='mantenimientos')
    descripcion_trabajo = models.TextField()
    responsable = models.CharField(max_length=150)
    fecha_mantenimiento = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)
    habilitado = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)
    class Meta:
        db_table = 'mantenimientos'

    def __str__(self):
        return f'Mantenimiento {self.id} - {self.reporte.semaforo.codigo}'
class Media(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True)
    nombre = models.CharField(max_length=100, null=False)
    ext = models.CharField(max_length=100, null=False)
    ruta = models.CharField(max_length=200, null=False)
    mimeType = models.CharField(db_column='mime_type', max_length=100, null=False)
    habilitado = models.BooleanField(default=True) 
    eliminado  = models.BooleanField(default=False)

    class Meta:
        db_table = 'medias'

class ManejadorUsuario(BaseUserManager):
    # Este sera el metodo que se llamara cuando en la terminal se quiera crear un superusuario (py manage.py createsuperuser)
    def create_superuser(self, nombre, correo,password):
        # Validamos si el correo no esta vacio
        if not correo or len(correo) == 0:
            raise ValueError("El correo es obligatorio")

        # normalize_email quita los espacios a los laterales y pone todo en minusculas y remueve caracteres especiales como tildes u otros 
        # EdUaRdO@gmail.com > eduardo@gmail.com
        correoNormalizado = self.normalize_email(correo)

        # con esto creamos la nueva instancia (registro) del usuario
        nuevoUsuario = self.model(correo = correoNormalizado, nombre = nombre)
        # set_password se encarga de generar el hash del password y guardarlo en la columna password
        nuevoUsuario.set_password(password)

        # Ahora modificamos los campos que usa el panel administrativo
        # is_superuser | is_staff
        nuevoUsuario.is_superuser = True
        nuevoUsuario.is_staff = True

        # Guardamos el registro en la bd
        nuevoUsuario.save()

# Vamos a usar el auth_user dentro de usuario
# Cambiamos la herencia de modelo comun y corriente al modelo encargado del auth_user
# Y tambien heredamos la forma en la cual se manejara los permisos del panel administrativo para el auth_user  
class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid4)
    nombre = models.TextField()
    apellidos = models.TextField(null=True)
    sexo = models.TextField()
    correo = models.TextField(unique=True)
    password = models.TextField()

    # Si aun queremos usar el panel administrativo nos vemos en la obligacion de agregar estos atributos
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Este atributo servira para indicar cual es el atributo que usare para poder identificar al usuario al momento de hacer login en el panel administrativo
    USERNAME_FIELD = 'correo'

    # Este atributo sirve para indicar que cuando se quiera crear un superusuario en la terminal que campos se deberia de solicitar 
    # No se debe de colocar el mismo atributo que el username_field porque ya esta implicito y asi mismo el password SIEMPRE sera solicitado
    REQUIRED_FIELDS = ['nombre']

    # Modificamos el comportamiento de nuestro auth_user y le asignamos la forma de creacion de un superusuario en la terminal
    objects = ManejadorUsuario()

    class Meta:
        db_table='usuarios'
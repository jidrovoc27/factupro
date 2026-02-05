import uuid
from django.db import models
from django.db.models.query_utils import Q
from django.contrib.auth.models import User, Group
from base.modelobase import ModeloBase

class CategoriaModulo(ModeloBase):
    orden = models.IntegerField(default=0, verbose_name='Orden')
    nombre = models.CharField(default='', max_length=1000, verbose_name=u'Nombre')
    icono = models.CharField(default='', max_length=100, verbose_name=u'Icono')

    def mismodulos(self, persona, ids_modulos_favoritos):
        ids_modulos_favoritos = [] if not ids_modulos_favoritos else ids_modulos_favoritos
        misgrupos = ModuloGrupo.objects.filter(grupos__in=persona.usuario.groups.all()).values_list('id', flat=True)
        return self.modulo_set.exclude(id__in=ids_modulos_favoritos).values('id', 'icono', 'nombre','descripcion', 'url').filter(Q(modulogrupo__in=misgrupos), activo=True, sagest=True).distinct().order_by('orden')

class Modulo(ModeloBase):
    categoria = models.ManyToManyField(CategoriaModulo, verbose_name=u'Categoria')
    orden = models.IntegerField(default=0, verbose_name='Orden')
    url = models.CharField(default='', max_length=100, verbose_name=u'URL')
    nombre = models.CharField(default='', max_length=1000, verbose_name=u'Nombre')
    icono = models.CharField(default='', max_length=100, verbose_name=u'Icono')
    descripcion = models.CharField(default='', max_length=200, verbose_name=u'Descripción')
    activo = models.BooleanField(default=True, verbose_name=u'Activo')

class ModuloGrupo(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u' Nombre')
    descripcion = models.CharField(default='', max_length=200, verbose_name=u'Descripción')
    modulos = models.ManyToManyField(Modulo, verbose_name=u'Modulos')
    grupos = models.ManyToManyField(Group, verbose_name=u'Grupos')
    prioridad = models.IntegerField(default=0, verbose_name=u'Prioridad')

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u'Grupo de modulos'
        verbose_name_plural = u"Grupos de modulos"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def modulos_activos(self):
        return self.modulos.filter(activo=True)

    def modules(self):
        return self.modulos.all()

    def groups(self):
        return self.grupos.all()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().capitalize()
        self.descripcion = self.descripcion.strip().capitalize()
        super(ModuloGrupo, self).save(*args, **kwargs)

class Persona(ModeloBase):
    """
    Identidad real (natural/jurídica). NO depende de empresa.
    Sirve para: clientes, proveedores, transportistas, representantes, etc.
    """
    TIPO_PERSONA = (
        (1, "NATURAL"),
        (2, "JURIDICA"),
        (3, "EXTRANJERA"),
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="personas", blank=True, null=True)
    tipo_persona = models.PositiveSmallIntegerField(choices=TIPO_PERSONA, default=1)

    identificacion = models.CharField(max_length=20, unique=True, blank=False, null=False)
    razon_social = models.CharField(max_length=255, blank=False, null=False)

    nombres = models.CharField(max_length=255, blank=True, null=True)
    apellidos = models.CharField(max_length=255, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)

    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.razon_social} - {self.identificacion}"

    def mi_perfiladministrativo(self):
        return self.perfilusuario_set.filter(status=True, administrativo__isnull=False).first()

class Administrativo(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, verbose_name=u"Persona")
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

class PerfilUsuario(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT)
    administrativo = models.ForeignKey(Administrativo, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u'Administrativo')


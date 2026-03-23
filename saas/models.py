import uuid
from django.db import models
from django.db.models.query_utils import Q
from django.contrib.auth.models import User, Group
from base.modelobase import ModeloBase
from base.choices import TIPO_IDENTIFICACION

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
    tipo_identificacion = models.PositiveSmallIntegerField(choices=TIPO_IDENTIFICACION, default=1)
    identificacion = models.CharField(max_length=20, unique=True, blank=False, null=False)
    razon_social = models.CharField(max_length=255, blank=False, null=False)

    nombres = models.CharField(max_length=255, blank=True, null=True)
    primerapellido = models.CharField(max_length=255, blank=True, null=True)
    segundoapellido = models.CharField(max_length=255, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)

    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres_completos()}"

    def nombres_completos(self):
        return f"{self.nombres} {self.primerapellido} {self.segundoapellido}"

    def nombres_completos_inverso(self):
        return f"{self.primerapellido} {self.segundoapellido} {self.nombres}"

    def mi_perfiladministrativo(self):
        return self.perfilusuario_set.filter(status=True, administrativo__isnull=False).first()

    def mi_perfilprofesional(self):
        return self.perfilusuario_set.filter(status=True, profesional__isnull=False).first()

    def mi_perfil(self):
        return self.perfilusuario_set.filter(status=True).first()

    def get_administrativo(self):
        return self.administrativo_set.filter(status=True).first()

    def get_profesionalsalud(self):
        return self.profesionalsalud_set.filter(status=True).first()

    def create_administrativo(self, request):
        administrativo_ = Administrativo(persona=self)
        administrativo_.save(request)
        return administrativo_

    def create_profesional(self, request):
        profesional_ = ProfesionalSalud(persona=self)
        profesional_.save(request)
        return profesional_

    @staticmethod
    def flexbox_query(q, extra=None):
        if ' ' in q:
            s = q.split(" ")
            if extra:
                return eval(
                    'Persona.objects.filter(Q(primerapellido__contains="%s") & Q(segundoapellido__contains="%s")).filter(%s).distinct()[:25]' % (
                    s[0], s[1], extra))
            return Persona.objects.filter(Q(primerapellido__contains=s[0]) & Q(segundoapellido__contains=s[1])).distinct()[:25]
        if extra:
            return eval(
                'Persona.objects.filter(Q(nombres__contains="%s") | Q(primerapellido__contains="%s") | Q(segundoapellido__contains="%s") | Q(identificacion__contains="%s")).filter(%s).distinct()[:25]' % (
                q, q, q, q, extra))
        return Persona.objects.filter(Q(nombres__contains=q) | Q(primerapellido__contains=q) | Q(segundoapellido__contains=q) | Q(identificacion__contains=q)).distinct()[:25]

    def flexbox_repr(self):
        return self.identificacion + " - " + self.nombres_completos_inverso() + " - " + self.id.__str__()

    def create_perfil_administrativo(self, request):
        miperfil_ = self.mi_perfil()
        administrativo_ = self.get_administrativo()
        if not administrativo_:
            administrativo_ = self.create_administrativo(request)
        if not miperfil_:
            miperfil_ = PerfilUsuario(persona=self, administrativo=administrativo_)
            miperfil_.save(request)
            return miperfil_
        if not miperfil_.administrativo:
            miperfil_.administrativo = administrativo_
            miperfil_.save(request)
            return miperfil_

    def create_perfil_profesional(self, request):
        miperfil_ = self.mi_perfil()
        profesional_ = self.get_profesionalsalud()
        if not profesional_:
            profesional_ = self.create_profesional(request)
        if not miperfil_:
            miperfil_ = PerfilUsuario(persona=self, profesional=profesional_)
            miperfil_.save(request)
            return miperfil_
        if not miperfil_.profesional:
            miperfil_.profesional = profesional_
            miperfil_.save(request)
            return miperfil_

    def create_user(self, request):
        from base.funciones import calculate_username
        username_ = calculate_username(self)
        password = self.identificacion.strip()
        user_ = User.objects.create_user(username=username_, email='', password=password)
        user_.save()

        self.usuario = user_
        self.save(request)

class Administrativo(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, verbose_name=u"Persona")
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

class ProfesionalSalud(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, blank=True, null=True)
    codigo_medico = models.CharField(max_length=50, blank=True, null=True)
    firma_sello = models.TextField(blank=True, null=True)

class PerfilUsuario(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT)
    administrativo = models.ForeignKey(Administrativo, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u'Administrativo')
    profesional = models.ForeignKey(ProfesionalSalud, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u'Profesional de la salud')


class Trabajador(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, blank=True, null=True)
    grupo_sanguineo = models.CharField(max_length=10, blank=True, null=True)
    lateralidad = models.CharField(max_length=20, blank=True, null=True)


class EvaluacionMedicaOcupacional(ModeloBase):
    persona = models.ForeignKey(
        Persona, on_delete=models.PROTECT,
        blank=True, null=True, related_name="evaluaciones"
    )
    profesional = models.ForeignKey(
        ProfesionalSalud, on_delete=models.PROTECT,
        blank=True, null=True, related_name="evaluaciones"
    )

    institucion_sistema = models.CharField(max_length=255, blank=True, null=True)
    ruc = models.CharField(max_length=20, blank=True, null=True)
    ciu = models.CharField(max_length=50, blank=True, null=True)
    establecimiento_trabajo = models.CharField(max_length=255, blank=True, null=True)
    numero_historia_clinica = models.CharField(max_length=50, blank=True, null=True)
    numero_archivo = models.CharField(max_length=50, blank=True, null=True)
    puesto_trabajo_ciu = models.CharField(max_length=255, blank=True, null=True)
    grupo_atencion_prioritaria = models.CharField(max_length=255, blank=True, null=True)

    fecha_atencion = models.DateField(blank=True, null=True)
    fecha_ingreso_trabajo = models.DateField(blank=True, null=True)
    fecha_reintegro = models.DateField(blank=True, null=True)
    fecha_ultimo_dia_laboral = models.DateField(blank=True, null=True)

    tipo_evaluacion = models.CharField(
        max_length=20,
        blank=True, null=True,
        choices=(
            ("INGRESO", "Ingreso"),
            ("PERIODICO", "Periódico"),
            ("REINTEGRO", "Reintegro"),
            ("RETIRO", "Retiro"),
            ("OTRO", "Otro"),
        )
    )
    motivo_consulta = models.TextField(blank=True, null=True)

    antecedentes_clinico_quirurgicos = models.TextField(blank=True, null=True)
    antecedentes_familiares = models.TextField(blank=True, null=True)

    requiere_transfusiones = models.BooleanField(blank=True, null=True)
    tratamiento_hormonal = models.BooleanField(blank=True, null=True)
    tratamiento_hormonal_cual = models.CharField(max_length=255, blank=True, null=True)

    fecha_ultima_menstruacion = models.DateField(blank=True, null=True)
    gestas = models.PositiveIntegerField(blank=True, null=True)
    partos = models.PositiveIntegerField(blank=True, null=True)
    cesareas = models.PositiveIntegerField(blank=True, null=True)
    abortos = models.PositiveIntegerField(blank=True, null=True)

    planificacion_familiar = models.CharField(
        max_length=20,
        blank=True, null=True,
        choices=(("SI", "Sí"), ("NO", "No"), ("NR", "No responde"))
    )
    planificacion_familiar_cual = models.CharField(max_length=255, blank=True, null=True)

    tabaco_detalle = models.CharField(max_length=100, blank=True, null=True)
    alcohol_detalle = models.CharField(max_length=100, blank=True, null=True)
    drogas_detalle = models.CharField(max_length=255, blank=True, null=True)
    consumo_observacion = models.TextField(blank=True, null=True)

    actividad_fisica = models.CharField(max_length=255, blank=True, null=True)
    actividad_fisica_tiempo = models.CharField(max_length=100, blank=True, null=True)

    medicacion_habitual = models.CharField(max_length=255, blank=True, null=True)
    condicion_preexistente = models.CharField(max_length=255, blank=True, null=True)
    condicion_preexistente_cantidad = models.CharField(max_length=100, blank=True, null=True)

    enfermedad_problema_actual = models.TextField(blank=True, null=True)

    temperatura_c = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    presion_arterial = models.CharField(max_length=20, blank=True, null=True)
    frecuencia_cardiaca = models.PositiveIntegerField(blank=True, null=True)
    frecuencia_respiratoria = models.PositiveIntegerField(blank=True, null=True)
    saturacion_oxigeno = models.PositiveIntegerField(blank=True, null=True)
    peso_kg = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    talla_cm = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    imc = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    perimetro_abdominal_cm = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    examen_cabeza = models.TextField(blank=True, null=True)
    examen_ojos = models.TextField(blank=True, null=True)
    examen_oidos = models.TextField(blank=True, null=True)
    examen_nariz = models.TextField(blank=True, null=True)
    examen_boca = models.TextField(blank=True, null=True)
    examen_faringe = models.TextField(blank=True, null=True)
    examen_cuello = models.TextField(blank=True, null=True)
    examen_torax = models.TextField(blank=True, null=True)
    examen_pulmones = models.TextField(blank=True, null=True)
    examen_corazon = models.TextField(blank=True, null=True)
    examen_abdomen = models.TextField(blank=True, null=True)
    examen_columna = models.TextField(blank=True, null=True)
    examen_extremidades_superiores = models.TextField(blank=True, null=True)
    examen_extremidades_inferiores = models.TextField(blank=True, null=True)
    examen_piel = models.TextField(blank=True, null=True)
    examen_neurologico = models.TextField(blank=True, null=True)
    examen_pelvis_genitales = models.TextField(blank=True, null=True)
    examen_observacion = models.TextField(blank=True, null=True)

    aptitud_medica = models.CharField(
        max_length=30,
        blank=True, null=True,
        choices=(
            ("APTO", "Apto"),
            ("APTO_OBSERVACION", "Apto en observación"),
            ("APTO_LIMITACIONES", "Apto con limitaciones"),
            ("NO_APTO", "No apto"),
        )
    )
    aptitud_detalle_observaciones = models.TextField(blank=True, null=True)

    recomendaciones_tratamiento = models.TextField(blank=True, null=True)

    retiro_se_realiza_evaluacion = models.BooleanField(blank=True, null=True)
    retiro_condicion_relacionada_trabajo = models.BooleanField(blank=True, null=True)
    retiro_observacion = models.TextField(blank=True, null=True)

    firma_huella_trabajador = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["persona", "fecha_atencion"]),
            models.Index(fields=["tipo_evaluacion"]),
            models.Index(fields=["numero_historia_clinica"]),
        ]


class AntecedenteLaboral(ModeloBase):
    evaluacion = models.ForeignKey(
        EvaluacionMedicaOcupacional, on_delete=models.PROTECT,
        blank=True, null=True, related_name="antecedentes_laborales"
    )
    empresa = models.CharField(max_length=255, blank=True, null=True)
    puesto = models.CharField(max_length=255, blank=True, null=True)
    actividad = models.TextField(blank=True, null=True)
    tiempo = models.CharField(max_length=100, blank=True, null=True)
    riesgos = models.TextField(blank=True, null=True)
    epp = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["evaluacion"])]


class IncidenteAccidenteEnfermedadOcupacional(ModeloBase):
    evaluacion = models.ForeignKey(
        EvaluacionMedicaOcupacional, on_delete=models.PROTECT,
        blank=True, null=True, related_name="incidentes_ocupacionales"
    )
    puesto_trabajo = models.CharField(max_length=255, blank=True, null=True)
    actividad_desempenada = models.TextField(blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    calificado_por_instituto = models.BooleanField(blank=True, null=True)
    reubicacion = models.BooleanField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["evaluacion", "fecha"])]


class ActividadExtraLaboral(ModeloBase):
    evaluacion = models.ForeignKey(
        EvaluacionMedicaOcupacional, on_delete=models.PROTECT,
        blank=True, null=True, related_name="actividades_extralaborales"
    )
    tipo_actividad = models.CharField(max_length=255, blank=True, null=True)
    frecuencia = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["evaluacion"])]


class ExamenGeneralEspecifico(ModeloBase):
    evaluacion = models.ForeignKey(
        EvaluacionMedicaOcupacional, on_delete=models.PROTECT,
        blank=True, null=True, related_name="examenes"
    )
    nombre_examen = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    resultados = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["evaluacion", "fecha"])]


class Diagnostico(ModeloBase):
    evaluacion = models.ForeignKey(
        EvaluacionMedicaOcupacional, on_delete=models.PROTECT,
        blank=True, null=True, related_name="diagnosticos"
    )
    cie10 = models.CharField(max_length=20, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    presuntivo = models.BooleanField(blank=True, null=True)
    definitivo = models.BooleanField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["evaluacion", "cie10"])]


class CertificadoEvaluacionMedicaOcupacional(ModeloBase):
    evaluacion = models.OneToOneField(
        EvaluacionMedicaOcupacional, on_delete=models.PROTECT,
        blank=True, null=True, related_name="certificado"
    )
    fecha_emision = models.DateField(blank=True, null=True)

    # “congelable” (por si luego editan la evaluación y el certificado no debe cambiar)
    aptitud_medica = models.CharField(
        max_length=30,
        blank=True, null=True,
        choices=(
            ("APTO", "Apto"),
            ("APTO_OBSERVACION", "Apto en observación"),
            ("APTO_LIMITACIONES", "Apto con limitaciones"),
            ("NO_APTO", "No apto"),
        )
    )
    detalle_observaciones = models.TextField(blank=True, null=True)
    recomendaciones = models.TextField(blank=True, null=True)
    firma_huella_trabajador = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["fecha_emision"])]


from django import forms
from saas.models import Persona, CategoriaModulo, Modulo
from base.choices import TIPO_IDENTIFICACION

# Si usas tus modelos en el mismo app:
# from .models import (
#     Trabajador, ProfesionalSalud, EvaluacionMedicaOcupacional,
#     AntecedenteLaboral, IncidenteAccidenteEnfermedadOcupacional,
#     ActividadExtraLaboral, ExamenGeneralEspecifico, Diagnostico,
#     CertificadoEvaluacionMedicaOcupacional
# )

TIPO_EVALUACION_CHOICES = (
    ("INGRESO", "Ingreso"),
    ("PERIODICO", "Periódico"),
    ("REINTEGRO", "Reintegro"),
    ("RETIRO", "Retiro"),
    ("OTRO", "Otro"),
)

PLANIFICACION_CHOICES = (
    ("SI", "Sí"),
    ("NO", "No"),
    ("NR", "No responde"),
)

APTITUD_CHOICES = (
    ("APTO", "Apto"),
    ("APTO_OBSERVACION", "Apto en observación"),
    ("APTO_LIMITACIONES", "Apto con limitaciones"),
    ("NO_APTO", "No apto"),
)

SEXO_CHOICES = (
    ("HOMBRE", "Hombre"),
    ("MUJER", "Mujer"),
)


class ModuloForm(forms.Form):
    # categoria = forms.ModelMultipleChoiceField(queryset=CategoriaModulo.objects.filter(status=True).order_by("nombre"),required=False,label=u"Categoría(s)",widget=forms.SelectMultiple(attrs={"select2search": "true","formwidth": "100%",}))

    orden = forms.IntegerField(initial=0,required=False,label=u"Orden",widget=forms.TextInput(attrs={"class": "imp-numeros","formwidth": "25%",}))

    url = forms.CharField(max_length=100,required=False,label=u"URL",widget=forms.TextInput(attrs={"class": "imp-descripcion","formwidth": "50%","placeholder": "/sistemamedico/evaluaciones"}))

    nombre = forms.CharField(max_length=1000,required=False,label=u"Nombre",widget=forms.TextInput(attrs={"class": "imp-descripcion","formwidth": "50%",}))

    icono = forms.CharField(max_length=100,required=False,label=u"Ícono",widget=forms.TextInput(attrs={"class": "imp-descripcion","formwidth": "50%","placeholder": "fa fa-user-md / bi bi-heart-pulse"}))

    descripcion = forms.CharField(max_length=200,required=False,label=u"Descripción",widget=forms.TextInput(attrs={"class": "imp-descripcion","formwidth": "100%",}))

    activo = forms.BooleanField(required=False,label=u"Activo",widget=forms.CheckboxInput(attrs={"formwidth": "25%",}))

    def cargar(self, modulo: Modulo):
        """
        Para EDIT: precarga los valores desde el objeto.
        """
        # self.fields["categoria"].initial = modulo.categoria.filter(status=True)
        self.fields["orden"].initial = modulo.orden
        self.fields["url"].initial = modulo.url
        self.fields["nombre"].initial = modulo.nombre
        self.fields["icono"].initial = modulo.icono
        self.fields["descripcion"].initial = modulo.descripcion
        self.fields["activo"].initial = modulo.activo

    def guardar(self, request, modulo: Modulo = None):
        """
        Crea o edita un módulo.
        - Si modulo=None -> crea
        - Si modulo existe -> edita
        """
        if modulo is None:
            modulo = Modulo()

        modulo.orden = self.cleaned_data.get("orden") or 0
        modulo.url = (self.cleaned_data.get("url") or "").strip()
        modulo.nombre = (self.cleaned_data.get("nombre") or "").strip()
        modulo.icono = (self.cleaned_data.get("icono") or "").strip()
        modulo.descripcion = (self.cleaned_data.get("descripcion") or "").strip()
        modulo.activo = bool(self.cleaned_data.get("activo"))

        modulo.save(request)

        # ManyToMany
        cats = self.cleaned_data.get("categoria")
        if cats is not None:
            modulo.categoria.set(cats)

        return modulo


class PersonaForm(forms.Form):

    tipo_persona = forms.ChoiceField(choices=Persona.TIPO_PERSONA,required=True,label=u'Tipo de persona',widget=forms.Select(attrs={'class': 'form-select','formwidth': '50%'}))
    tipo_identificacion = forms.ChoiceField(choices=TIPO_IDENTIFICACION,required=True,label=u'Tipo de identificación',widget=forms.Select(attrs={'class': 'form-select','formwidth': '50%'}))
    identificacion = forms.CharField(required=True,max_length=20,label=u'Identificación',widget=forms.TextInput(attrs={'class': 'imp-identificacion','formwidth': '50%'}))

    nombres = forms.CharField(required=False,max_length=255,label=u'Nombres',widget=forms.TextInput(attrs={'class': 'imp-descripcion','formwidth': '50%'}))

    primerapellido = forms.CharField(required=False,max_length=255,label=u'Primer apellido',widget=forms.TextInput(attrs={'class': 'imp-descripcion','formwidth': '50%'}))

    segundoapellido = forms.CharField(required=False,max_length=255,label=u'Segundo apellido',widget=forms.TextInput(attrs={'class': 'imp-descripcion','formwidth': '50%'}))

    email = forms.EmailField(required=False,label=u'Correo electrónico',widget=forms.EmailInput(attrs={'class': 'imp-email','formwidth': '50%'}))

    telefono = forms.CharField(required=False,max_length=30,label=u'Teléfono',widget=forms.TextInput(attrs={'class': 'imp-telefono','formwidth': '50%'}))

    direccion = forms.CharField(required=False,label=u'Dirección',widget=forms.Textarea(attrs={'class': 'imp-descripcion','rows': 3,'formwidth': '100%'}))

    activo = forms.BooleanField(required=False,label=u'Activo',widget=forms.CheckboxInput(attrs={ 'class': 'form-check-input'}))


# ==========================
# TRABAJADOR
# ==========================
class TrabajadorForm(forms.Form):
    persona = forms.IntegerField(
        required=False,
        label=u'Persona',
        widget=forms.TextInput(attrs={'select2search': 'true', 'formwidth': '100%'})
    )
    grupo_sanguineo = forms.CharField(
        required=False, max_length=10, label=u'Grupo sanguíneo',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )
    lateralidad = forms.CharField(
        required=False, max_length=20, label=u'Lateralidad',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )


# ==========================
# PROFESIONAL SALUD
# ==========================
class ProfesionalSaludForm(forms.Form):
    codigo_medico = forms.CharField(
        required=False, max_length=50, label=u'Código médico',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )


# ==========================
# EVALUACIÓN FEMO (CABECERA)
# ==========================
class EvaluacionMedicaOcupacionalForm(forms.Form):
    persona = forms.IntegerField(
        required=True,
        label=u'Persona',
        widget=forms.TextInput(attrs={'select2search': 'true', 'formwidth': '100%'})
    )

    institucion_sistema = forms.CharField(
        required=False, max_length=255, label=u'Institución del sistema',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '100%'})
    )
    ruc = forms.CharField(
        required=False, max_length=20, label=u'RUC',
        widget=forms.TextInput(attrs={'class': 'imp-cedula', 'formwidth': '50%'})
    )
    ciu = forms.CharField(
        required=False, max_length=50, label=u'CIU',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )
    establecimiento_trabajo = forms.CharField(
        required=False, max_length=255, label=u'Establecimiento/Centro de trabajo',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '100%'})
    )
    numero_historia_clinica = forms.CharField(
        required=False, max_length=50, label=u'N° Historia clínica',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )
    numero_archivo = forms.CharField(
        required=False, max_length=50, label=u'N° Archivo',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )
    puesto_trabajo_ciu = forms.CharField(
        required=False, max_length=255, label=u'Puesto de trabajo (CIU)',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '100%'})
    )
    grupo_atencion_prioritaria = forms.CharField(
        required=False, max_length=255, label=u'Grupo de atención prioritaria',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '100%'})
    )

    fecha_atencion = forms.DateField(
        required=False, label=u'Fecha de atención',
        widget=forms.DateInput(attrs={'type': 'date', 'formwidth': '50%'})
    )
    fecha_ingreso_trabajo = forms.DateField(
        required=False, label=u'Fecha de ingreso al trabajo',
        widget=forms.DateInput(attrs={'type': 'date', 'formwidth': '50%'})
    )
    fecha_reintegro = forms.DateField(
        required=False, label=u'Fecha de reintegro',
        widget=forms.DateInput(attrs={'type': 'date', 'formwidth': '50%'})
    )
    fecha_ultimo_dia_laboral = forms.DateField(
        required=False, label=u'Fecha último día laboral/salida',
        widget=forms.DateInput(attrs={'type': 'date', 'formwidth': '50%'})
    )

    tipo_evaluacion = forms.ChoiceField(
        required=False, choices=TIPO_EVALUACION_CHOICES, label=u'Tipo de evaluación',
        widget=forms.Select(attrs={'formwidth': '50%'})
    )
    motivo_consulta = forms.CharField(
        required=False, label=u'Motivo de consulta',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )

    antecedentes_clinico_quirurgicos = forms.CharField(
        required=False, label=u'Antecedentes clínico-quirúrgicos',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )
    antecedentes_familiares = forms.CharField(
        required=False, label=u'Antecedentes familiares',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )

    requiere_transfusiones = forms.BooleanField(
        required=False, label=u'Autoriza transfusiones',
        widget=forms.CheckboxInput(attrs={'formwidth': '25%'})
    )
    tratamiento_hormonal = forms.BooleanField(
        required=False, label=u'Tratamiento hormonal',
        widget=forms.CheckboxInput(attrs={'formwidth': '25%'})
    )
    tratamiento_hormonal_cual = forms.CharField(
        required=False, max_length=255, label=u'Tratamiento hormonal: ¿Cuál?',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )

    fecha_ultima_menstruacion = forms.DateField(
        required=False, label=u'Fecha última menstruación',
        widget=forms.DateInput(attrs={'type': 'date', 'formwidth': '50%'})
    )
    gestas = forms.IntegerField(
        required=False, label=u'Gestas',
        widget=forms.TextInput(attrs={'class': 'imp-numeros', 'formwidth': '25%'})
    )
    partos = forms.IntegerField(
        required=False, label=u'Partos',
        widget=forms.TextInput(attrs={'class': 'imp-numeros', 'formwidth': '25%'})
    )
    cesareas = forms.IntegerField(
        required=False, label=u'Cesáreas',
        widget=forms.TextInput(attrs={'class': 'imp-numeros', 'formwidth': '25%'})
    )
    abortos = forms.IntegerField(
        required=False, label=u'Abortos',
        widget=forms.TextInput(attrs={'class': 'imp-numeros', 'formwidth': '25%'})
    )

    planificacion_familiar = forms.ChoiceField(
        required=False, choices=PLANIFICACION_CHOICES, label=u'Planificación familiar',
        widget=forms.Select(attrs={'formwidth': '50%'})
    )
    planificacion_familiar_cual = forms.CharField(
        required=False, max_length=255, label=u'Planificación: ¿Cuál?',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )

    tabaco_detalle = forms.CharField(
        required=False, max_length=100, label=u'Tabaco (detalle)',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '33%'})
    )
    alcohol_detalle = forms.CharField(
        required=False, max_length=100, label=u'Alcohol (detalle)',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '33%'})
    )
    drogas_detalle = forms.CharField(
        required=False, max_length=255, label=u'Otras drogas (detalle)',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '33%'})
    )
    consumo_observacion = forms.CharField(
        required=False, label=u'Observación (consumo)',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )

    actividad_fisica = forms.CharField(
        required=False, max_length=255, label=u'Actividad física',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )
    actividad_fisica_tiempo = forms.CharField(
        required=False, max_length=100, label=u'Actividad física (tiempo)',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'})
    )

    medicacion_habitual = forms.CharField(
        required=False, max_length=255, label=u'Medicación habitual',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '100%'})
    )
    condicion_preexistente = forms.CharField(
        required=False, max_length=255, label=u'Condición preexistente',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '70%'})
    )
    condicion_preexistente_cantidad = forms.CharField(
        required=False, max_length=100, label=u'Cantidad',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '30%'})
    )

    enfermedad_problema_actual = forms.CharField(
        required=False, label=u'Enfermedad / problema actual',
        widget=forms.Textarea(attrs={'rows': 3, 'formwidth': '100%'})
    )

    temperatura_c = forms.DecimalField(
        required=False, label=u'Temperatura (°C)', max_digits=5, decimal_places=2,
        widget=forms.TextInput(attrs={'class': 'imp-moneda', 'formwidth': '25%'})
    )
    presion_arterial = forms.CharField(
        required=False, max_length=20, label=u'Presión arterial (mmHg)',
        widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '25%'})
    )
    frecuencia_cardiaca = forms.IntegerField(
        required=False, label=u'Frecuencia cardiaca',
        widget=forms.TextInput(attrs={'class': 'imp-numeros', 'formwidth': '25%'})
    )
    frecuencia_respiratoria = forms.IntegerField(
        required=False, label=u'Frecuencia respiratoria',
        widget=forms.TextInput(attrs={'class': 'imp-numeros', 'formwidth': '25%'})
    )
    saturacion_oxigeno = forms.IntegerField(
        required=False, label=u'Saturación O2 (%)',
        widget=forms.TextInput(attrs={'class': 'imp-numeros', 'formwidth': '25%'})
    )
    peso_kg = forms.DecimalField(
        required=False, label=u'Peso (Kg)', max_digits=7, decimal_places=2,
        widget=forms.TextInput(attrs={'class': 'imp-moneda', 'formwidth': '25%'})
    )
    talla_cm = forms.DecimalField(
        required=False, label=u'Talla (cm)', max_digits=6, decimal_places=2,
        widget=forms.TextInput(attrs={'class': 'imp-moneda', 'formwidth': '25%'})
    )
    imc = forms.DecimalField(
        required=False, label=u'IMC', max_digits=6, decimal_places=2,
        widget=forms.TextInput(attrs={'class': 'imp-moneda', 'formwidth': '25%'})
    )
    perimetro_abdominal_cm = forms.DecimalField(
        required=False, label=u'Perímetro abdominal (cm)', max_digits=6, decimal_places=2,
        widget=forms.TextInput(attrs={'class': 'imp-moneda', 'formwidth': '25%'})
    )

    # Examen físico regional (texto libre por zona)
    examen_cabeza = forms.CharField(required=False, label=u'Examen: Cabeza',
                                    widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_ojos = forms.CharField(required=False, label=u'Examen: Ojos',
                                  widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_oidos = forms.CharField(required=False, label=u'Examen: Oídos',
                                   widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_nariz = forms.CharField(required=False, label=u'Examen: Nariz',
                                   widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_boca = forms.CharField(required=False, label=u'Examen: Boca',
                                  widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_faringe = forms.CharField(required=False, label=u'Examen: Faringe',
                                     widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_cuello = forms.CharField(required=False, label=u'Examen: Cuello',
                                    widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_torax = forms.CharField(required=False, label=u'Examen: Tórax',
                                   widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_pulmones = forms.CharField(required=False, label=u'Examen: Pulmones',
                                      widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_corazon = forms.CharField(required=False, label=u'Examen: Corazón',
                                     widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_abdomen = forms.CharField(required=False, label=u'Examen: Abdomen',
                                     widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_columna = forms.CharField(required=False, label=u'Examen: Columna',
                                     widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_extremidades_superiores = forms.CharField(required=False, label=u'Examen: Miembros superiores',
                                                     widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_extremidades_inferiores = forms.CharField(required=False, label=u'Examen: Miembros inferiores',
                                                     widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_piel = forms.CharField(required=False, label=u'Examen: Piel',
                                  widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_neurologico = forms.CharField(required=False, label=u'Examen: Neurológico',
                                         widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_pelvis_genitales = forms.CharField(required=False, label=u'Examen: Pelvis/Genitales',
                                              widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    examen_observacion = forms.CharField(required=False, label=u'Observación examen físico',
                                         widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))

    aptitud_medica = forms.ChoiceField(
        required=False, choices=APTITUD_CHOICES, label=u'Aptitud médica',
        widget=forms.Select(attrs={'formwidth': '50%'})
    )
    aptitud_detalle_observaciones = forms.CharField(
        required=False, label=u'Detalle de observaciones (aptitud)',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )

    recomendaciones_tratamiento = forms.CharField(
        required=False, label=u'Recomendaciones / tratamiento',
        widget=forms.Textarea(attrs={'rows': 3, 'formwidth': '100%'})
    )

    retiro_se_realiza_evaluacion = forms.BooleanField(
        required=False, label=u'Retiro: ¿Se realiza evaluación?',
        widget=forms.CheckboxInput(attrs={'formwidth': '25%'})
    )
    retiro_condicion_relacionada_trabajo = forms.BooleanField(
        required=False, label=u'Retiro: ¿Condición relacionada al trabajo?',
        widget=forms.CheckboxInput(attrs={'formwidth': '25%'})
    )
    retiro_observacion = forms.CharField(
        required=False, label=u'Retiro: Observación',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )

    firma_huella_trabajador = forms.CharField(
        required=False, label=u'Firma o huella del trabajador',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )

    def cargar_persona(self, persona):
        self.fields['persona'].widget.attrs['descripcion'] = persona.__str__()
        self.fields['persona'].initial = persona.id
        self.fields['persona'].widget.attrs['value'] = persona.id


# ==========================
# DETALLES (TABLAS ILIMITADAS)
# ==========================

class AntecedenteLaboralForm(forms.Form):
    evaluacion = forms.IntegerField(
        required=False, label=u'Evaluación',
        widget=forms.TextInput(attrs={'select2search': 'true', 'formwidth': '100%'})
    )
    empresa = forms.CharField(required=False, max_length=255, label=u'Empresa',
                              widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'}))
    puesto = forms.CharField(required=False, max_length=255, label=u'Puesto',
                             widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'}))
    actividad = forms.CharField(required=False, label=u'Actividad',
                                widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    tiempo = forms.CharField(required=False, max_length=100, label=u'Tiempo',
                             widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '33%'}))
    riesgos = forms.CharField(required=False, label=u'Riesgos',
                              widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    epp = forms.CharField(required=False, label=u'EPP / Medidas',
                          widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    observaciones = forms.CharField(required=False, label=u'Observaciones',
                                    widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))


class IncidenteAccidenteEnfermedadOcupacionalForm(forms.Form):
    evaluacion = forms.IntegerField(
        required=False, label=u'Evaluación',
        widget=forms.TextInput(attrs={'select2search': 'true', 'formwidth': '100%'})
    )
    puesto_trabajo = forms.CharField(required=False, max_length=255, label=u'Puesto de trabajo',
                                     widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '50%'}))
    actividad_desempenada = forms.CharField(required=False, label=u'Actividad que desempeñaba',
                                           widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    fecha = forms.DateField(required=False, label=u'Fecha',
                            widget=forms.DateInput(attrs={'type': 'date', 'formwidth': '50%'}))
    descripcion = forms.CharField(required=False, label=u'Descripción',
                                  widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    calificado_por_instituto = forms.BooleanField(required=False, label=u'Calificado por instituto/seguro',
                                                  widget=forms.CheckboxInput(attrs={'formwidth': '25%'}))
    reubicacion = forms.BooleanField(required=False, label=u'Reubicación',
                                     widget=forms.CheckboxInput(attrs={'formwidth': '25%'}))
    observaciones = forms.CharField(required=False, label=u'Observaciones',
                                    widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))


class ActividadExtraLaboralForm(forms.Form):
    evaluacion = forms.IntegerField(
        required=False, label=u'Evaluación',
        widget=forms.TextInput(attrs={'select2search': 'true', 'formwidth': '100%'})
    )
    tipo_actividad = forms.CharField(required=False, max_length=255, label=u'Tipo de actividad',
                                     widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '70%'}))
    frecuencia = forms.CharField(required=False, max_length=100, label=u'Frecuencia',
                                 widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '30%'}))
    observaciones = forms.CharField(required=False, label=u'Observaciones',
                                    widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))


class ExamenGeneralEspecificoForm(forms.Form):
    evaluacion = forms.IntegerField(
        required=False, label=u'Evaluación',
        widget=forms.TextInput(attrs={'select2search': 'true', 'formwidth': '100%'})
    )
    nombre_examen = forms.CharField(required=False, max_length=255, label=u'Nombre del examen',
                                    widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '70%'}))
    fecha = forms.DateField(required=False, label=u'Fecha',
                            widget=forms.DateInput(attrs={'type': 'date', 'formwidth': '30%'}))
    resultados = forms.CharField(required=False, label=u'Resultados',
                                 widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))
    observaciones = forms.CharField(required=False, label=u'Observaciones',
                                    widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'}))


class DiagnosticoForm(forms.Form):
    evaluacion = forms.IntegerField(
        required=False, label=u'Evaluación',
        widget=forms.TextInput(attrs={'select2search': 'true', 'formwidth': '100%'})
    )
    cie10 = forms.CharField(required=False, max_length=20, label=u'CIE-10',
                            widget=forms.TextInput(attrs={'class': 'imp-descripcion', 'formwidth': '30%'}))
    descripcion = forms.CharField(required=False, label=u'Descripción',
                                  widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '70%'}))
    presuntivo = forms.BooleanField(required=False, label=u'Presuntivo',
                                    widget=forms.CheckboxInput(attrs={'formwidth': '25%'}))
    definitivo = forms.BooleanField(required=False, label=u'Definitivo',
                                    widget=forms.CheckboxInput(attrs={'formwidth': '25%'}))


class CertificadoEvaluacionMedicaOcupacionalForm(forms.Form):
    evaluacion = forms.IntegerField(
        required=False, label=u'Evaluación',
        widget=forms.TextInput(attrs={'select2search': 'true', 'formwidth': '100%'})
    )
    fecha_emision = forms.DateField(
        required=False, label=u'Fecha de emisión',
        widget=forms.DateInput(attrs={'type': 'date', 'formwidth': '50%'})
    )
    aptitud_medica = forms.ChoiceField(
        required=False, choices=APTITUD_CHOICES, label=u'Aptitud médica',
        widget=forms.Select(attrs={'formwidth': '50%'})
    )
    detalle_observaciones = forms.CharField(
        required=False, label=u'Detalle observaciones',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )
    recomendaciones = forms.CharField(
        required=False, label=u'Recomendaciones',
        widget=forms.Textarea(attrs={'rows': 3, 'formwidth': '100%'})
    )
    firma_huella_trabajador = forms.CharField(
        required=False, label=u'Firma/Huella trabajador',
        widget=forms.Textarea(attrs={'rows': 2, 'formwidth': '100%'})
    )

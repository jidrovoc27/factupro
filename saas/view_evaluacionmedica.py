import os, subprocess, tempfile
import json
from datetime import datetime
from django.db.models import Q
from django.db import transaction
from sistemamedico import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.http import FileResponse, Http404
from django.template.loader import get_template, render_to_string

from .models import EvaluacionMedicaOcupacional, Trabajador, ProfesionalSalud, AntecedenteLaboral
from .forms import EvaluacionMedicaOcupacionalForm, AntecedenteLaboralForm
from saas.vistaprincipal import act_info
from saas.models import *
from base.funciones import MiPaginador, _to_date_or_none, _to_int_or_none, _to_decimal_or_none, _to_bool, obtener_ip_cliente_actual
from saas.funciones_reporte import generar_pdf_femo_completo

# adduserdata, MiPaginador, log, etc. los asumo existentes como en tu proyecto.

def _parse_json_list(raw):
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except:
        return []

def _parse_json_dict(raw):
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except:
        return {}

def _loads_list(value):
    try:
        if not value:
            return []
        return json.loads(value)
    except Exception:
        return []

def _to_date(v):
    if not v:
        return None
    try:
        return datetime.strptime(v, "%Y-%m-%d").date()
    except Exception:
        return None

def _to_bool(v):
    return True if str(v).lower() in ("1", "true", "yes", "si", "on") else False

def chunk(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)] or [[]]



def view(request):
    data = {}
    act_info(request, data)
    persona = request.session.get('persona')
    profesional_ = data['profesional_']

    if request.method == 'POST':
        action = request.POST.get('action', '')
        data['action'] = action

        # =========================
        # EVALUACION: ADD
        # =========================
        if action == 'addevaluacion':
            try:
                with transaction.atomic():

                    if not profesional_:
                        return JsonResponse({
                            'result': True,
                            'mensaje': 'Usted no cuenta como Profesional de la salud autorizado.'
                        })

                    p = request.POST  # shortcut

                    # ── Crear evaluación con TODOS los campos del formulario ──
                    ev = EvaluacionMedicaOcupacional(
                        persona_id=p.get('persona') or None,
                        profesional=profesional_,

                        # A. Datos establecimiento
                        institucion_sistema=p.get('institucion_sistema') or None,
                        ruc=p.get('ruc') or None,
                        ciu=p.get('ciu') or None,
                        establecimiento_trabajo=p.get('establecimiento_trabajo') or None,
                        numero_historia_clinica=p.get('numero_historia_clinica') or None,
                        numero_archivo=p.get('numero_archivo') or None,
                        puesto_trabajo_ciu=p.get('puesto_trabajo_ciu') or p.get('puesto_trabajo_ciu_b') or None,

                        # Grupo atención prioritaria
                        gap_embarazada=p.get('gap_embarazada') or None,
                        gap_discapacidad=p.get('gap_discapacidad') or None,
                        gap_catastrofica=p.get('gap_catastrofica') or None,
                        gap_adulto_mayor=p.get('gap_adulto_mayor') or None,

                        # B. Motivo consulta
                        fecha_atencion=_to_date_or_none(p.get('fecha_atencion')),
                        fecha_ingreso_trabajo=_to_date_or_none(p.get('fecha_ingreso_trabajo')),
                        fecha_reintegro=_to_date_or_none(p.get('fecha_reintegro')),
                        fecha_ultimo_dia_laboral=_to_date_or_none(p.get('fecha_ultimo_dia_laboral')),
                        tipo_evaluacion=p.get('tipo_evaluacion') or None,
                        motivo_consulta=p.get('motivo_consulta') or None,

                        # C. Antecedentes personales
                        antecedentes_clinico_quirurgicos=p.get('antecedentes_clinico_quirurgicos') or None,
                        antecedentes_familiares=p.get('antecedentes_familiares') or None,
                        requiere_transfusiones=_to_bool(p.get('requiere_transfusiones')),
                        tratamiento_hormonal=_to_bool(p.get('tratamiento_hormonal')),
                        tratamiento_hormonal_cual=p.get('tratamiento_hormonal_cual') or None,

                        # Gineco-obstétrico
                        fecha_ultima_menstruacion=_to_date_or_none(p.get('fecha_ultima_menstruacion')),
                        gestas=_to_int_or_none(p.get('gestas')),
                        partos=_to_int_or_none(p.get('partos')),
                        cesareas=_to_int_or_none(p.get('cesareas')),
                        abortos=_to_int_or_none(p.get('abortos')),
                        planificacion_familiar=p.get('planificacion_familiar') or None,
                        planificacion_familiar_cual=p.get('planificacion_familiar_cual') or None,
                        examenes_gineco_cual=p.get('examenes_gineco_cual') or None,
                        examenes_gineco_tiempo=p.get('examenes_gineco_tiempo') or None,

                        # Reproductivos masculinos
                        examenes_masculino_cual=p.get('examenes_masculino_cual') or None,
                        examenes_masculino_tiempo=p.get('examenes_masculino_tiempo') or None,
                        plan_fam_masculino=p.get('plan_fam_masculino') or None,
                        plan_fam_masculino_cual=p.get('plan_fam_masculino_cual') or None,

                        # Consumo
                        # Tabaco
                        tabaco_detalle=p.get('tabaco_detalle') or None,
                        tabaco_ex_consumidor=p.get('tabaco_ex_consumidor') or None,
                        tabaco_tiempo_abstinencia=p.get('tabaco_tiempo_abstinencia') or None,
                        tabaco_no_consume=p.get('tabaco_no_consume') or None,

                        # Alcohol
                        alcohol_detalle=p.get('alcohol_detalle') or None,
                        alcohol_ex_consumidor=p.get('alcohol_ex_consumidor') or None,
                        alcohol_tiempo_abstinencia=p.get('alcohol_tiempo_abstinencia') or None,
                        alcohol_no_consume=p.get('alcohol_no_consume') or None,

                        # Drogas
                        drogas_detalle=p.get('drogas_detalle') or None,
                        drogas_ex_consumidor=p.get('drogas_ex_consumidor') or None,
                        drogas_tiempo_abstinencia=p.get('drogas_tiempo_abstinencia') or None,
                        drogas_no_consume=p.get('drogas_no_consume') or None,
                        consumo_observacion=p.get('consumo_observacion') or None,

                        # Estilo de vida
                        actividad_fisica=p.get('actividad_fisica') or None,
                        actividad_fisica_cual=p.get('actividad_fisica_cual') or None,
                        actividad_fisica_tiempo=p.get('actividad_fisica_tiempo') or None,

                        # Condición preexistente
                        medicacion_habitual=p.get('medicacion_habitual') or None,
                        condicion_preexistente=p.get('condicion_preexistente') or None,
                        condicion_preexistente_cantidad=p.get('condicion_preexistente_cantidad') or None,

                        # D. Enfermedad actual
                        enfermedad_problema_actual=p.get('enfermedad_problema_actual') or None,

                        # E. Constantes vitales
                        temperatura_c=_to_decimal_or_none(p.get('temperatura_c')),
                        presion_arterial=p.get('presion_arterial') or None,
                        frecuencia_cardiaca=_to_int_or_none(p.get('frecuencia_cardiaca')),
                        frecuencia_respiratoria=_to_int_or_none(p.get('frecuencia_respiratoria')),
                        saturacion_oxigeno=_to_int_or_none(p.get('saturacion_oxigeno')),
                        peso_kg=_to_decimal_or_none(p.get('peso_kg')),
                        talla_cm=_to_decimal_or_none(p.get('talla_cm')),
                        imc=_to_decimal_or_none(p.get('imc')),
                        perimetro_abdominal_cm=_to_decimal_or_none(p.get('perimetro_abdominal_cm')),

                        # F. Examen físico
                        examen_piel=p.get('examen_piel') or None,
                        examen_ojos=p.get('examen_ojos') or None,
                        examen_oidos=p.get('examen_oidos') or None,
                        examen_nariz=p.get('examen_nariz') or None,
                        examen_boca=p.get('examen_boca') or None,
                        examen_cuello=p.get('examen_cuello') or None,
                        examen_torax=p.get('examen_torax') or None,
                        examen_pulmones=p.get('examen_pulmones') or None,
                        examen_abdomen=p.get('examen_abdomen') or None,
                        examen_columna=p.get('examen_columna') or None,
                        examen_extremidades_superiores=p.get('examen_extremidades_superiores') or None,
                        examen_pelvis_genitales=p.get('examen_pelvis_genitales') or None,
                        examen_neurologico=p.get('examen_neurologico') or None,
                        examen_observacion=p.get('examen_observacion') or None,

                        # J. Observaciones exámenes
                        examenes_observaciones=p.get('examenes_observaciones') or None,

                        # L. Aptitud
                        aptitud_medica=p.get('aptitud_medica') or None,
                        aptitud_detalle_observaciones=p.get('aptitud_detalle_observaciones') or None,

                        # M. Recomendaciones
                        recomendaciones_tratamiento=p.get('recomendaciones_tratamiento') or None,

                        # N. Retiro
                        retiro_se_realiza_evaluacion=_to_bool(p.get('retiro_se_realiza_evaluacion')),
                        retiro_condicion_relacionada_trabajo=_to_bool(p.get('retiro_condicion_relacionada_trabajo')),
                        retiro_observacion=p.get('retiro_observacion') or None,

                        # P. Firma
                        firma_huella_trabajador=p.get('firma_huella_trabajador') or None,
                    )
                    ev.save(request)

                    # ── Tabla H — Antecedentes laborales (fusionada) ──
                    antecedentes = _parse_json_list(request.POST.get('antecedentes_json'))
                    for a in antecedentes:
                        _id = a.get('id')
                        payload = dict(
                            empresa=a.get('empresa') or None,
                            puesto=a.get('puesto') or None,
                            actividad=a.get('actividad_desempenada') or a.get('actividad') or None,
                            tiempo=a.get('tiempo') or None,
                            riesgos=a.get('riesgos') or None,
                            epp=a.get('epp') or None,
                            observaciones=a.get('observaciones') or None,
                            # nuevos campos tabla H
                            anterior=_to_bool(a.get('anterior')),
                            actual=_to_bool(a.get('actual')),
                            incidente=_to_bool(a.get('incidente')),
                            accidente=_to_bool(a.get('accidente')),
                            enfermedad_profesional=_to_bool(a.get('enfermedad_profesional')),
                            calificado_por_instituto=_to_bool(a.get('calificado_por_instituto')),
                            fecha=_to_date_or_none(a.get('fecha')),
                            descripcion=a.get('descripcion') or None,
                        )
                        if _id:
                            AntecedenteLaboral.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            AntecedenteLaboral.objects.create(evaluacion=ev, **payload)

                    # Eliminados
                    deleted_ant = _parse_json_list(request.POST.get('antecedentes_deleted', '[]'))
                    if deleted_ant:
                        AntecedenteLaboral.objects.filter(
                            id__in=[x for x in deleted_ant if x],
                            evaluacion=ev
                        ).delete()

                    # ── Tabla I — Actividades extralaborales ──
                    actividades = _parse_json_list(request.POST.get('actividades_json'))
                    for x in actividades:
                        _id = x.get('id')
                        payload = dict(
                            tipo_actividad=x.get('tipo_actividad') or None,
                            frecuencia=x.get('fecha') or None,  # el form usa 'fecha' como frecuencia/fecha
                            observaciones=x.get('observaciones') or None,
                        )
                        if _id:
                            ActividadExtraLaboral.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            ActividadExtraLaboral.objects.create(evaluacion=ev, **payload)

                    deleted_act = _parse_json_list(request.POST.get('actividades_deleted', '[]'))
                    if deleted_act:
                        ActividadExtraLaboral.objects.filter(
                            id__in=[x for x in deleted_act if x],
                            evaluacion=ev
                        ).delete()

                    # ── Tabla J — Exámenes ──
                    examenes = _parse_json_list(request.POST.get('examenes_json'))
                    for e in examenes:
                        _id = e.get('id')
                        payload = dict(
                            nombre_examen=e.get('nombre_examen') or None,
                            fecha=_to_date_or_none(e.get('fecha')),
                            resultados=e.get('resultados') or None,
                            observaciones=e.get('observaciones') or None,
                        )
                        if _id:
                            ExamenGeneralEspecifico.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            ExamenGeneralEspecifico.objects.create(evaluacion=ev, **payload)

                    deleted_exa = _parse_json_list(request.POST.get('examenes_deleted', '[]'))
                    if deleted_exa:
                        ExamenGeneralEspecifico.objects.filter(
                            id__in=[x for x in deleted_exa if x],
                            evaluacion=ev
                        ).delete()

                    # ── Tabla K — Diagnósticos ──
                    diagnosticos = _parse_json_list(request.POST.get('diagnosticos_json'))
                    for d in diagnosticos:
                        _id = d.get('id')
                        payload = dict(
                            cie10=d.get('cie10') or None,
                            descripcion=d.get('descripcion') or None,
                            presuntivo=_to_bool(d.get('presuntivo')),
                            definitivo=_to_bool(d.get('definitivo')),
                        )
                        if _id:
                            Diagnostico.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            Diagnostico.objects.create(evaluacion=ev, **payload)

                    deleted_dx = _parse_json_list(request.POST.get('diagnosticos_deleted', '[]'))
                    if deleted_dx:
                        Diagnostico.objects.filter(
                            id__in=[x for x in deleted_dx if x],
                            evaluacion=ev
                        ).delete()

                    # ── Certificado (opcional) ──
                    cert = _parse_json_dict(request.POST.get('certificado_json', '{}'))
                    if any((cert.get(k) or '').strip() for k in
                           ['fecha_emision', 'aptitud_medica', 'detalle_observaciones',
                            'recomendaciones', 'firma_huella_trabajador']):
                        CertificadoEvaluacionMedicaOcupacional.objects.create(
                            evaluacion=ev,
                            fecha_emision=_to_date_or_none(cert.get('fecha_emision')),
                            aptitud_medica=cert.get('aptitud_medica') or None,
                            detalle_observaciones=cert.get('detalle_observaciones') or None,
                            recomendaciones=cert.get('recomendaciones') or None,
                            firma_huella_trabajador=cert.get('firma_huella_trabajador') or None,
                        )

                    return JsonResponse({'result': False, 'mensaje': 'Guardado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                import traceback
                return JsonResponse({'result': True, 'mensaje': f'Error al guardar: {traceback.format_exc()}'})

        # =========================
        # EVALUACION: EDIT
        # =========================
        if action == 'editevaluacion':
            try:
                with transaction.atomic():

                    ev = EvaluacionMedicaOcupacional.objects.get(pk=int(request.POST.get('id')))
                    p = request.POST

                    # Actualizar todos los campos (mismos que el ADD)
                    ev.persona_id = p.get('persona') or None
                    ev.institucion_sistema = p.get('institucion_sistema') or None
                    ev.ruc = p.get('ruc') or None
                    ev.ciu = p.get('ciu') or None
                    ev.establecimiento_trabajo = p.get('establecimiento_trabajo') or None
                    ev.numero_historia_clinica = p.get('numero_historia_clinica') or None
                    ev.numero_archivo = p.get('numero_archivo') or None
                    ev.puesto_trabajo_ciu = p.get('puesto_trabajo_ciu') or p.get('puesto_trabajo_ciu_b') or None
                    ev.gap_embarazada = p.get('gap_embarazada') or None
                    ev.gap_discapacidad = p.get('gap_discapacidad') or None
                    ev.gap_catastrofica = p.get('gap_catastrofica') or None
                    ev.gap_adulto_mayor = p.get('gap_adulto_mayor') or None
                    ev.fecha_atencion = _to_date_or_none(p.get('fecha_atencion'))
                    ev.fecha_ingreso_trabajo = _to_date_or_none(p.get('fecha_ingreso_trabajo'))
                    ev.fecha_reintegro = _to_date_or_none(p.get('fecha_reintegro'))
                    ev.fecha_ultimo_dia_laboral = _to_date_or_none(p.get('fecha_ultimo_dia_laboral'))
                    ev.tipo_evaluacion = p.get('tipo_evaluacion') or None
                    ev.motivo_consulta = p.get('motivo_consulta') or None
                    ev.antecedentes_clinico_quirurgicos = p.get('antecedentes_clinico_quirurgicos') or None
                    ev.antecedentes_familiares = p.get('antecedentes_familiares') or None
                    ev.requiere_transfusiones = _to_bool(p.get('requiere_transfusiones'))
                    ev.tratamiento_hormonal = _to_bool(p.get('tratamiento_hormonal'))
                    ev.tratamiento_hormonal_cual = p.get('tratamiento_hormonal_cual') or None
                    ev.fecha_ultima_menstruacion = _to_date_or_none(p.get('fecha_ultima_menstruacion'))
                    ev.gestas = _to_int_or_none(p.get('gestas'))
                    ev.partos = _to_int_or_none(p.get('partos'))
                    ev.cesareas = _to_int_or_none(p.get('cesareas'))
                    ev.abortos = _to_int_or_none(p.get('abortos'))
                    ev.planificacion_familiar = p.get('planificacion_familiar') or None
                    ev.planificacion_familiar_cual = p.get('planificacion_familiar_cual') or None
                    ev.examenes_gineco_cual = p.get('examenes_gineco_cual') or None
                    ev.examenes_gineco_tiempo = p.get('examenes_gineco_tiempo') or None
                    ev.examenes_masculino_cual = p.get('examenes_masculino_cual') or None
                    ev.examenes_masculino_tiempo = p.get('examenes_masculino_tiempo') or None
                    ev.plan_fam_masculino = p.get('plan_fam_masculino') or None
                    ev.plan_fam_masculino_cual = p.get('plan_fam_masculino_cual') or None
                    ev.tabaco_detalle = p.get('tabaco_detalle') or None
                    ev.alcohol_detalle = p.get('alcohol_detalle') or None
                    ev.drogas_detalle = p.get('drogas_detalle') or None
                    ev.consumo_observacion = p.get('consumo_observacion') or None
                    ev.actividad_fisica = p.get('actividad_fisica') or None
                    ev.actividad_fisica_tiempo = p.get('actividad_fisica_tiempo') or None
                    ev.medicacion_habitual = p.get('medicacion_habitual') or None
                    ev.condicion_preexistente = p.get('condicion_preexistente') or None
                    ev.condicion_preexistente_cantidad = p.get('condicion_preexistente_cantidad') or None
                    ev.enfermedad_problema_actual = p.get('enfermedad_problema_actual') or None
                    ev.temperatura_c = _to_decimal_or_none(p.get('temperatura_c'))
                    ev.presion_arterial = p.get('presion_arterial') or None
                    ev.frecuencia_cardiaca = _to_int_or_none(p.get('frecuencia_cardiaca'))
                    ev.frecuencia_respiratoria = _to_int_or_none(p.get('frecuencia_respiratoria'))
                    ev.saturacion_oxigeno = _to_int_or_none(p.get('saturacion_oxigeno'))
                    ev.peso_kg = _to_decimal_or_none(p.get('peso_kg'))
                    ev.talla_cm = _to_decimal_or_none(p.get('talla_cm'))
                    ev.imc = _to_decimal_or_none(p.get('imc'))
                    ev.perimetro_abdominal_cm = _to_decimal_or_none(p.get('perimetro_abdominal_cm'))
                    ev.examen_piel = p.get('examen_piel') or None
                    ev.examen_ojos = p.get('examen_ojos') or None
                    ev.examen_oidos = p.get('examen_oidos') or None
                    ev.examen_nariz = p.get('examen_nariz') or None
                    ev.examen_boca = p.get('examen_boca') or None
                    ev.examen_cuello = p.get('examen_cuello') or None
                    ev.examen_torax = p.get('examen_torax') or None
                    ev.examen_pulmones = p.get('examen_pulmones') or None
                    ev.examen_abdomen = p.get('examen_abdomen') or None
                    ev.examen_columna = p.get('examen_columna') or None
                    ev.examen_extremidades_superiores = p.get('examen_extremidades_superiores') or None
                    ev.examen_pelvis_genitales = p.get('examen_pelvis_genitales') or None
                    ev.examen_neurologico = p.get('examen_neurologico') or None
                    ev.examen_observacion = p.get('examen_observacion') or None
                    ev.examenes_observaciones = p.get('examenes_observaciones') or None
                    ev.aptitud_medica = p.get('aptitud_medica') or None
                    ev.aptitud_detalle_observaciones = p.get('aptitud_detalle_observaciones') or None
                    ev.recomendaciones_tratamiento = p.get('recomendaciones_tratamiento') or None
                    ev.retiro_se_realiza_evaluacion = _to_bool(p.get('retiro_se_realiza_evaluacion'))
                    ev.retiro_condicion_relacionada_trabajo = _to_bool(p.get('retiro_condicion_relacionada_trabajo'))
                    ev.retiro_observacion = p.get('retiro_observacion') or None
                    ev.firma_huella_trabajador = p.get('firma_huella_trabajador') or None

                    ev.save(request)

                    # Sub-tablas: misma lógica que ADD (reutiliza el bloque de arriba)
                    # ... (copiar desde el bloque de antecedentes hasta diagnósticos)

                    return JsonResponse({'result': False, 'mensaje': 'Actualizado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                import traceback
                return JsonResponse({'result': True, 'mensaje': f'Error al actualizar: {traceback.format_exc()}'})

        # =========================
        # EVALUACION: DELETE LOGICO
        # =========================
        if action == 'delevaluacion':
            try:
                evaluacion = EvaluacionMedicaOcupacional.objects.get(pk=request.POST.get('id'))
                evaluacion.status = False
                evaluacion.save(request)
                #log(u'Eliminó evaluación FEMO: %s' % evaluacion.id, request, 'del')
                return JsonResponse({"error": False, "refresh": True, "mensaje": "Se ha eliminado correctamente el registro."})
            except Exception:
                transaction.set_rollback(True)
                return JsonResponse({"error": True, "mensaje": "Ha ocurrido un error al eliminar la evaluación."})

        # =========================
        # DETALLE (ANTECEDENTE): ADD
        # =========================
        if action == 'addantecedente':
            try:
                with transaction.atomic():
                    form = AntecedenteLaboralForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse({'result': True, 'mensaje': 'El formulario no ha sido completado correctamente.'})

                    evaluacion_id = request.POST.get('evaluacion_id')
                    if not evaluacion_id:
                        return JsonResponse({'result': True, 'mensaje': 'No se recibió evaluacion_id.'})

                    det = AntecedenteLaboral(
                        evaluacion_id=int(evaluacion_id),
                        empresa=form.cleaned_data.get('empresa'),
                        puesto=form.cleaned_data.get('puesto'),
                        actividad=form.cleaned_data.get('actividad'),
                        tiempo=form.cleaned_data.get('tiempo'),
                        riesgos=form.cleaned_data.get('riesgos'),
                        epp=form.cleaned_data.get('epp'),
                        observaciones=form.cleaned_data.get('observaciones'),
                    )
                    det.save(request)
                    #log(u'Adicionó antecedente laboral: %s' % det.id, request, 'add')
                    return JsonResponse({'result': False, 'mensaje': u'Guardado con éxito'})
            except Exception:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': 'Ha ocurrido un error al adicionar el antecedente.'})

        # =========================
        # DETALLE (ANTECEDENTE): EDIT
        # =========================
        if action == 'editantecedente':
            try:
                with transaction.atomic():
                    form = AntecedenteLaboralForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse({'result': True, 'mensaje': 'El formulario no ha sido completado correctamente.'})

                    det = AntecedenteLaboral.objects.get(pk=request.POST.get('id'))
                    det.empresa = form.cleaned_data.get('empresa')
                    det.puesto = form.cleaned_data.get('puesto')
                    det.actividad = form.cleaned_data.get('actividad')
                    det.tiempo = form.cleaned_data.get('tiempo')
                    det.riesgos = form.cleaned_data.get('riesgos')
                    det.epp = form.cleaned_data.get('epp')
                    det.observaciones = form.cleaned_data.get('observaciones')
                    det.save(request)

                    #log(u'Editó antecedente laboral: %s' % det.id, request, 'edit')
                    return JsonResponse({'result': False, 'mensaje': 'Ha editado el antecedente exitosamente.'})
            except Exception:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': 'Ha ocurrido un error al editar el antecedente.'})

        # =========================
        # DETALLE (ANTECEDENTE): DELETE LOGICO
        # =========================
        if action == 'delantecedente':
            try:
                det = AntecedenteLaboral.objects.get(pk=request.POST.get('id'))
                det.status = False
                det.save(request)
                #log(u'Eliminó antecedente laboral: %s' % det.id, request, 'del')
                return JsonResponse({"error": False, "refresh": True, "mensaje": "Se ha eliminado correctamente el registro."})
            except Exception:
                transaction.set_rollback(True)
                return JsonResponse({"error": True, "mensaje": "Ha ocurrido un error al eliminar el antecedente."})

        return JsonResponse({'result': True, 'mensaje': 'Acción no reconocida.'})

    # =========================
    # GET (LISTADOS + MODALES)
    # =========================
    if 'action' in request.GET:
        action = request.GET.get('action')
        data['action'] = action

        # MODAL ADD EVALUACION
        if action == 'addevaluacion':
            try:
                data['action'] = 'addevaluacion'
                data['title_modal'] = 'Nueva evaluación FEMO'
                data['form'] = EvaluacionMedicaOcupacionalForm()

                data[
                    "lista"] = "Temperaturas altas,Temperaturas bajas,Radiación Ionizante,Radiación No Ionizante,Ruido,Vibración,Iluminación,Ventilación,Fluido eléctrico,Otros __________".split(
                    ",")
                data[
                    "listaseguridad"] = "Atrapamiento entre Máquinas y o superficies,Atrapamiento entre objetos,Caída de objetos,Caídas al mismo nivel,Caídas a diferente nivel,Pinchazos,Cortes,Choques /colisión vehicular,Atropellamientos por vehículos,Proyección de fluidos,Proyección de partículas – fragmentos,Contacto con superficies de trabajos".split(
                    ",")
                data[
                    "listaquimicos"] = "Polvos,Sólidos,Humos,líquidos,vapores,Aerosoles,Neblinas,Gaseosos,Otros __________".split(
                    ",")
                data[
                    "listabiologicos"] = "Virus,Hongos,Bacterias,Parásitos,Exposición a vectores,Exposición a animales selváticos,Otros __________".split(
                    ",")
                data[
                    "listaergonomicos"] = "Manejo manual de cargas,Movimiento repetitivos,Posturas forzadas,Trabajos con PVD,Diseño Inadecuado del puesto,Otros __________".split(
                    ",")
                data[
                    "listapsicosociales"] = "Monotonía del trabajo,Sobrecarga laboral,Minuciosidad de la tarea,Alta responsabilidad,Autonomía en la toma de decisiones,Supervisión y estilos de dirección deficiente,Conflicto de rol,Falta de Claridad en las funciones,Incorrecta distribución del trabajo,Turnos rotativos,Relaciones interpersonales,inestabilidad laboral,Amenaza Delincuencial,Otros __________".split(
                    ",")
                data["listanumbers"] = "1,2,3,4,5,6,7,8,9,10,11,12,13,14".split(",")
                data["listanumberssix"] = "1,2,3,4,5,6".split(",")

                data['preload_json'] = json.dumps({
                    "antecedentes": [], "incidentes": [], "actividades": [],
                    "examenes": [], "diagnosticos": [], "certificado": {}
                })
                data['TIPO_EVALUACION_CHOICES'] = TIPO_EVALUACION_CHOICES
                data['APTITUD_MEDICA'] = APTITUD_MEDICA
                data['RESPUESTA_SIMPLE'] = RESPUESTA_SIMPLE
                data['OPCIONES_RESPUESTA'] = OPCIONES_RESPUESTA

                template = get_template("sistemamedico/evaluacionmedica/evaluacion_tabs.html")
                return JsonResponse({"result": True, "data": template.render(data, request)})

            except Exception as ex:
                import traceback
                return JsonResponse({"result": False, "mensaje": traceback.format_exc()})

        # MODAL EDIT EVALUACION
        if action == 'editevaluacion':
            ev = EvaluacionMedicaOcupacional.objects.get(pk=request.GET['id'])
            data['id'] = ev.id
            data['action'] = 'editevaluacion'
            data['title_modal'] = 'Editar evaluación FEMO'

            initial = {
                # aquí pones TODOS los campos del form (igual como ya venías)
                'profesional': ev.profesional_id,
                'institucion_sistema': ev.institucion_sistema,
                'ruc': ev.ruc,
                'ciu': ev.ciu,
                'establecimiento_trabajo': ev.establecimiento_trabajo,
                'numero_historia_clinica': ev.numero_historia_clinica,
                'numero_archivo': ev.numero_archivo,
                'puesto_trabajo_ciu': ev.puesto_trabajo_ciu,
                'grupo_atencion_prioritaria': ev.grupo_atencion_prioritaria,
                'fecha_atencion': ev.fecha_atencion,
                'fecha_ingreso_trabajo': ev.fecha_ingreso_trabajo,
                'fecha_reintegro': ev.fecha_reintegro,
                'fecha_ultimo_dia_laboral': ev.fecha_ultimo_dia_laboral,
                'tipo_evaluacion': ev.tipo_evaluacion,
                'motivo_consulta': ev.motivo_consulta,
                'aptitud_medica': ev.aptitud_medica,
                'aptitud_detalle_observaciones': ev.aptitud_detalle_observaciones,
                'recomendaciones_tratamiento': ev.recomendaciones_tratamiento,
            }
            data['form'] = form_ = EvaluacionMedicaOcupacionalForm(initial=initial)
            if ev.persona:
                form_.cargar_persona(ev.persona)

            data["preload_json"] = json.dumps({
                "antecedentes": list(ev.antecedentes_laborales.filter(status=True).values(
                    "id", "empresa", "puesto", "actividad", "tiempo", "riesgos", "epp", "observaciones"
                )),
                "incidentes": list(ev.incidentes_ocupacionales.filter(status=True).values(
                    "id", "puesto_trabajo", "actividad_desempenada", "fecha", "descripcion",
                    "calificado_por_instituto", "reubicacion", "observaciones"
                )),
                "actividades": list(ev.actividades_extralaborales.filter(status=True).values(
                    "id", "tipo_actividad", "frecuencia", "observaciones"
                )),
                "examenes": list(ev.examenes.filter(status=True).values(
                    "id", "nombre_examen", "fecha", "resultados", "observaciones"
                )),
                "diagnosticos": list(ev.diagnosticos.filter(status=True).values(
                    "id", "cie10", "descripcion", "presuntivo", "definitivo"
                )),
                "certificado": (lambda c: {
                    "fecha_emision": c.fecha_emision.strftime("%Y-%m-%d") if c and c.fecha_emision else "",
                    "aptitud_medica": c.aptitud_medica if c else "",
                    "detalle_observaciones": c.detalle_observaciones if c else "",
                    "recomendaciones": c.recomendaciones if c else "",
                    "firma_huella_trabajador": c.firma_huella_trabajador if c else "",
                })(getattr(ev, "certificado", None))
            }, ensure_ascii=False, default=str)

            template = get_template("sistemamedico/evaluacionmedica/evaluacion_tabs.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

        if action == 'ver_evaluacion':
            ev = EvaluacionMedicaOcupacional.objects.get(pk=request.GET['id'])
            data['id'] = ev.id
            data['title_modal'] = 'Evaluación FEMO'

            initial = {
                # aquí pones TODOS los campos del form (igual como ya venías)
                'profesional': ev.profesional_id,
                'institucion_sistema': ev.institucion_sistema,
                'ruc': ev.ruc,
                'ciu': ev.ciu,
                'establecimiento_trabajo': ev.establecimiento_trabajo,
                'numero_historia_clinica': ev.numero_historia_clinica,
                'numero_archivo': ev.numero_archivo,
                'puesto_trabajo_ciu': ev.puesto_trabajo_ciu,
                'grupo_atencion_prioritaria': ev.grupo_atencion_prioritaria,
                'fecha_atencion': ev.fecha_atencion,
                'fecha_ingreso_trabajo': ev.fecha_ingreso_trabajo,
                'fecha_reintegro': ev.fecha_reintegro,
                'fecha_ultimo_dia_laboral': ev.fecha_ultimo_dia_laboral,
                'tipo_evaluacion': ev.tipo_evaluacion,
                'motivo_consulta': ev.motivo_consulta,
                'aptitud_medica': ev.aptitud_medica,
                'aptitud_detalle_observaciones': ev.aptitud_detalle_observaciones,
                'recomendaciones_tratamiento': ev.recomendaciones_tratamiento,
            }
            data['form'] = form_ = EvaluacionMedicaOcupacionalForm(initial=initial)
            if ev.persona:
                form_.cargar_persona(ev.persona)

            data["preload_json"] = json.dumps({
                "antecedentes": list(ev.antecedentes_laborales.filter(status=True).values(
                    "id", "empresa", "puesto", "actividad", "tiempo", "riesgos", "epp", "observaciones"
                )),
                "incidentes": list(ev.incidentes_ocupacionales.filter(status=True).values(
                    "id", "puesto_trabajo", "actividad_desempenada", "fecha", "descripcion",
                    "calificado_por_instituto", "reubicacion", "observaciones"
                )),
                "actividades": list(ev.actividades_extralaborales.filter(status=True).values(
                    "id", "tipo_actividad", "frecuencia", "observaciones"
                )),
                "examenes": list(ev.examenes.filter(status=True).values(
                    "id", "nombre_examen", "fecha", "resultados", "observaciones"
                )),
                "diagnosticos": list(ev.diagnosticos.filter(status=True).values(
                    "id", "cie10", "descripcion", "presuntivo", "definitivo"
                )),
                "certificado": (lambda c: {
                    "fecha_emision": c.fecha_emision.strftime("%Y-%m-%d") if c and c.fecha_emision else "",
                    "aptitud_medica": c.aptitud_medica if c else "",
                    "detalle_observaciones": c.detalle_observaciones if c else "",
                    "recomendaciones": c.recomendaciones if c else "",
                    "firma_huella_trabajador": c.firma_huella_trabajador if c else "",
                })(getattr(ev, "certificado", None))
            }, ensure_ascii=False, default=str)

            template = get_template("sistemamedico/evaluacionmedica/ver_evaluacion.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})


        # MODAL ADD ANTECEDENTE (recibe evaluacion_id)
        if action == 'addantecedente':
            evaluacion_id = request.GET.get('evaluacion_id')
            data.update({
                'form': AntecedenteLaboralForm(),
                'action': 'addantecedente',
                'title_modal': 'Nuevo antecedente laboral',
                'extra_hidden': f'<input type="hidden" name="evaluacion_id" value="{evaluacion_id}">'
            })
            template = get_template("base/form.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

        # MODAL EDIT ANTECEDENTE
        if action == 'editantecedente':
            det = AntecedenteLaboral.objects.get(pk=request.GET.get('id'))
            initial = {
                'empresa': det.empresa,
                'puesto': det.puesto,
                'actividad': det.actividad,
                'tiempo': det.tiempo,
                'riesgos': det.riesgos,
                'epp': det.epp,
                'observaciones': det.observaciones,
            }
            data.update({
                'id': det.id,
                'form': AntecedenteLaboralForm(initial=initial),
                'action': 'editantecedente',
                'title_modal': 'Editar antecedente laboral'
            })
            template = get_template("base/form.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

        if action == 'list_antecedentes':
            ev = EvaluacionMedicaOcupacional.objects.get(pk=request.GET['evaluacion_id'])
            data['evaluacion'] = ev
            data['antecedentes'] = ev.antecedentes_laborales.filter(status=True)
            tpl = "sistemamedico/evaluacionmedica/modals/antecedentes_list.html"

        if action == 'list_incidentes':
            ev = EvaluacionMedicaOcupacional.objects.get(pk=request.GET['evaluacion_id'])
            data['incidentes'] = ev.incidentes_ocupacionales.filter(status=True)
            tpl = "sistemamedico/evaluacionmedica/modals/incidentes_list.html"

        if action == 'list_actividades':
            ev = EvaluacionMedicaOcupacional.objects.get(pk=request.GET['evaluacion_id'])
            data['actividades'] = ev.actividades_extralaborales.filter(status=True)
            tpl = "sistemamedico/evaluacionmedica/modals/actividades_list.html"

        if action == 'list_examenes':
            ev = EvaluacionMedicaOcupacional.objects.get(pk=request.GET['evaluacion_id'])
            data['examenes'] = ev.examenes.filter(status=True)
            tpl = "sistemamedico/evaluacionmedica/modals/examenes_list.html"

        if action == 'list_diagnosticos':
            ev = EvaluacionMedicaOcupacional.objects.get(pk=request.GET['evaluacion_id'])
            data['diagnosticos'] = ev.diagnosticos.filter(status=True)
            tpl = "sistemamedico/evaluacionmedica/modals/diagnosticos_list.html"

        if action == 'view_certificado':
            ev = EvaluacionMedicaOcupacional.objects.get(pk=request.GET['evaluacion_id'])
            data['certificado'] = getattr(ev, 'certificado', None)
            tpl = "sistemamedico/evaluacionmedica/modals/certificado_view.html"

        # Render común
        if action.startswith('list_') or action == 'view_certificado':
            template = get_template(tpl)
            return JsonResponse({"result": True, "data": template.render(data, request)})

        if action == 'generar_femo':
            try:
                WKHTMLTOPDF_CMD = r"D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
                ev = EvaluacionMedicaOcupacional.objects.get(pk=int(request.GET['id']))

                texto = "Temperaturas altas,Temperaturas bajas,Radiación Ionizante,Radiación No Ionizante,Ruido,Vibración,Iluminación,Ventilación,Fluido eléctrico,Otros __________"
                textoseguridad = "Atrapamiento entre Máquinas y o superficies,Atrapamiento entre objetos,Caída de objetos,Caídas al mismo nivel,Caídas a diferente nivel,Pinchazos,Cortes,Choques /colisión vehicular,Atropellamientos por vehículos,Proyección de fluidos,Proyección de partículas – fragmentos,Contacto con superficies de trabajos"
                textoquimicos = "Polvos,Sólidos,Humos,líquidos,vapores,Aerosoles,Neblinas,Gaseosos,Otros __________"
                textobiologicos = "Virus,Hongos,Bacterias,Parásitos,Exposición a vectores,Exposición a animales selváticos,Otros __________"
                textoergonomicos = "Manejo manual de cargas,Movimiento repetitivos,Posturas forzadas,Trabajos con PVD,Diseño Inadecuado del puesto,Otros __________"
                textopsicosociales = "Monotonía del trabajo,Sobrecarga laboral,Minuciosidad de la tarea,Alta responsabilidad,Autonomía en la toma de decisiones,Supervisión y estilos de dirección deficiente,Conflicto de rol,Falta de Claridad en las funciones,Incorrecta distribución del trabajo,Turnos rotativos,Relaciones interpersonales,inestabilidad laboral,Amenaza Delincuencial,Otros __________"
                textonumbers = "1,2,3,4,5,6,7,8,9,10,11,12,13,14"
                textonumberssix = "1,2,3,4,5,6"
                lista = texto.split(",")
                listaseguridad = textoseguridad.split(",")
                listaquimicos= textoquimicos.split(",")
                listabiologicos = textobiologicos.split(",")
                listaergonomicos = textoergonomicos.split(",")
                listapsicosociales = textopsicosociales.split(",")
                listanumbers = textonumbers.split(",")
                listanumberssix = textonumberssix.split(",")

                data['lista'] = lista

                antecedentes = list(ev.antecedentes_laborales.filter(status=True).values())
                incidentes = list(ev.incidentes_ocupacionales.filter(status=True).values())
                actividades = list(ev.actividades_extralaborales.filter(status=True).values())
                examenes = list(ev.examenes.filter(status=True).values())
                diagnosticos = list(ev.diagnosticos.filter(status=True).values())

                # Ajusta tamaños por página según tu layout real
                ant_pages = chunk(antecedentes, 12)
                inc_pages = chunk(incidentes, 10)
                act_pages = chunk(actividades, 12)
                exa_pages = chunk(examenes, 10)
                dia_pages = chunk(diagnosticos, 12)

                max_pages = max(len(ant_pages), len(inc_pages), len(act_pages), len(exa_pages), len(dia_pages))

                anexo2_pages = []
                for i in range(max_pages):
                    anexo2_pages.append({
                        "antecedentes": ant_pages[i] if i < len(ant_pages) else [],
                        "incidentes": inc_pages[i] if i < len(inc_pages) else [],
                        "actividades": act_pages[i] if i < len(act_pages) else [],
                        "examenes": exa_pages[i] if i < len(exa_pages) else [],
                        "diagnosticos": dia_pages[i] if i < len(dia_pages) else [],
                    })

                html = render_to_string("sistemamedico/evaluacionmedica/reporte_femo.html", {
                    "ev": ev,
                    "anexo2_pages": anexo2_pages,
                    "lista": lista,
                    "listaseguridad": listaseguridad,
                    "listaquimicos": listaquimicos,
                    "listabiologicos": listabiologicos,
                    "listaergonomicos": listaergonomicos,
                    "listapsicosociales": listapsicosociales,
                    "listanumbers": listanumbers,
                    "listanumberssix": listanumberssix,
                })

                with tempfile.TemporaryDirectory() as tmp:
                    html_path = os.path.join(tmp, "femo.html")
                    pdf_path = os.path.join(tmp, "femo.pdf")

                    # 1) Guardar HTML
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html)

                    # 2) Ejecutar wkhtmltopdf
                    cmd = [
                        WKHTMLTOPDF_CMD,
                        "--page-size", "A4",
                        "--encoding", "utf-8",
                        "--enable-local-file-access",
                        html_path,
                        pdf_path,
                    ]

                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        shell=False  # IMPORTANTE
                    )

                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)

                    # 3) VALIDAR ejecución
                    if result.returncode != 0:
                        raise Exception("wkhtmltopdf falló, revisa stderr")

                    # 4) VALIDAR que el PDF exista
                    if not os.path.exists(pdf_path):
                        raise FileNotFoundError("wkhtmltopdf no generó el PDF")

                    # 5) Leer PDF
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                resp = HttpResponse(pdf_bytes, content_type="application/pdf")
                resp["Content-Disposition"] = f'inline; filename="FEMO_{ev.id}.pdf"'
                return resp
            except Exception as ex:
                pass

        return JsonResponse({"result": False, "mensaje": "Acción GET no reconocida."})

    data['title'] = u'Evaluaciones FEMO'
    request.session['viewactivo'] = 1

    search = request.GET.get('s', '')
    url_vars = f''
    filtro = Q(status=True)

    if search:
        data['s'] = search
        filtro &= Q(numero_historia_clinica__icontains=search) | Q(numero_archivo__icontains=search)
        url_vars += f'&s={search}'

    listado = EvaluacionMedicaOcupacional.objects.filter(filtro).order_by('-id')
    paging = MiPaginador(listado, 10)
    p = int(request.GET.get('page', request.session.get('paginador', 1)))

    try:
        page = paging.page(p)
    except:
        p = 1
        page = paging.page(p)

    request.session['paginador'] = p
    data.update({
        'paging': paging,
        'url_vars': url_vars,
        'rangospaging': paging.rangos_paginado(p),
        'page': page,
        'listado': page.object_list
    })
    data['title'] = u'Evaluaciones FEMO'
    return render(request, 'sistemamedico/evaluacionmedica/view.html', data)

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
from base.funciones import MiPaginador
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
                    form = EvaluacionMedicaOcupacionalForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse(
                            {'result': True, 'mensaje': 'El formulario no ha sido completado correctamente.'})

                    if not profesional_:
                        return JsonResponse({'result': True, 'mensaje': 'Usted no cuenta como Profesional de la salud autorizado.'})

                    ev = EvaluacionMedicaOcupacional(
                        persona_id=form.cleaned_data.get('persona') or None,
                        profesional=profesional_,
                        institucion_sistema=form.cleaned_data.get('institucion_sistema'),
                        ruc=form.cleaned_data.get('ruc'),
                        ciu=form.cleaned_data.get('ciu'),
                        establecimiento_trabajo=form.cleaned_data.get('establecimiento_trabajo'),
                        numero_historia_clinica=form.cleaned_data.get('numero_historia_clinica'),
                        numero_archivo=form.cleaned_data.get('numero_archivo'),
                        puesto_trabajo_ciu=form.cleaned_data.get('puesto_trabajo_ciu'),
                        grupo_atencion_prioritaria=form.cleaned_data.get('grupo_atencion_prioritaria'),
                        fecha_atencion=form.cleaned_data.get('fecha_atencion'),
                        fecha_ingreso_trabajo=form.cleaned_data.get('fecha_ingreso_trabajo'),
                        fecha_reintegro=form.cleaned_data.get('fecha_reintegro'),
                        fecha_ultimo_dia_laboral=form.cleaned_data.get('fecha_ultimo_dia_laboral'),
                        tipo_evaluacion=form.cleaned_data.get('tipo_evaluacion'),
                        motivo_consulta=form.cleaned_data.get('motivo_consulta'),
                        aptitud_medica=form.cleaned_data.get('aptitud_medica'),
                        aptitud_detalle_observaciones=form.cleaned_data.get('aptitud_detalle_observaciones'),
                        recomendaciones_tratamiento=form.cleaned_data.get('recomendaciones_tratamiento'),
                    )
                    ev.save(request)

                    # ====== N registros ======
                    antecedentes = json.loads(request.POST.get("antecedentes_json", "[]"))
                    incidentes = _parse_json_list(request.POST.get('incidentes_json'))
                    actividades = _parse_json_list(request.POST.get('actividades_json'))
                    examenes = _parse_json_list(request.POST.get('examenes_json'))
                    diagnosticos = _parse_json_list(request.POST.get('diagnosticos_json'))

                    for a in antecedentes:
                        _id = a.get("id")

                        payload = dict(
                            empresa=a.get("empresa", ""),
                            puesto=a.get("puesto", ""),
                            actividad=a.get("actividad", ""),
                            tiempo=a.get("tiempo", ""),
                            riesgos=a.get("riesgos", ""),
                            epp=a.get("epp", ""),
                            observaciones=a.get("observaciones", ""),
                        )

                        if _id:
                            # ✅ Update SOLO si el id pertenece a esa evaluación
                            AntecedenteLaboral.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            # ✅ Create nuevo
                            AntecedenteLaboral.objects.create(evaluacion=ev, **payload)

                    if incidentes:
                        IncidenteAccidenteEnfermedadOcupacional.objects.bulk_create([
                            IncidenteAccidenteEnfermedadOcupacional(
                                evaluacion=ev,
                                puesto_trabajo=i.get('puesto_trabajo'),
                                actividad_desempenada=i.get('actividad_desempenada'),
                                fecha=i.get('fecha') or None,
                                descripcion=i.get('descripcion'),
                                calificado_por_instituto=bool(i.get('calificado_por_instituto')),
                                reubicacion=bool(i.get('reubicacion')),
                                observaciones=i.get('observaciones'),
                            ) for i in incidentes
                        ])

                    if actividades:
                        ActividadExtraLaboral.objects.bulk_create([
                            ActividadExtraLaboral(
                                evaluacion=ev,
                                tipo_actividad=x.get('tipo_actividad'),
                                frecuencia=x.get('frecuencia'),
                                observaciones=x.get('observaciones'),
                            ) for x in actividades
                        ])

                    if examenes:
                        ExamenGeneralEspecifico.objects.bulk_create([
                            ExamenGeneralEspecifico(
                                evaluacion=ev,
                                nombre_examen=e.get('nombre_examen'),
                                fecha=e.get('fecha') or None,
                                resultados=e.get('resultados'),
                                observaciones=e.get('observaciones'),
                            ) for e in examenes
                        ])

                    if diagnosticos:
                        Diagnostico.objects.bulk_create([
                            Diagnostico(
                                evaluacion=ev,
                                cie10=d.get('cie10'),
                                descripcion=d.get('descripcion'),
                                presuntivo=bool(d.get('presuntivo')),
                                definitivo=bool(d.get('definitivo')),
                            ) for d in diagnosticos
                        ])

                    # ====== Certificado (1) ======
                    cert = _parse_json_dict(request.POST.get('certificado_json'))
                    # solo crear si al menos hay algo
                    if any((cert.get(k) or "").strip() for k in
                           ["fecha_emision", "aptitud_medica", "detalle_observaciones", "recomendaciones",
                            "firma_huella_trabajador"]):
                        CertificadoEvaluacionMedicaOcupacional.objects.create(
                            evaluacion=ev,
                            fecha_emision=cert.get('fecha_emision') or None,
                            aptitud_medica=cert.get('aptitud_medica') or None,
                            detalle_observaciones=cert.get('detalle_observaciones') or None,
                            recomendaciones=cert.get('recomendaciones') or None,
                            firma_huella_trabajador=cert.get('firma_huella_trabajador') or None,
                        )

                    #log(u'Adicionó evaluación FEMO: %s' % ev.id, request, 'add')
                    return JsonResponse({'result': False, 'mensaje': 'Guardado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al guardar: {str(ex)}'})

        # =========================
        # EVALUACION: EDIT
        # =========================
        if action == 'editevaluacion':
            try:
                with transaction.atomic():
                    form = EvaluacionMedicaOcupacionalForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse(
                            {'result': True, 'mensaje': 'El formulario no ha sido completado correctamente.'})

                    ev = EvaluacionMedicaOcupacional.objects.get(pk=request.POST['id'])

                    # actualizar campos 1 registro
                    ev.persona_id = form.cleaned_data.get('persona') or None
                    ev.profesional_id = form.cleaned_data.get('profesional') or None
                    ev.institucion_sistema = form.cleaned_data.get('institucion_sistema')
                    ev.ruc = form.cleaned_data.get('ruc')
                    ev.ciu = form.cleaned_data.get('ciu')
                    ev.establecimiento_trabajo = form.cleaned_data.get('establecimiento_trabajo')
                    ev.numero_historia_clinica = form.cleaned_data.get('numero_historia_clinica')
                    ev.numero_archivo = form.cleaned_data.get('numero_archivo')
                    ev.puesto_trabajo_ciu = form.cleaned_data.get('puesto_trabajo_ciu')
                    ev.grupo_atencion_prioritaria = form.cleaned_data.get('grupo_atencion_prioritaria')
                    ev.fecha_atencion = form.cleaned_data.get('fecha_atencion')
                    ev.fecha_ingreso_trabajo = form.cleaned_data.get('fecha_ingreso_trabajo')
                    ev.fecha_reintegro = form.cleaned_data.get('fecha_reintegro')
                    ev.fecha_ultimo_dia_laboral = form.cleaned_data.get('fecha_ultimo_dia_laboral')
                    ev.tipo_evaluacion = form.cleaned_data.get('tipo_evaluacion')
                    ev.motivo_consulta = form.cleaned_data.get('motivo_consulta')
                    ev.aptitud_medica = form.cleaned_data.get('aptitud_medica')
                    ev.aptitud_detalle_observaciones = form.cleaned_data.get('aptitud_detalle_observaciones')
                    ev.recomendaciones_tratamiento = form.cleaned_data.get('recomendaciones_tratamiento')
                    ev.save(request)

                    # marcar como inactivos los detalles anteriores (delete lógico)
                    # ev.antecedentes_laborales.filter(status=True).update(status=False)
                    # ev.incidentes_ocupacionales.filter(status=True).update(status=False)
                    # ev.actividades_extralaborales.filter(status=True).update(status=False)
                    # ev.examenes.filter(status=True).update(status=False)
                    # ev.diagnosticos.filter(status=True).update(status=False)

                    # =============================
                    # JSON payloads (N)
                    # =============================
                    antecedentes = _loads_list(request.POST.get("antecedentes_json"))
                    incidentes = _loads_list(request.POST.get("incidentes_json"))
                    actividades = _loads_list(request.POST.get("actividades_json"))
                    examenes = _loads_list(request.POST.get("examenes_json"))
                    diagnosticos = _loads_list(request.POST.get("diagnosticos_json"))
                    certificado = _loads_list(request.POST.get("certificado_json"))  # OJO: aquí es dict, lo trato abajo

                    antecedentes_deleted = _loads_list(request.POST.get("antecedentes_deleted"))
                    incidentes_deleted = _loads_list(request.POST.get("incidentes_deleted"))
                    actividades_deleted = _loads_list(request.POST.get("actividades_deleted"))
                    examenes_deleted = _loads_list(request.POST.get("examenes_deleted"))
                    diagnosticos_deleted = _loads_list(request.POST.get("diagnosticos_deleted"))

                    # =============================
                    # DELETE por sección
                    # =============================
                    if antecedentes_deleted:
                        AntecedenteLaboral.objects.filter(evaluacion=ev, id__in=antecedentes_deleted).delete()

                    if incidentes_deleted:
                        IncidenteAccidenteEnfermedadOcupacional.objects.filter(evaluacion=ev,
                                                                               id__in=incidentes_deleted).delete()

                    if actividades_deleted:
                        ActividadExtraLaboral.objects.filter(evaluacion=ev, id__in=actividades_deleted).delete()

                    if examenes_deleted:
                        ExamenGeneralEspecifico.objects.filter(evaluacion=ev, id__in=examenes_deleted).delete()

                    if diagnosticos_deleted:
                        Diagnostico.objects.filter(evaluacion=ev, id__in=diagnosticos_deleted).delete()

                    # =============================
                    # UPSERT: ANTECEDENTES
                    # =============================
                    for a in antecedentes:
                        _id = a.get("id")
                        _id = int(_id) if _id not in (None, "", "null") else None
                        payload = dict(
                            empresa=a.get("empresa", ""),
                            puesto=a.get("puesto", ""),
                            actividad=a.get("actividad", ""),
                            tiempo=a.get("tiempo", ""),
                            riesgos=a.get("riesgos", ""),
                            epp=a.get("epp", ""),
                            observaciones=a.get("observaciones", ""),
                        )
                        if _id:
                            AntecedenteLaboral.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            AntecedenteLaboral.objects.create(evaluacion=ev, **payload)

                    # =============================
                    # UPSERT: INCIDENTES
                    # =============================
                    for i in incidentes:
                        _id = i.get("id")
                        _id = int(_id) if _id not in (None, "", "null") else None
                        payload = dict(
                            puesto_trabajo=i.get("puesto_trabajo", ""),
                            actividad_desempenada=i.get("actividad_desempenada", ""),
                            fecha=_to_date(i.get("fecha")),
                            descripcion=i.get("descripcion", ""),
                            calificado_por_instituto=_to_bool(i.get("calificado_por_instituto")),
                            reubicacion=_to_bool(i.get("reubicacion")),
                            observaciones=i.get("observaciones", ""),
                        )
                        if _id:
                            IncidenteAccidenteEnfermedadOcupacional.objects.filter(id=_id, evaluacion=ev).update(
                                **payload)
                        else:
                            IncidenteAccidenteEnfermedadOcupacional.objects.create(evaluacion=ev, **payload)

                    # =============================
                    # UPSERT: ACTIVIDADES EXTRA
                    # =============================
                    for x in actividades:
                        _id = x.get("id")
                        _id = int(_id) if _id not in (None, "", "null") else None
                        payload = dict(
                            tipo_actividad=x.get("tipo_actividad", ""),
                            frecuencia=x.get("frecuencia", ""),
                            observaciones=x.get("observaciones", ""),
                        )
                        if _id:
                            ActividadExtraLaboral.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            ActividadExtraLaboral.objects.create(evaluacion=ev, **payload)

                    # =============================
                    # UPSERT: EXÁMENES
                    # =============================
                    for e in examenes:
                        _id = e.get("id")
                        _id = int(_id) if _id not in (None, "", "null") else None
                        payload = dict(
                            nombre_examen=e.get("nombre_examen", ""),
                            fecha=_to_date(e.get("fecha")),
                            resultados=e.get("resultados", ""),
                            observaciones=e.get("observaciones", ""),
                        )
                        if _id:
                            ExamenGeneralEspecifico.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            ExamenGeneralEspecifico.objects.create(evaluacion=ev, **payload)

                    # =============================
                    # UPSERT: DIAGNÓSTICOS
                    # =============================
                    for d in diagnosticos:
                        _id = d.get("id")
                        _id = int(_id) if _id not in (None, "", "null") else None
                        payload = dict(
                            cie10=d.get("cie10", ""),
                            descripcion=d.get("descripcion", ""),
                            presuntivo=_to_bool(d.get("presuntivo")),
                            definitivo=_to_bool(d.get("definitivo")),
                        )
                        if _id:
                            Diagnostico.objects.filter(id=_id, evaluacion=ev).update(**payload)
                        else:
                            Diagnostico.objects.create(evaluacion=ev, **payload)

                    # =============================
                    # CERTIFICADO (OneToOne) UPSERT
                    # Tu JS manda un objeto, no lista:
                    # =============================
                    try:
                        cert = json.loads(request.POST.get("certificado_json") or "{}")
                    except Exception:
                        cert = {}

                    # Si está vacío, no hago nada
                    if any((cert.get(k) or "").strip() for k in
                           ["fecha_emision", "aptitud_medica", "detalle_observaciones", "recomendaciones",
                            "firma_huella_trabajador"]):
                        CertificadoEvaluacionMedicaOcupacional.objects.update_or_create(
                            evaluacion=ev,
                            defaults=dict(
                                fecha_emision=_to_date(cert.get("fecha_emision")),
                                aptitud_medica=cert.get("aptitud_medica") or None,
                                detalle_observaciones=cert.get("detalle_observaciones", ""),
                                recomendaciones=cert.get("recomendaciones", ""),
                                firma_huella_trabajador=cert.get("firma_huella_trabajador", ""),
                            )
                        )

                    #log(u'Editó evaluación FEMO: %s' % ev.id, request, 'edit')
                    return JsonResponse({'result': False, 'mensaje': 'Actualizado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al actualizar: {str(ex)}'})

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
            data['action'] = 'addevaluacion'
            data['title_modal'] = 'Nueva evaluación FEMO'
            data['form'] = EvaluacionMedicaOcupacionalForm()
            data['preload_json'] = json.dumps({
                "antecedentes": [],
                "incidentes": [],
                "actividades": [],
                "examenes": [],
                "diagnosticos": [],
                "certificado": {}
            })
            template = get_template("sistemamedico/evaluacionmedica/evaluacion_tabs.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

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

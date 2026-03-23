import json
from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template

from .models import EvaluacionMedicaOcupacional, Trabajador, ProfesionalSalud, AntecedenteLaboral
from .forms import EvaluacionMedicaOcupacionalForm, AntecedenteLaboralForm, PersonaForm
from saas.vistaprincipal import act_info
from saas.models import *
from base.funciones import MiPaginador

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


def view(request):
    data = {}
    act_info(request, data)
    persona = request.session.get('persona')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        data['action'] = action

        # =========================
        # PERSONA: ADD
        # =========================
        if action == 'addpersona':
            try:
                with transaction.atomic():
                    form = PersonaForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse(
                            {'result': True, 'mensaje': 'El formulario no ha sido completado correctamente.'})

                    persona_ = Persona(
                        tipo_persona=form.cleaned_data.get('tipo_persona') or None,
                        tipo_identificacion=form.cleaned_data.get('tipo_identificacion') or None,
                        identificacion=form.cleaned_data.get('identificacion'),
                        nombres=form.cleaned_data.get('nombres'),
                        primerapellido=form.cleaned_data.get('primerapellido'),
                        segundoapellido=form.cleaned_data.get('segundoapellido'),
                        email=form.cleaned_data.get('email'),
                        telefono=form.cleaned_data.get('telefono'),
                        direccion=form.cleaned_data.get('direccion'),
                        activo=form.cleaned_data.get('activo')
                    )
                    persona_.save(request)

                    return JsonResponse({'result': False, 'mensaje': 'Guardado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al guardar: {str(ex)}'})

        # =========================
        # EVALUACION: EDIT
        # =========================
        if action == 'editpersona':
            try:
                with transaction.atomic():
                    form = PersonaForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse(
                            {'result': True, 'mensaje': 'El formulario no ha sido completado correctamente.'})

                    ev = Persona.objects.get(pk=request.POST['id'])

                    # actualizar campos 1 registro
                    ev.tipo_persona = form.cleaned_data.get('tipo_persona') or None
                    ev.tipo_identificacion = form.cleaned_data.get('tipo_identificacion') or None
                    ev.identificacion = form.cleaned_data.get('identificacion')
                    ev.nombres = form.cleaned_data.get('nombres')
                    ev.primerapellido = form.cleaned_data.get('primerapellido')
                    ev.segundoapellido = form.cleaned_data.get('segundoapellido')
                    ev.email = form.cleaned_data.get('email')
                    ev.telefono = form.cleaned_data.get('telefono')
                    ev.direccion = form.cleaned_data.get('direccion')
                    ev.activo = form.cleaned_data.get('activo')
                    ev.save(request)
                    return JsonResponse({'result': False, 'mensaje': 'Actualizado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al actualizar: {str(ex)}'})

        # =========================
        # EVALUACION: DELETE LOGICO
        # =========================
        if action == 'delpersona':
            try:
                persona_ = Persona.objects.get(pk=request.POST.get('id'))
                persona_.status = False
                persona_.save(request)
                return JsonResponse({"error": False, "refresh": True, "mensaje": "Se ha eliminado correctamente el registro."})
            except Exception:
                transaction.set_rollback(True)
                return JsonResponse({"error": True, "mensaje": "Ha ocurrido un error al eliminar la persona."})

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

        if action == 'data':
            try:
                m = request.GET['model']
                if 'q' in request.GET:
                    q = request.GET['q'].upper().strip()
                    if ':' in m:
                        sp = m.split(':')
                        model = eval(sp[0])
                        if len(sp) > 1:
                            query = model.flexbox_query(q, extra=sp[1])
                        else:
                            query = model.flexbox_query(q)
                    else:
                        model = eval(request.GET['model'])
                        query = model.flexbox_query(q)
                else:
                    m = request.GET['model']
                    if ':' in m:
                        sp = m.split(':')
                        model = eval(sp[0])
                        resultquery = model.flexbox_query('')
                        try:
                            query = eval('resultquery.filter(%s, status=True).distinct()' % (sp[1]))
                        except Exception as ex:
                            query = resultquery
                    else:
                        model = eval(request.GET['model'])
                        query = model.flexbox_query('')
                data = {"result": "ok", "results": [{"id": x.id, "name": x.flexbox_repr(),
                                                     'alias': x.flexbox_alias() if hasattr(x, 'flexbox_alias') else []}
                                                    for x in query]}
                return JsonResponse(data)
            except Exception as ex:
                return JsonResponse({"result": "bad", 'mensaje': u'Error al obtener los datos.'})

        return JsonResponse({"result": False, "mensaje": "Acción GET no reconocida."})


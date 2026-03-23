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

                    persona_.create_perfil_administrativo(request)
                    persona_.create_user(request)

                    return JsonResponse({'result': False, 'mensaje': 'Guardado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al guardar: {str(ex)}'})

        if action == 'create_perfil_administrativo':
            try:
                with transaction.atomic():
                    persona_ = Persona.objects.get(id=int(request.POST['id']))
                    persona_.create_perfil_administrativo(request)
                    return JsonResponse({'result': True, 'mensaje': 'Perfil creado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': False, 'mensaje': f'Error al guardar: {str(ex)}'})

        if action == 'create_perfil_profesional':
            try:
                with transaction.atomic():
                    persona_ = Persona.objects.get(id=int(request.POST['id']))
                    persona_.create_perfil_profesional(request)
                    return JsonResponse({'result': True, 'mensaje': 'Perfil creado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': False, 'mensaje': f'Error al guardar: {str(ex)}'})

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
        data['action'] = action

        # MODAL ADD EVALUACION
        if action == 'addpersona':
            data['title_modal'] = 'Nueva persona'
            data['form'] = PersonaForm()
            template = get_template("base/form.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

        # MODAL EDIT EVALUACION
        if action == 'editpersona':
            ev = Persona.objects.get(pk=request.GET['id'])
            data['id'] = ev.id
            data['title_modal'] = 'Editar persona'

            initial = {
                # aquí pones TODOS los campos del form (igual como ya venías)
                'tipo_persona': ev.tipo_persona,
                'tipo_identificacion': ev.tipo_identificacion,
                'identificacion': ev.identificacion,
                'nombres': ev.nombres,
                'primerapellido': ev.primerapellido,
                'segundoapellido': ev.segundoapellido,
                'email': ev.email,
                'telefono': ev.telefono,
                'direccion': ev.direccion,
                'activo': ev.activo
            }
            data['form'] = PersonaForm(initial=initial)

            template = get_template("base/form.html")
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

        return JsonResponse({"result": False, "mensaje": "Acción GET no reconocida."})

    data['title'] = u'Personas'
    request.session['viewactivo'] = 2

    search = request.GET.get('s', '')
    url_vars = f''
    filtro = Q(status=True)

    if search:
        data['s'] = search
        filtro &= Q(nombres__icontains=search) | Q(primerapellido__icontains=search | Q(segundoapellido__icontains=search))
        url_vars += f'&s={search}'

    listado = Persona.objects.filter(filtro).order_by('-id')
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
    return render(request, 'sistemamedico/persona/view.html', data)

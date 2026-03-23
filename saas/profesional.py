import json
from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template

from .models import EvaluacionMedicaOcupacional, Trabajador, ProfesionalSalud, AntecedenteLaboral
from .forms import EvaluacionMedicaOcupacionalForm, AntecedenteLaboralForm, PersonaForm, ProfesionalSaludForm
from saas.vistaprincipal import act_info
from saas.models import *
from base.funciones import MiPaginador, calculate_username

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
        if action == 'addprofesional':
            try:
                with transaction.atomic():
                    form = PersonaForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse({'result': True, 'mensaje': 'El formulario no ha sido completado correctamente.'})

                    persona_ = Persona.objects.filter(status=True, identificacion=form.cleaned_data['identificacion']).first()
                    if persona_:
                        return JsonResponse({'result': True, 'mensaje': 'Ya existe una persona registrada con la identificación enviada.'})

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

                    persona_.create_perfil_profesional(request)

                    persona_.create_user(request)

                    return JsonResponse({'result': False, 'mensaje': 'Guardado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al guardar: {str(ex)}'})

        # =========================
        # EVALUACION: EDIT
        # =========================
        if action == 'editprofesional':
            try:
                with transaction.atomic():
                    form = ProfesionalSaludForm(request.POST)
                    if not form.is_valid():
                        return JsonResponse(
                            {'result': True, 'mensaje': 'El formulario no ha sido completado correctamente.'})

                    ev = ProfesionalSalud.objects.get(pk=request.POST['id'])

                    # actualizar campos 1 registro
                    ev.codigo_medico = form.cleaned_data.get('codigo_medico') or None
                    ev.save(request)
                    return JsonResponse({'result': False, 'mensaje': 'Actualizado con éxito'})

            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al actualizar: {str(ex)}'})

        # =========================
        # EVALUACION: DELETE LOGICO
        # =========================
        if action == 'delprofesional':
            try:
                persona_ = ProfesionalSalud.objects.get(pk=request.POST.get('id'))
                persona_.status = False
                persona_.save(request)
                return JsonResponse({"error": False, "refresh": True, "mensaje": "Se ha eliminado correctamente el registro."})
            except Exception:
                transaction.set_rollback(True)
                return JsonResponse({"error": True, "mensaje": "Ha ocurrido un error al eliminar la persona."})

        return JsonResponse({'result': True, 'mensaje': 'Acción no reconocida.'})

    # =========================
    # GET (LISTADOS + MODALES)
    # =========================
    if 'action' in request.GET:
        action = request.GET.get('action')
        data['action'] = action

        # MODAL ADD EVALUACION
        if action == 'addprofesional':
            data['title_modal'] = 'Nuevo profesional'
            data['form'] = PersonaForm()
            template = get_template("base/form.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

        # MODAL EDIT EVALUACION
        if action == 'editprofesional':
            ev = ProfesionalSalud.objects.get(pk=request.GET['id'])
            data['id'] = ev.id
            data['title_modal'] = 'Editar profesional'

            initial = {
                # aquí pones TODOS los campos del form (igual como ya venías)
                'codigo_medico': ev.codigo_medico
            }
            data['form'] = ProfesionalSaludForm(initial=initial)

            template = get_template("base/form.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

        # Render común
        if action.startswith('list_') or action == 'view_certificado':
            template = get_template(tpl)
            return JsonResponse({"result": True, "data": template.render(data, request)})

        return JsonResponse({"result": False, "mensaje": "Acción GET no reconocida."})

    data['title'] = u'Profesionales'
    request.session['viewactivo'] = 3

    search = request.GET.get('s', '')
    url_vars = f''
    filtro = Q(status=True)

    if search:
        data['s'] = search
        filtro &= Q(persona__nombres__icontains=search) | Q(persona__primerapellido__icontains=search | Q(persona__segundoapellido__icontains=search))
        url_vars += f'&s={search}'

    listado = ProfesionalSalud.objects.filter(filtro).order_by('-id')
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
    return render(request, 'sistemamedico/profesional/view.html', data)

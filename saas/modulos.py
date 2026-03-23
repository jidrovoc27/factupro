import json
from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template

from .models import EvaluacionMedicaOcupacional, Trabajador, ProfesionalSalud, AntecedenteLaboral
from .forms import EvaluacionMedicaOcupacionalForm, AntecedenteLaboralForm, PersonaForm, ModuloForm
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
        if action == 'addmodulo':
            try:
                with transaction.atomic():
                    form = ModuloForm(request.POST)
                    if form.is_valid():
                        modulo = form.guardar(request)
                        return JsonResponse({"result": False, "mensaje": "Guardado con éxito"})
                    return JsonResponse({"result": True, "mensaje": "Formulario inválido"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al guardar: {str(ex)}'})


        if action == 'editmodulo':
            try:
                with transaction.atomic():
                    modulo = Modulo.objects.get(pk=request.POST["id"])
                    form = ModuloForm(request.POST)
                    if form.is_valid():
                        modulo = form.guardar(request, modulo=modulo)
                        return JsonResponse({"result": False, "mensaje": "Editado con éxito"})
                    return JsonResponse({"result": True, "mensaje": "Formulario inválido"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({'result': True, 'mensaje': f'Error al actualizar: {str(ex)}'})

        if action == 'delmodulo':
            try:
                persona_ = Persona.objects.get(pk=request.POST.get('id'))
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

        # MODAL ADD MÓDULO
        if action == 'addmodulo':
            data['title_modal'] = 'Nuevo módulo'
            data['form'] = ModuloForm()
            template = get_template("base/form.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

        # MODAL EDIT MÓDULO
        if action == 'editmodulo':
            modulo = Modulo.objects.get(pk=request.GET["id"])
            form = ModuloForm()
            form.cargar(modulo)
            data["form"] = form
            data["action"] = "editmodulo"
            data["id"] = modulo.id
            template = get_template("base/form.html")
            return JsonResponse({"result": True, "data": template.render(data, request)})

        return JsonResponse({"result": False, "mensaje": "Acción GET no reconocida."})

    data['title'] = u'Módulos'
    request.session['viewactivo'] = 3

    search = request.GET.get('s', '')
    url_vars = f''
    filtro = Q(status=True)

    if search:
        data['s'] = search
        filtro &= Q(nombre__icontains=search)
        url_vars += f'&s={search}'

    listado = Modulo.objects.filter(filtro).order_by('-id')
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
    return render(request, 'sistemamedico/modulo/view.html', data)

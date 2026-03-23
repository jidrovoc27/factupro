import sys
import datetime
from datetime import datetime, timedelta
from django.utils import timezone

from django.core.cache import cache
from django.shortcuts import render, redirect
from django.db.models.query_utils import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, JsonResponse
from saas.models import Persona, Modulo, ModuloGrupo, CategoriaModulo, ProfesionalSalud
from base.funciones import obtener_ip_cliente_actual
from sistemamedico.settings import DEBUG
from sistemamedico import settings


def act_info(request, data):
    """
    Carga información base para templates y sesión.
    - No guarda objetos Django en session (solo IDs / strings).
    - Reduce queries repetidas.
    - Maneja faltantes sin romper.
    """
    data['rutaurl'] = request.path
    data['check_sesion'] = True
    data['currenttime'] = timezone.now()
    data["formlocation"] = True
    data['permite_modificar'] = True

    # -------------------------
    # 1) Persona de sesión (robusto)
    # -------------------------
    if not request.user.is_authenticated:
        # Para vistas públicas puedes preferir no lanzar excepción, depende de tu app:
        # data['persona_sesion'] = None
        # return data
        raise Exception('Usuario no autentificado en el sistema')

    persona_id = request.session.get('persona_id')

    # Si no hay persona_id, intenta resolverla (y guarda el id)
    if not persona_id:
        persona_sesion = (Persona.objects
                          .filter(usuario=request.user, status=True)
                          .only('id', 'razon_social', 'identificacion')  # ajusta a campos reales
                          .first())
        if not persona_sesion:
            raise Exception('El usuario no tiene Persona asociada')
        perfiladministrativo = persona_sesion.mi_perfiladministrativo()
        if not perfiladministrativo:
            raise Exception('El usuario no tiene perfil administrativo')
        request.session['persona_id'] = persona_sesion.id
        request.session['perfilprincipal'] = perfiladministrativo.id
        persona_id = persona_sesion.id
    else:
        persona_sesion = (Persona.objects
                          .filter(id=persona_id, status=True)
                          .only('id', 'razon_social', 'identificacion')
                          .first())
        if not persona_sesion:
            # Sesión desincronizada: limpia y vuelve a resolver
            request.session.pop('persona_id', None)
            raise Exception('Sesión inválida: persona no encontrada')

    data['persona_sesion'] = persona_sesion
    data['profesional_'] = profesional_ = ProfesionalSalud.objects.filter(status=True, persona_id=request.session.get('persona_id')).first()
    data['modulos'] = modulos = Modulo.objects.filter(status=True)

    # -------------------------
    # 2) Parámetros de GET (sin romper)
    # -------------------------
    if request.method == 'GET':
        for key in ('ret', 'mensj', 'info'):
            val = request.GET.get(key)
            if val is not None:
                data[key] = val

    # -------------------------
    # 3) Datos básicos desde sesión (con defaults)
    # -------------------------
    data['nombresistema'] = request.session.get('nombresistema', 'sistemamedico')
    data['tiposistema'] = request.session.get('tiposistema', '')
    data['perfiles_usuario'] = request.session.get('perfiles', [])
    data['perfilprincipal'] = request.session.get('perfilprincipal', None)
    data['eTemplateBaseSetting'] = request.session.get('eTemplateBaseSetting')

    # ultimo acceso
    request.session.setdefault('ultimo_acceso', timezone.now().isoformat())

    # remote addr (sin KeyError)
    server_name = request.META.get('SERVER_NAME', '')
    data['remoteaddr'] = f"{obtener_ip_cliente_actual(request)} - {server_name}"

    # -------------------------
    # 4) Grupos de usuario (no guardes QuerySet en sesión)
    # -------------------------
    cache_key_groups = f"user_groups:{request.user.id}"
    grupos = cache.get(cache_key_groups)
    if grupos is None:
        # lista de nombres, liviana y serializable
        grupos = list(request.user.groups.values_list('name', flat=True))
        cache.set(cache_key_groups, grupos, 300)  # 5 min
    data['grupos_usuarios'] = grupos

    # -------------------------
    # -------------------------
    # 6) Breadcrumb / ruta (con cache de módulo)
    # -------------------------
    rutalista = request.session.get('ruta')
    if not isinstance(rutalista, list) or not rutalista:
        rutalista = [['/', 'Inicio']]

    if request.path:
        path_key = request.path.lstrip('/')  # evita [1:]
        cache_key_modulo = f"modulo:url:{path_key}"
        modulo = cache.get(cache_key_modulo)
        if modulo is None:
            # Trae lo mínimo
            modulo = (Modulo.objects
                      .filter(url=path_key)
                      .only('url', 'nombre')
                      .first())
            cache.set(cache_key_modulo, modulo, 3600)

        if modulo:
            url_item = [f'/{modulo.url}', modulo.nombre]
            if url_item not in rutalista:
                # Mantener máximo 8 items (sin borrar Inicio)
                if len(rutalista) >= 8:
                    rutalista.pop(1)
                rutalista.append(url_item)
            request.session['ruta'] = rutalista

            data["url_back"] = '/'
            request.session['url_back'] = [data['url_back']]

    data["ruta"] = rutalista

    return data


def login_user(request):
    if request.user.is_authenticated:
        return redirect('/')

    data = {}
    # act_info(request, data)
    data['title'] = 'Bienvenidos a sistemamedico'

    # Redirección por host (si aplica)
    if not settings.DEBUG:
        host = request.META.get('HTTP_HOST', '')
        if 'sistemamedico' in host:
            return HttpResponseRedirect('/sistemamedico')

    # Set expiry (mejor hacerlo una vez)
    request.session.set_expiry(240 * 60)

    # client_id de apoyo
    # if 'client_id' not in request.session:
    #     sid = request.COOKIES.get('sessionid')
    #     if sid:
    #         request.session['client_id'] = sid

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'ingresar':
            datos = {'resp': False}

            username = (request.POST.get('username') or '').strip()
            password = request.POST.get('pass') or ''
            next_url = request.POST.get('next_url') or ''

            if not username or not password:
                datos['error'] = 'Debe ingresar usuario y contraseña'
                return JsonResponse(datos)

            # 1) Autenticar
            user_login = authenticate(request, username=username, password=password)
            if user_login is None:
                datos['error'] = 'Credenciales incorrectas'
                return JsonResponse(datos)

            # 2) Validar activo
            if not user_login.is_active:
                datos['error'] = 'Usuario inactivo'
                return JsonResponse(datos)

            persona_ = Persona.objects.filter(usuario=user_login).first()
            if not persona_:
                datos['error'] = 'Usuario sin persona vinculada'
                return JsonResponse(datos)

            # if not persona_.status:
            #     datos['error'] = 'Usuario con persona desactivada'
            #     return JsonResponse(datos)

            persona = persona_

            # 4) Guardar info del cliente (sin romper si no viene)
            request.session['navegador'] = request.POST.get('navegador', '')
            request.session['os'] = request.POST.get('os', '')
            request.session['cookies'] = request.POST.get('cookies', '')
            request.session['screensize'] = request.POST.get('screensize', '')
            request.session['ipreal'] = obtener_ip_cliente_actual(request)

            # 5) Loguear
            if user_login is not None:
                login(request, user_login)

            request.session['persona_id'] = persona_.id

            datos['result'] = True
            datos['url'] = next_url
            return JsonResponse(datos)

    # GET render
    data['next_url'] = request.GET.get('next_url', '')
    data['catalogo'] = request.GET.get('catalogo', '')
    return render(request, "sistemamedico/iniciosesion.html", data)


def logout_user(request):
    if 'persona_id' in request.session:
        del request.session['persona_id']
    if 'empresa_id' in request.session:
        del request.session['empresa_id']
    logout(request)
    return HttpResponseRedirect("/")


@login_required(redirect_field_name='', login_url='/sistemamedico')
# @secure_module
# @last_access
# @transaction.atomic()
def panel(request):
    data = {}
    act_info(request, data)
    persona = data['persona_sesion']
    perfilprincipal = request.session.get('perfilprincipal')
    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        # hoy = datetime.now()
        data['title'] = 'sistemamedico'
        if 'action' in request.GET:

            action = request.GET['action']

            return HttpResponseRedirect(request.path)
        else:

            try:
                if 'paginador' in request.session:
                    del request.session['paginador']
                misgrupos = ModuloGrupo.objects.filter(grupos__in=persona.usuario.groups.all()).distinct()
                modulos = Modulo.objects.filter(Q(modulogrupo__in=misgrupos), activo=True).distinct().order_by('nombre')
                data['mismodulos'] = modulos
                data['CATEGORIAS_MODULOS'] = CategoriaModulo.objects.filter(status=True, id__in=modulos.values_list('categoria',flat=True)).order_by('orden')
                # tiposistema = request.session['tiposistema']
                data['tipoentrada'] = "sistemamedico"
                data['institucion'] = 'Sistema de Facturación'
                if 'info' in request.GET:
                    data['info'] = request.GET['info']

                data['currenttime'] = datetime.now()
                fecha = datetime.today().date() - timedelta(days=15)

                data['eTemplateBaseSetting'] = eTemplateBaseSetting = request.session['eTemplateBaseSetting'] if 'eTemplateBaseSetting' in request.session and request.session['eTemplateBaseSetting'] else None
                modulos_favoritos = None
                ids_modulos_favoritos = []
                data['CATEGORIZACION_MODULOS'] = True
                data['ids_modulos_favoritos'] = ids_modulos_favoritos
                data['modulos_favoritos'] = modulos_favoritos

                data['modulos_sice'] = True

                if not '127.0.0.1' in request.META['HTTP_HOST']:
                    if 'sice' in request.META['HTTP_HOST']:
                        data['modulos_sice'] = True
                    else:
                        data['modulos_sice'] = True
                else:
                    data['modulos_sice'] = True

                return render(request, 'sistemamedico/principal.html', data)
            except Exception as ex:
                text_error = 'Error on line {}, {}'.format(sys.exc_info()[-1].tb_lineno, ex)
                return JsonResponse({'resp': f'{text_error}'})
                # return HttpResponseRedirect('/logout')

def panelweb(request):
    data = {}
    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        # hoy = datetime.now()
        data['title'] = 'sistemamedico'
        if 'action' in request.GET:

            action = request.GET['action']

            return HttpResponseRedirect(request.path)
        else:
            try:
                return render(request, 'sistemamedico/web.html', data)
            except Exception as ex:
                text_error = 'Error on line {}, {}'.format(sys.exc_info()[-1].tb_lineno, ex)
                return JsonResponse({'resp': f'{text_error}'})
                # return HttpResponseRedirect('/logout')
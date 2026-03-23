from django.urls import path, re_path, include
from sistemamedico.settings import *
from saas import vistaprincipal
from saas import view_evaluacionmedica, personas, consultargeneral, profesional, modulos


def _routingpanel(request):
    try:
        if not DEBUG:
            if '127.0.0.1' in request.META['HTTP_HOST']:
                return vistaprincipal.panel(request)
            else:
                if 'sistemamedico' in request.META['HTTP_HOST']:
                    return vistaprincipal.panel(request)
        else:
            if 'sistemamedico' in request.META['HTTP_HOST']:
                return vistaprincipal.panel(request)
            else:
                return vistaprincipal.panel(request)
    except Exception as ex:
        return vistaprincipal.panel(request)

urlpatterns = [
    re_path(r'^$', _routingpanel, name='panel'),
    re_path(r'^sistemamedico$', vistaprincipal.login_user, name='sistemamedico'),
    re_path(r'^logout$', vistaprincipal.logout_user, name='logout'),
    re_path(r'^evaluacionmedica$', view_evaluacionmedica.view, name='evaluacionmedica'),
    re_path(r'^personas$', personas.view, name='personas'),
    re_path(r'^consultargeneral$', consultargeneral.view, name='consultargeneral'),
    re_path(r'^profesionales$', profesional.view, name='profesional'),
    re_path(r'^modulos$', modulos.view, name='modulos'),
]
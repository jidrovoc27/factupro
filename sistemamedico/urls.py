"""
URL configuration for sistemamedico project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path, re_path, include
from sistemamedico import settings
from sistemamedico.settings import *
from django.conf.urls.static import static
from saas import vistaprincipal


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
    # re_path(r'^$', _routingpanel, name='panel'),
    re_path(r'^', include('saas.urls')),
    #    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

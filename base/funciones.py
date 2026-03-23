import ipaddress
from django.core.paginator import Paginator
from django.contrib.auth.models import User

def obtener_ip_cliente_actual(request):
    """
    Obtiene la IP real del cliente considerando proxies.
    Compatible con Nginx, Cloudflare, Gunicorn, etc.
    """

    # Lista de headers comunes usados por proxies
    headers = [
        'HTTP_CF_CONNECTING_IP',     # Cloudflare
        'HTTP_X_REAL_IP',            # Nginx
        'HTTP_X_FORWARDED_FOR',      # Proxies
        'REMOTE_ADDR',
    ]

    for header in headers:
        ip = request.META.get(header)

        if ip:
            # X-Forwarded-For puede traer varias IPs
            ip = ip.split(',')[0].strip()

            # Validar que sea IP válida
            try:
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                continue

    return None


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador, self).__init__(object_list, per_page, orphans=orphans,
                                          allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left < 1:
            left = 1
        if right > self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right + 1)
        self.primera_pagina = True if left > 1 else False
        self.ultima_pagina = True if right < self.num_pages else False
        self.ellipsis_izquierda = left - 1
        self.ellipsis_derecha = right + 1
        
def calculate_username(persona, variant=1):
    alfabeto = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    s = persona.nombres.lower().split(' ')
    while '' in s:
        s.remove('')
    if persona.segundoapellido:
        usernamevariant = s[0][0] + persona.primerapellido.lower() + persona.segundoapellido.lower()[0]
    else:
        usernamevariant = s[0][0] + persona.primerapellido.lower()
    usernamevariant = usernamevariant.replace(' ', '').replace(u'ñ', 'n').replace(u'á', 'a').replace(u'é', 'e').replace(
        u'í', 'i').replace(u'ó', 'o').replace(u'ú', 'u')
    usernamevariantfinal = ''
    for letra in usernamevariant:
        if letra in alfabeto:
            usernamevariantfinal += letra
    if variant > 1:
        usernamevariantfinal += str(variant)
    if not User.objects.filter(username=usernamevariantfinal).exists():
        return usernamevariantfinal
    else:
        return calculate_username(persona, variant + 1)

def _to_bool(val):
    """Convierte cualquier valor truthy/falsy a bool, acepta None."""
    if val is None:
        return None
    return val in (True, 'true', '1', 1)


def _to_int_or_none(val):
    try:
        return int(val) if val not in (None, '', 'null') else None
    except (ValueError, TypeError):
        return None


def _to_decimal_or_none(val):
    try:
        from decimal import Decimal
        return Decimal(str(val)) if val not in (None, '', 'null') else None
    except Exception:
        return None


def _to_date_or_none(val):
    if not val or val in ('null', 'undefined'):
        return None
    return val  # Django acepta strings 'YYYY-MM-DD' directamente
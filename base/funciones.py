import ipaddress


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

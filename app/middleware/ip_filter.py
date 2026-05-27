import ipaddress

from flask import abort, request, current_app


def _is_ip_allowed(ip_address: str, allowed_ranges: list[str]) -> bool:
    try:
        client_ip = ipaddress.ip_address(ip_address)
        for allowed_range in allowed_ranges:
            if client_ip in ipaddress.ip_network(allowed_range, strict=False):
                return True
        return False
    except ValueError:
        return False


def register_ip_filter(app):
    @app.before_request
    def limit_remote_addr():
        if current_app.config.get('DISABLE_IP_FILTER'):
            return
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()

        if request.endpoint in ['health', 'status', 'static']:
            return

        allowed_ranges = current_app.config.get('ALLOWED_IPS', [])
        if not _is_ip_allowed(client_ip, allowed_ranges):
            abort(403)

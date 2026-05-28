import ipaddress
import logging

from flask import abort, request, current_app

logger = logging.getLogger("docify.security")


def _is_ip_allowed(ip_address: str, allowed_ranges: list[str]) -> bool:
    try:
        client_ip = ipaddress.ip_address(ip_address)
        for allowed_range in allowed_ranges:
            if client_ip in ipaddress.ip_network(allowed_range, strict=False):
                return True
        return False
    except ValueError:
        logger.warning(f"Could not parse client IP address: {ip_address}")
        return False


def register_ip_filter(app):
    @app.before_request
    def limit_remote_addr():
        if current_app.config.get('DISABLE_IP_FILTER'):
            return
        
        # Check standard headers safely
        client_ip = request.headers.get('X-Forwarded-For')
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        else:
            client_ip = request.remote_addr

        if not client_ip:
            logger.warning("Rejecting request with unresolved client IP.")
            abort(403)

        if request.endpoint in ['health', 'status', 'static']:
            return

        allowed_ranges = current_app.config.get('ALLOWED_IPS', [])
        if not _is_ip_allowed(client_ip, allowed_ranges):
            logger.warning(f"IP blocked: {client_ip} is not in allowed ranges: {allowed_ranges}")
            abort(403)

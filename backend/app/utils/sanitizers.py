import re
from typing import Optional
import validators
import socket
import ipaddress


BLACKLISTED_NETWORKS = [
    '127.0.0.0/8',      # Localhost
    '10.0.0.0/8',       # Private
    '172.16.0.0/12',    # Private
    '192.168.0.0/16',   # Private
    '169.254.0.0/16',   # Link-local
    '0.0.0.0/8',        # Invalid
    '224.0.0.0/4',      # Multicast
]

DANGEROUS_CHARS = [';', '|', '&', '$', '`', '\n', '\r', '(', ')', '<', '>']


def sanitize_target(target: str) -> str:
    """
    Sanitize and validate target input
    Returns cleaned target or raises ValueError
    """
    # Strip whitespace
    target = target.strip()

    # Check for dangerous characters
    for char in DANGEROUS_CHARS:
        if char in target:
            raise ValueError(f"Invalid character in target: {char}")

    # Remove protocol if present for domain validation
    clean_target = target.replace('https://', '').replace('http://', '').split('/')[0]

    # Try to validate as different types
    is_valid = False

    # Check if it's a valid domain
    if validators.domain(clean_target):
        is_valid = True
        target = clean_target  # Use cleaned version

    # Check if it's a valid IP
    elif validators.ipv4(clean_target) or validators.ipv6(clean_target):
        # Check if IP is blacklisted
        if is_ip_blacklisted(clean_target):
            raise ValueError(f"Target IP is in blacklisted network range")
        is_valid = True
        target = clean_target

    # Check if it's a valid URL
    elif validators.url(target):
        is_valid = True

    if not is_valid:
        raise ValueError("Invalid target format. Must be a domain, IP, or URL")

    return target


def is_ip_blacklisted(ip_str: str) -> bool:
    """Check if IP is in blacklisted network ranges"""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network_str in BLACKLISTED_NETWORKS:
            network = ipaddress.ip_network(network_str)
            if ip in network:
                return True
        return False
    except:
        return False


def resolve_domain_to_ip(domain: str) -> Optional[str]:
    """Resolve domain to IP address"""
    try:
        return socket.gethostbyname(domain)
    except:
        return None

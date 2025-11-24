"""
Utilidades para cálculo de hashes.
Usa SHA256 por defecto.
"""

import hashlib


def calculate_hash(content, algorithm: str = "sha256") -> str:
    """
    Calcula el hash de un contenido.
    
    Args:
        content: Puede ser bytes o string.
        algorithm: "sha256" (default), "md5", "sha1", etc.
    
    Returns:
        Hexadecimal del hash.
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()


def calculate_hash_sha256(content) -> str:
    """
    Atajo: calcula SHA256 directamente.
    """
    return calculate_hash(content, algorithm="sha256")

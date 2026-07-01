import asyncio
import hashlib
import logging

log = logging.getLogger(__name__)


async def hash_password(plain: str) -> str:
    """Genera un hash bcrypt de la contraseña en un threadpool.

    Usa bcrypt cuando esté disponible; de lo contrario, cae al fallback SHA-256
    (solo para desarrollo). Siempre corre en un executor para no bloquear el event loop.
    """
    loop = asyncio.get_running_loop()

    try:
        import bcrypt  # type: ignore

        def _bcrypt_hash() -> str:
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

        return await loop.run_in_executor(None, _bcrypt_hash)
    except ImportError:
        # Fallback con hashlib si bcrypt no está instalado. SOLO para desarrollo.
        import os

        log.warning("bcrypt no disponible; usando SHA-256 (solo desarrollo).")

        def _fallback() -> str:
            salt = os.urandom(16).hex()
            digest = hashlib.sha256(f"{salt}:{plain}".encode()).hexdigest()
            return f"sha256${salt}${digest}"

        return await loop.run_in_executor(None, _fallback)


async def verify_password(plain: str, stored: str) -> bool:
    """Verifica la contraseña comparando con el hash almacenado, en un executor."""
    loop = asyncio.get_running_loop()

    if stored.startswith("sha256$"):
        try:
            _, salt, digest = stored.split("$", 2)
        except ValueError:
            return False

        def _check_sha() -> bool:
            candidate = hashlib.sha256(f"{salt}:{plain}".encode()).hexdigest()
            return candidate == digest

        return await loop.run_in_executor(None, _check_sha)

    try:
        import bcrypt  # type: ignore

        def _check_bcrypt() -> bool:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))

        return await loop.run_in_executor(None, _check_bcrypt)
    except ImportError:
        log.warning("bcrypt no disponible; no se puede verificar hash bcrypt.")
        return False

"""
Logica pura: decide si una publicacion cuenta como etiqueta valida y que
hacer con ella. No habla con Instagram ni con la base de datos, por eso se
puede probar con datos inventados.
"""

import re
from typing import Dict, List, Optional

# Un handle de Instagram: letras, numeros, puntos y guiones bajos, maximo 30.
# El (?<![\w.]) evita contar correos como "hola@clinicasol.com".
_PATRON_HANDLE = re.compile(r"(?<![\w.])@([A-Za-z0-9._]{1,30})")


def extraer_handles(texto: Optional[str]) -> List[str]:
    """Devuelve los @handles que aparecen en el texto, en minusculas y sin '@'."""
    if not texto:
        return []
    handles = []
    for coincidencia in _PATRON_HANDLE.finditer(texto):
        # Un handle no puede terminar en punto: "@clinicasol." es "@clinicasol".
        handle = coincidencia.group(1).rstrip(".").lower()
        if handle:
            handles.append(handle)
    return handles


def es_etiqueta_real(caption: Optional[str], handle_negocio: str) -> bool:
    """
    True solo si el texto trae el @handle EXACTO del negocio.
    Escribir el nombre sin @, o un handle parecido (@clinicasol_mx), no cuenta.
    """
    return handle_negocio.lower().lstrip("@") in extraer_handles(caption)


def decidir(
    publicacion: Dict,
    handle_negocio: str,
    creadores: Dict[str, Dict],
) -> Dict:
    """
    Primer filtro, antes de tocar la tabla de canjes.

    Devuelve {"accion": "activar" | "ignorar", "motivo": ..., ...}.
    Si la accion es "activar", todavia falta confirmar que el creador no
    haya canjeado antes (eso lo hace el almacen de canjes, de forma atomica).
    """
    creador = (publicacion.get("username") or "").lower()

    if not es_etiqueta_real(publicacion.get("caption"), handle_negocio):
        return {"accion": "ignorar", "motivo": "sin_etiqueta_real", "creador": creador}

    if creador not in creadores:
        return {"accion": "ignorar", "motivo": "no_es_creador_registrado", "creador": creador}

    return {
        "accion": "activar",
        "motivo": "etiqueta_valida",
        "creador": creador,
        "beneficio": creadores[creador],
    }

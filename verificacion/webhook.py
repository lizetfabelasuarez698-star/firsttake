"""
Procesa un aviso (webhook) de Meta: "te mencionaron en esta publicacion".

Pasos del algoritmo:
  1. Confirmar que el aviso viene de Meta (firma HMAC con el secreto de la app).
  2. Sacar los media_id de las menciones en publicaciones (no en comentarios).
  3. Pedir a Instagram cada publicacion (texto y autor).
  4. Decidir: ¿etiqueta real? ¿creador registrado?
  5. Registrar el canje solo si es el primero de ese creador.
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from verificacion.menciones import decidir


def firma_valida(cuerpo: bytes, encabezado_firma: Optional[str], secreto_app: str) -> bool:
    """Meta firma cada aviso con 'sha256=<hmac del cuerpo>'."""
    if not encabezado_firma or not secreto_app:
        return False
    esperado = "sha256=" + hmac.new(secreto_app.encode("utf-8"), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, encabezado_firma)


def media_ids_del_aviso(aviso: Dict) -> List[str]:
    ids = []
    for entrada in aviso.get("entry", []):
        for cambio in entrada.get("changes", []):
            valor = cambio.get("value") or {}
            # Si trae comment_id, la mencion fue en un comentario: no cuenta.
            if cambio.get("field") == "mentions" and valor.get("media_id") and not valor.get("comment_id"):
                ids.append(str(valor["media_id"]))
    return ids


def procesar_aviso(
    cuerpo: bytes,
    encabezado_firma: Optional[str],
    secreto_app: str,
    handle_negocio: str,
    creadores: Dict[str, Dict],
    graph,
    almacen,
) -> Tuple[int, Dict]:
    """Devuelve (codigo_http, respuesta). Meta reintenta si no recibe 200."""
    if not firma_valida(cuerpo, encabezado_firma, secreto_app):
        return 401, {"error": "firma_invalida"}

    try:
        aviso = json.loads(cuerpo.decode("utf-8"))
    except ValueError:
        return 400, {"error": "json_invalido"}

    resultados = []
    for media_id in media_ids_del_aviso(aviso):
        publicacion = graph.publicacion_mencionada(media_id)
        if publicacion is None:
            resultados.append({"media_id": media_id, "accion": "ignorar", "motivo": "no_encontrada"})
            continue

        decision = decidir(publicacion, handle_negocio, creadores)
        if decision["accion"] == "activar":
            datos_canje = {
                "media_id": media_id,
                "beneficio": decision["beneficio"],
                "fecha": datetime.now(timezone.utc).isoformat(),
            }
            if not almacen.registrar_si_nuevo(decision["creador"], datos_canje):
                decision = {"accion": "ignorar", "motivo": "ya_canjeado", "creador": decision["creador"]}

        decision["media_id"] = media_id
        resultados.append(decision)

    return 200, {"resultados": resultados}

"""
Cliente minimo de la Graph API de Instagram. Solo corre en el servidor: el
token llega por variable de entorno y viaja en el encabezado, nunca en la URL.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Optional


class ClienteGraph:
    def __init__(self, token: str, id_negocio: str, version: str = "v23.0"):
        if not token or not id_negocio:
            raise ValueError("Faltan INSTAGRAM_ACCESS_TOKEN o INSTAGRAM_BUSINESS_ID")
        self._token = token
        self._id_negocio = id_negocio
        self._base = "https://graph.facebook.com/" + version

    def publicacion_mencionada(self, media_id: str) -> Optional[Dict]:
        """
        Pide a Instagram la publicacion donde mencionaron al negocio.
        Devuelve {"id", "caption", "username", "timestamp"} o None si no existe.
        """
        campos = "mentioned_media.media_id({}){{id,caption,username,timestamp}}".format(media_id)
        url = "{}/{}?{}".format(
            self._base, self._id_negocio, urllib.parse.urlencode({"fields": campos})
        )
        peticion = urllib.request.Request(url, headers={"Authorization": "Bearer " + self._token})
        try:
            with urllib.request.urlopen(peticion, timeout=10) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
        except urllib.error.HTTPError:
            return None
        return datos.get("mentioned_media")

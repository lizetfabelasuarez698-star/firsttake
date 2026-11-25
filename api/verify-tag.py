"""
Funcion de servidor de Vercel: /api/verify-tag

  GET  -> Meta verifica el webhook (hub.challenge) al darlo de alta.
  POST -> Meta avisa de una mencion; se verifica y se activa el beneficio.

El token de Instagram solo se lee aqui, de las variables de entorno.
"""

import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler

# Permite importar el paquete "verificacion" que esta en la raiz del proyecto.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from verificacion.canjes import AlmacenMemoria, AlmacenSupabase, AlmacenUpstash  # noqa: E402
from verificacion.instagram import ClienteGraph  # noqa: E402
from verificacion.webhook import procesar_aviso  # noqa: E402

_RUTA_CREADORES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos", "creadores.json")
_almacen_local = AlmacenMemoria()


def _almacen():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        return AlmacenSupabase(supabase_url, supabase_key)
    url, token = os.environ.get("UPSTASH_REDIS_REST_URL"), os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    return AlmacenUpstash(url, token) if url and token else _almacen_local


def _creadores():
    with open(_RUTA_CREADORES, encoding="utf-8") as archivo:
        return {handle.lower(): beneficio for handle, beneficio in json.load(archivo).items()}


class handler(BaseHTTPRequestHandler):
    def _responder(self, codigo, cuerpo):
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else json.dumps(cuerpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "text/plain" if isinstance(cuerpo, str) else "application/json")
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        parametros = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        modo = parametros.get("hub.mode", [""])[0]
        token = parametros.get("hub.verify_token", [""])[0]
        reto = parametros.get("hub.challenge", [""])[0]
        if modo == "subscribe" and token and token == os.environ.get("META_VERIFY_TOKEN"):
            return self._responder(200, reto)
        return self._responder(403, {"error": "verificacion_rechazada"})

    def do_POST(self):
        largo = int(self.headers.get("Content-Length") or 0)
        cuerpo = self.rfile.read(largo)
        graph = ClienteGraph(
            os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
            os.environ.get("INSTAGRAM_BUSINESS_ID", ""),
            os.environ.get("GRAPH_API_VERSION", "v23.0"),
        )
        codigo, respuesta = procesar_aviso(
            cuerpo,
            self.headers.get("X-Hub-Signature-256"),
            os.environ.get("META_APP_SECRET", ""),
            os.environ.get("INSTAGRAM_HANDLE", ""),
            _creadores(),
            graph,
            _almacen(),
        )
        return self._responder(codigo, respuesta)

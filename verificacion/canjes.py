"""
Tabla de canjes ("redemptions"): recuerda que creador ya recibio su beneficio.

La operacion clave es registrar_si_nuevo(): revisa y guarda en UN solo paso.
Si se hiciera en dos ("¿ya canjeo?" y luego "guardar"), dos avisos que
llegan al mismo tiempo podrian pasar ambos la revision y dar dos premios.
"""

import json
import threading
import urllib.parse
import urllib.request
from typing import Dict


class AlmacenMemoria:
    """Para pruebas y para correr en local. Se borra al reiniciar."""

    def __init__(self):
        self._canjes: Dict[str, Dict] = {}
        self._candado = threading.Lock()

    def registrar_si_nuevo(self, creador: str, datos: Dict) -> bool:
        """True si es su primer canje (y lo guarda); False si ya habia canjeado."""
        with self._candado:
            if creador in self._canjes:
                return False
            self._canjes[creador] = datos
            return True

    def canje_de(self, creador: str):
        return self._canjes.get(creador)


class AlmacenUpstash:
    """
    Para Vercel, donde la memoria no sobrevive entre llamadas. Usa Redis de
    Upstash por su API REST: "SET ... NX" solo escribe si la clave no existia,
    asi que revisar y guardar ocurre en un paso.
    """

    def __init__(self, url: str, token: str):
        self._url = url.rstrip("/")
        self._token = token

    def registrar_si_nuevo(self, creador: str, datos: Dict) -> bool:
        comando = ["SET", "canje:" + creador, json.dumps(datos), "NX"]
        peticion = urllib.request.Request(
            self._url,
            data=json.dumps(comando).encode("utf-8"),
            headers={"Authorization": "Bearer " + self._token, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            resultado = json.loads(respuesta.read().decode("utf-8")).get("result")
        return resultado == "OK"


class AlmacenSupabase:
    """
    Para produccion con Supabase: la tabla "redemptions" guarda que creador
    ya canjeo que beneficio. Usa insert con Prefer: resolution=ignore-duplicates
    (equivale a ON CONFLICT DO NOTHING), asi que revisar y guardar ocurre en
    un solo paso, igual que AlmacenUpstash con SET ... NX.

    Usa la SUPABASE_SERVICE_ROLE_KEY porque esto corre solo del lado del
    servidor (dentro de api/verify-tag.py); esa clave nunca debe llegar al
    frontend ni a index.html.
    """

    def __init__(self, url: str, service_role_key: str):
        self._url = url.rstrip("/")
        self._key = service_role_key

    def registrar_si_nuevo(self, creador: str, datos: Dict) -> bool:
        peticion = urllib.request.Request(
            self._url + "/rest/v1/redemptions",
            data=json.dumps({"creador": creador, "datos": datos}).encode("utf-8"),
            headers={
                "apikey": self._key,
                "Authorization": "Bearer " + self._key,
                "Content-Type": "application/json",
                "Prefer": "resolution=ignore-duplicates,return=representation",
            },
            method="POST",
        )
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            resultado = json.loads(respuesta.read().decode("utf-8"))
        return len(resultado) > 0

    def canje_de(self, creador: str):
        qs = urllib.parse.urlencode({"creador": "eq." + creador, "select": "datos"})
        peticion = urllib.request.Request(
            self._url + "/rest/v1/redemptions?" + qs,
            headers={"apikey": self._key, "Authorization": "Bearer " + self._key},
        )
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            filas = json.loads(respuesta.read().decode("utf-8"))
        return filas[0]["datos"] if filas else None

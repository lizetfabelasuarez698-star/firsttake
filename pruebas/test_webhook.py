"""
Los 3 criterios de aceptacion, de punta a punta, sin tocar Instagram real:
la Graph API se reemplaza por un "Instagram falso" con publicaciones inventadas.
"""

import hashlib
import hmac
import json
import unittest

from verificacion.canjes import AlmacenMemoria
from verificacion.webhook import procesar_aviso

SECRETO = "secreto-de-prueba"
NEGOCIO = "clinicasol"
CREADORES = {"ana.creadora": {"tipo": "descuento", "valor": "15%"}}


class InstagramFalso:
    def __init__(self, publicaciones):
        self._publicaciones = publicaciones

    def publicacion_mencionada(self, media_id):
        return self._publicaciones.get(media_id)


def aviso_de_mencion(media_id, comment_id=None):
    valor = {"media_id": media_id}
    if comment_id:
        valor["comment_id"] = comment_id
    return json.dumps({"object": "instagram", "entry": [{"changes": [{"field": "mentions", "value": valor}]}]}).encode()


def firmar(cuerpo):
    return "sha256=" + hmac.new(SECRETO.encode(), cuerpo, hashlib.sha256).hexdigest()


class CriteriosDeAceptacion(unittest.TestCase):
    def setUp(self):
        self.almacen = AlmacenMemoria()
        self.instagram = InstagramFalso(
            {
                "post-1": {"id": "post-1", "username": "ana.creadora", "caption": "Amo a @clinicasol"},
                "post-2": {"id": "post-2", "username": "ana.creadora", "caption": "Otra vez @clinicasol"},
                "post-3": {"id": "post-3", "username": "ana.creadora", "caption": "Fui a Clinica Sol"},
            }
        )

    def enviar(self, cuerpo, firma=None):
        return procesar_aviso(
            cuerpo, firma or firmar(cuerpo), SECRETO, NEGOCIO, CREADORES, self.instagram, self.almacen
        )

    def test_caso_1_etiqueta_correcta_activa_beneficio(self):
        codigo, respuesta = self.enviar(aviso_de_mencion("post-1"))
        self.assertEqual(codigo, 200)
        self.assertEqual(respuesta["resultados"][0]["accion"], "activar")
        self.assertEqual(self.almacen.canje_de("ana.creadora")["media_id"], "post-1")

    def test_caso_2_ya_canjeo_no_activa_otro(self):
        self.enviar(aviso_de_mencion("post-1"))
        codigo, respuesta = self.enviar(aviso_de_mencion("post-2"))
        self.assertEqual(codigo, 200)
        self.assertEqual(respuesta["resultados"][0]["motivo"], "ya_canjeado")
        # El canje guardado sigue siendo el primero.
        self.assertEqual(self.almacen.canje_de("ana.creadora")["media_id"], "post-1")

    def test_caso_3_mencion_sin_handle_real_no_cuenta(self):
        codigo, respuesta = self.enviar(aviso_de_mencion("post-3"))
        self.assertEqual(codigo, 200)
        self.assertEqual(respuesta["resultados"][0]["motivo"], "sin_etiqueta_real")
        self.assertIsNone(self.almacen.canje_de("ana.creadora"))

    def test_firma_falsa_se_rechaza(self):
        codigo, _ = self.enviar(aviso_de_mencion("post-1"), firma="sha256=falsa")
        self.assertEqual(codigo, 401)
        self.assertIsNone(self.almacen.canje_de("ana.creadora"))

    def test_mencion_en_comentario_no_cuenta(self):
        _, respuesta = self.enviar(aviso_de_mencion("post-1", comment_id="c-1"))
        self.assertEqual(respuesta["resultados"], [])


if __name__ == "__main__":
    unittest.main()

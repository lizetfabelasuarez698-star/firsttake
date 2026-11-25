"""
AlmacenSupabase, con urlopen mockeado: nunca le pega a un Supabase real.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from verificacion.canjes import AlmacenSupabase


def _respuesta(cuerpo):
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.read.return_value = json.dumps(cuerpo).encode("utf-8")
    return mock


class AlmacenSupabaseTest(unittest.TestCase):
    def setUp(self):
        self.almacen = AlmacenSupabase("https://xyz.supabase.co", "clave-de-prueba")

    @patch("verificacion.canjes.urllib.request.urlopen")
    def test_primer_canje_devuelve_true(self, urlopen):
        urlopen.return_value = _respuesta([{"creador": "ana.creadora"}])
        self.assertTrue(self.almacen.registrar_si_nuevo("ana.creadora", {"media_id": "post-1"}))
        peticion = urlopen.call_args[0][0]
        self.assertIn("ignore-duplicates", peticion.headers["Prefer"])
        self.assertEqual(peticion.headers["Apikey"], "clave-de-prueba")

    @patch("verificacion.canjes.urllib.request.urlopen")
    def test_segundo_canje_devuelve_false(self, urlopen):
        # PostgREST responde [] cuando el ON CONFLICT ignora la fila.
        urlopen.return_value = _respuesta([])
        self.assertFalse(self.almacen.registrar_si_nuevo("ana.creadora", {"media_id": "post-2"}))

    @patch("verificacion.canjes.urllib.request.urlopen")
    def test_canje_de_existente(self, urlopen):
        urlopen.return_value = _respuesta([{"datos": {"media_id": "post-1"}}])
        self.assertEqual(self.almacen.canje_de("ana.creadora"), {"media_id": "post-1"})

    @patch("verificacion.canjes.urllib.request.urlopen")
    def test_canje_de_inexistente(self, urlopen):
        urlopen.return_value = _respuesta([])
        self.assertIsNone(self.almacen.canje_de("nadie"))


if __name__ == "__main__":
    unittest.main()

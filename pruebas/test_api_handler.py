"""Pruebas de la funcion de Vercel (api/verify-tag.py) sin internet."""
import hashlib
import hmac
import importlib.util
import io
import os
import unittest
from unittest import mock

_RUTA = os.path.join(os.path.dirname(__file__), "..", "api", "verify-tag.py")
_spec = importlib.util.spec_from_file_location("verify_tag", _RUTA)
verify_tag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_tag)


def _post(cuerpo, firma=None):
    """Simula un POST al handler y devuelve (codigo, cuerpo de respuesta)."""
    h = verify_tag.handler.__new__(verify_tag.handler)
    h.headers = {"Content-Length": str(len(cuerpo))}
    if firma:
        h.headers["X-Hub-Signature-256"] = firma
    h.rfile, h.wfile = io.BytesIO(cuerpo), io.BytesIO()
    enviados = {}
    h.send_response = lambda c: enviados.setdefault("codigo", c)
    h.send_header = lambda *a: None
    h.end_headers = lambda: None
    h.do_POST()
    return enviados["codigo"], h.wfile.getvalue().decode()


class HandlerTest(unittest.TestCase):
    def test_sin_firma_da_401_aunque_falten_variables(self):
        # Antes: tronaba con 500 porque creaba el cliente de Instagram primero.
        with mock.patch.dict(os.environ, {}, clear=True):
            codigo, _ = _post(b'{"entry":[]}')
        self.assertEqual(codigo, 401)

    def test_firma_valida_sin_instagram_configurado_da_503(self):
        cuerpo = b'{"entry":[]}'
        firma = "sha256=" + hmac.new(b"s3", cuerpo, hashlib.sha256).hexdigest()
        with mock.patch.dict(os.environ, {"META_APP_SECRET": "s3"}, clear=True):
            codigo, respuesta = _post(cuerpo, firma)
        self.assertEqual(codigo, 503)
        self.assertIn("falta_configurar_instagram", respuesta)


if __name__ == "__main__":
    unittest.main()

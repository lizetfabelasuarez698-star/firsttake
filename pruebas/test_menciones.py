import unittest

from verificacion.menciones import decidir, es_etiqueta_real, extraer_handles

NEGOCIO = "clinicasol"
CREADORES = {"ana.creadora": {"tipo": "descuento", "valor": "15%"}}


class ExtraerHandles(unittest.TestCase):
    def test_encuentra_handles_en_minusculas(self):
        self.assertEqual(extraer_handles("Gracias @ClinicaSol y @ana.creadora!"), ["clinicasol", "ana.creadora"])

    def test_quita_el_punto_final(self):
        self.assertEqual(extraer_handles("Fui a @clinicasol."), ["clinicasol"])

    def test_ignora_correos(self):
        self.assertEqual(extraer_handles("Escribe a hola@clinicasol.com"), [])

    def test_texto_vacio(self):
        self.assertEqual(extraer_handles(None), [])


class EtiquetaReal(unittest.TestCase):
    def test_handle_exacto_cuenta(self):
        self.assertTrue(es_etiqueta_real("Me encanto @clinicasol", NEGOCIO))

    def test_nombre_sin_arroba_no_cuenta(self):
        self.assertFalse(es_etiqueta_real("Me encanto Clinica Sol, clinicasol", NEGOCIO))

    def test_handle_parecido_no_cuenta(self):
        self.assertFalse(es_etiqueta_real("Me encanto @clinicasol_mx", NEGOCIO))


class Decidir(unittest.TestCase):
    def test_etiqueta_valida_de_creador_registrado(self):
        decision = decidir({"username": "ana.creadora", "caption": "@clinicasol"}, NEGOCIO, CREADORES)
        self.assertEqual(decision["accion"], "activar")
        self.assertEqual(decision["beneficio"]["valor"], "15%")

    def test_creador_no_registrado(self):
        decision = decidir({"username": "desconocido", "caption": "@clinicasol"}, NEGOCIO, CREADORES)
        self.assertEqual(decision["motivo"], "no_es_creador_registrado")

    def test_sin_etiqueta_real(self):
        decision = decidir({"username": "ana.creadora", "caption": "Clinica Sol"}, NEGOCIO, CREADORES)
        self.assertEqual(decision["motivo"], "sin_etiqueta_real")


if __name__ == "__main__":
    unittest.main()

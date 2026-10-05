import json
import unittest
from unittest.mock import patch

from diagnostico import crear_script_consola, registrar_en_navegador


class TestConsolaNavegador(unittest.TestCase):
    def test_sin_diagnostico_no_se_inserta_script(self):
        with patch("diagnostico.components.html") as html:
            registrar_en_navegador([{"nombre": "foto.png"}])
        html.assert_not_called()

    def test_nombre_no_puede_cerrar_script(self):
        nombre = '</script><script>alert("prueba")</script>'
        script = crear_script_consola([{"nombre": nombre, "diagnostico": {}}])
        self.assertEqual(script.count("</script>"), 1)
        payload = script.split("for (const reporte of ", 1)[1].split(") {", 1)[0]
        self.assertEqual(json.loads(payload)[0]["nombre"], nombre)

    def test_diagnostico_se_envia_a_componente_del_navegador(self):
        resultado = {"nombre": "foto.png", "diagnostico": {"tipo_detectado": "PNG"}}
        with patch("diagnostico.components.html") as html:
            registrar_en_navegador([resultado])
        html.assert_called_once()
        script = html.call_args.args[0]
        self.assertIn('"tipo_detectado": "PNG"', script)
        self.assertIn("console.table(d.coincidencias)", script)

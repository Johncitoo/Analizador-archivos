"""Pruebas de la interfaz sin conectarse al backend."""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app.py"


class TestLimiteSubida(unittest.TestCase):
    def analizar(self, tamano, diagnostico=None):
        archivo = SimpleNamespace(name="prueba.txt", size=tamano, getvalue=lambda: b"hola")
        resultado = {
            "nombre": "prueba.txt", "extension": "txt", "tipo_detectado": "Texto",
            "mime": "text/plain", "tamano": tamano,
        }
        if diagnostico is not None:
            resultado["diagnostico"] = diagnostico
        with (
            patch("streamlit.file_uploader", return_value=[archivo]),
            patch("api.subir_archivo", return_value=resultado) as subir,
            patch("api.obtener_estadisticas", return_value={"total_archivos": 0}),
            patch("api.listar_archivos", return_value=[]),
        ):
            app = AppTest.from_file(str(APP)).run()
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            return app, subir

    def test_archivo_mayor_a_20_mb_no_se_envia(self):
        app, subir = self.analizar(20 * 1024 * 1024 + 1)
        subir.assert_not_called()
        self.assertIn("supera el máximo de 20 MB", app.error[0].value)

    def test_archivo_de_20_mb_se_envia(self):
        app, subir = self.analizar(20 * 1024 * 1024)
        subir.assert_called_once_with("prueba.txt", b"hola")
        self.assertEqual(len(app.success), 1)

    def test_analisis_con_diagnostico_genera_log_para_navegador(self):
        diagnostico = {"tipo_detectado": "Texto", "coincidencias": []}
        with patch("diagnostico.components.html") as html:
            self.analizar(4, diagnostico)
        html.assert_called_once()
        self.assertIn('"tipo_detectado": "Texto"', html.call_args.args[0])

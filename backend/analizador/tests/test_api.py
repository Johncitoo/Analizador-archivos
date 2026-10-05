import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from analizador import serializers
from analizador.models import ArchivoAnalizado

URL_ARCHIVOS = "/api/archivos/"
URL_ESTADISTICAS = "/api/archivos/estadisticas/"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
PDF = b"%PDF-1.7\n" + b"contenido"


@pytest.fixture
def cliente():
    return APIClient()


def subir(cliente, nombre, contenido):
    archivo = SimpleUploadedFile(nombre, contenido)
    return cliente.post(URL_ARCHIVOS, {"archivo": archivo}, format="multipart")


@pytest.mark.django_db
class TestSubida:
    def test_subir_archivo_detecta_y_guarda(self, cliente):
        respuesta = subir(cliente, "foto.png", PNG)

        assert respuesta.status_code == 201
        assert respuesta.data["nombre"] == "foto.png"
        assert respuesta.data["extension"] == "png"
        assert respuesta.data["tipo_detectado"] == "PNG"
        assert respuesta.data["mime"] == "image/png"
        assert respuesta.data["tamano"] == len(PNG)
        assert ArchivoAnalizado.objects.count() == 1

    def test_detecta_por_contenido_aunque_la_extension_mienta(self, cliente):
        respuesta = subir(cliente, "factura.jpg", PDF)

        assert respuesta.status_code == 201
        assert respuesta.data["extension"] == "jpg"
        assert respuesta.data["tipo_detectado"] == "PDF"

    def test_sin_archivo_responde_400(self, cliente):
        respuesta = cliente.post(URL_ARCHIVOS, {}, format="multipart")

        assert respuesta.status_code == 400
        assert "archivo" in respuesta.data
        assert ArchivoAnalizado.objects.count() == 0

    def test_archivo_muy_grande_responde_400(self, cliente, monkeypatch):
        monkeypatch.setattr(serializers, "TAMANO_MAXIMO", 10)

        respuesta = subir(cliente, "grande.pdf", PDF)

        assert respuesta.status_code == 400
        assert ArchivoAnalizado.objects.count() == 0


    def test_extension_demasiado_larga_responde_400(self, cliente):
        respuesta = subir(cliente, "archivo." + "x" * 21, PDF)

        assert respuesta.status_code == 400
        assert "archivo" in respuesta.data
        assert "20 caracteres" in str(respuesta.data["archivo"])
        assert ArchivoAnalizado.objects.count() == 0

    def test_extension_en_limite_se_guarda(self, cliente):
        respuesta = subir(cliente, "archivo." + "x" * 20, PDF)

        assert respuesta.status_code == 201
        assert respuesta.data["extension"] == "x" * 20
        assert ArchivoAnalizado.objects.count() == 1

    def test_diagnostico_png_solo_en_subida_solicitada(self, cliente, settings):
        settings.DEBUG = True
        settings.DJANGO_DIAGNOSTICO_ENABLED = True
        archivo = SimpleUploadedFile("foto.jpg", PNG)
        respuesta = cliente.post(URL_ARCHIVOS + "?diagnostico=1", {"archivo": archivo}, format="multipart")
        assert respuesta.status_code == 201
        diagnostico = respuesta.data["diagnostico"]
        assert diagnostico["tipo_detectado"] == "PNG"
        assert diagnostico["muestra_bytes"] == 16
        patron = diagnostico["coincidencias"][0]
        assert patron["offset"] == 0
        assert patron["esperado_hex"] == patron["encontrado_hex"] == "89 50 4e 47 0d 0a 1a 0a"
        assert patron["esperado_bits"] == patron["encontrado_bits"]
        detalle = cliente.get(f"{URL_ARCHIVOS}{respuesta.data['id']}/")
        assert "diagnostico" not in detalle.data

    @pytest.mark.parametrize("debug", [False, True])
    def test_diagnostico_desactivado_se_omite(self, cliente, settings, debug):
        settings.DEBUG = debug
        settings.DJANGO_DIAGNOSTICO_ENABLED = False
        archivo = SimpleUploadedFile("foto.png", PNG)
        respuesta = cliente.post(URL_ARCHIVOS + "?diagnostico=1", {"archivo": archivo}, format="multipart")
        assert respuesta.status_code == 201
        assert "diagnostico" not in respuesta.data

    @pytest.mark.parametrize("debug", [False, True])
    def test_diagnostico_no_solicitado_se_omite(self, cliente, settings, debug):
        settings.DEBUG = debug
        settings.DJANGO_DIAGNOSTICO_ENABLED = True
        respuesta = subir(cliente, "foto.png", PNG)
        assert respuesta.status_code == 201
        assert "diagnostico" not in respuesta.data

    def test_diagnostico_habilitado_en_produccion(self, cliente, settings):
        settings.DEBUG = False
        settings.DJANGO_DIAGNOSTICO_ENABLED = True
        archivo = SimpleUploadedFile("foto.jpg", PNG)
        respuesta = cliente.post(URL_ARCHIVOS + "?diagnostico=1", {"archivo": archivo}, format="multipart")
        assert respuesta.status_code == 201
        diagnostico = respuesta.data["diagnostico"]
        assert diagnostico["tipo_detectado"] == "PNG"
        assert diagnostico["muestra_bytes"] == 16
        patron = diagnostico["coincidencias"][0]
        assert patron["esperado_bits"] == patron["encontrado_bits"]
        assert "diagnostico" not in cliente.get(f"{URL_ARCHIVOS}{respuesta.data['id']}/").data
        assert all("diagnostico" not in registro for registro in cliente.get(URL_ARCHIVOS).data)

    @pytest.mark.parametrize(
        ("datos", "tipo", "offsets"),
        [
            (b"RIFF\x00\x00\x00\x00WAVEfmt ", "WAV", [0, 8]),
            (b"\x00" * 257 + b"ustar", "TAR", [257]),
            (b"hola", "Texto", []),
            (b"hola\xff", "Desconocido", []),
        ],
    )
    def test_diagnostico_respeta_firmas_y_posiciones(self, cliente, settings, datos, tipo, offsets):
        settings.DEBUG = True
        settings.DJANGO_DIAGNOSTICO_ENABLED = True
        archivo = SimpleUploadedFile("prueba.bin", datos)
        respuesta = cliente.post(URL_ARCHIVOS + "?diagnostico=1", {"archivo": archivo}, format="multipart")
        assert respuesta.status_code == 201
        diagnostico = respuesta.data["diagnostico"]
        assert diagnostico["tipo_detectado"] == tipo
        assert diagnostico["muestra_bytes"] <= 16
        assert [p["offset"] for p in diagnostico["coincidencias"]] == offsets
        for patron in diagnostico["coincidencias"]:
            assert patron["esperado_bits"] == patron["encontrado_bits"]
            assert patron["esperado_hex"] == patron["encontrado_hex"]


@pytest.mark.django_db
class TestConsulta:
    def test_listar_ordena_del_mas_nuevo_al_mas_viejo(self, cliente):
        subir(cliente, "a.png", PNG)
        subir(cliente, "b.pdf", PDF)

        respuesta = cliente.get(URL_ARCHIVOS)

        assert respuesta.status_code == 200
        assert [a["nombre"] for a in respuesta.data] == ["b.pdf", "a.png"]

    def test_detalle(self, cliente):
        creado = subir(cliente, "a.png", PNG).data

        respuesta = cliente.get(f"{URL_ARCHIVOS}{creado['id']}/")

        assert respuesta.status_code == 200
        assert respuesta.data == creado

    def test_detalle_inexistente_responde_404(self, cliente):
        assert cliente.get(f"{URL_ARCHIVOS}9999/").status_code == 404


@pytest.mark.django_db
class TestEstadisticas:
    def test_sin_archivos(self, cliente):
        respuesta = cliente.get(URL_ESTADISTICAS)

        assert respuesta.status_code == 200
        assert respuesta.data == {"total_archivos": 0, "tamano_total": 0, "por_tipo": []}

    def test_cuenta_por_tipo(self, cliente):
        subir(cliente, "a.png", PNG)
        subir(cliente, "b.png", PNG)
        subir(cliente, "c.pdf", PDF)

        respuesta = cliente.get(URL_ESTADISTICAS)

        assert respuesta.data["total_archivos"] == 3
        assert respuesta.data["tamano_total"] == 2 * len(PNG) + len(PDF)
        assert respuesta.data["por_tipo"] == [
            {"tipo_detectado": "PNG", "cantidad": 2, "tamano_total": 2 * len(PNG)},
            {"tipo_detectado": "PDF", "cantidad": 1, "tamano_total": len(PDF)},
        ]


@pytest.mark.django_db
def test_str_del_modelo_es_el_nombre():
    archivo = ArchivoAnalizado(nombre="foto.png", tipo_detectado="PNG", tamano=1)
    assert str(archivo) == "foto.png"


@pytest.mark.django_db
def test_swagger_disponible(cliente):
    assert cliente.get("/api/docs/").status_code == 200
    assert cliente.get("/api/schema/").status_code == 200


@pytest.mark.django_db
class TestCors:
    def test_permite_origen_del_frontend(self, cliente, settings):
        settings.CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
        respuesta = cliente.get(URL_ARCHIVOS, HTTP_ORIGIN="http://localhost:5173")

        assert respuesta["Access-Control-Allow-Origin"] == "http://localhost:5173"

    def test_rechaza_origen_desconocido(self, cliente, settings):
        settings.CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
        respuesta = cliente.get(URL_ARCHIVOS, HTTP_ORIGIN="http://sitio-malicioso.com")

        assert "Access-Control-Allow-Origin" not in respuesta

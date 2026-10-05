import io
import logging
import zipfile

import pytest

from analizador.detector import (
    BYTES_CABECERA,
    MIME_DESCONOCIDO,
    TIPO_DESCONOCIDO,
    detectar_tipo,
    obtener_extension,
)


def crear_zip(*nombres: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for nombre in nombres:
            zf.writestr(nombre, "contenido")
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("datos", "tipo", "mime"),
    [
        (b"%PDF-1.7\n...", "PDF", "application/pdf"),
        (b"\x89PNG\r\n\x1a\n" + b"\x00" * 20, "PNG", "image/png"),
        (b"\xff\xd8\xff\xe0" + b"\x00" * 20, "JPEG", "image/jpeg"),
        (b"GIF89a" + b"\x00" * 10, "GIF", "image/gif"),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", "WEBP", "image/webp"),
        (b"RIFF\x00\x00\x00\x00WAVEfmt ", "WAV", "audio/wav"),
        (b"\x00\x00\x00\x18ftypmp42", "MP4", "video/mp4"),
        (b"ID3\x03\x00" + b"\x00" * 10, "MP3", "audio/mpeg"),
        (b"\x1f\x8b\x08\x00", "GZIP", "application/gzip"),
        (b"MZ\x90\x00" + b"\x00" * 10, "EXE", "application/vnd.microsoft.portable-executable"),
        (b"\x00" * 257 + b"ustar\x0000", "TAR", "application/x-tar"),
        (b"SQLite format 3\x00" + b"\x00" * 10, "SQLite", "application/vnd.sqlite3"),
    ],
)
def test_detecta_por_firma(datos, tipo, mime):
    resultado = detectar_tipo(datos)
    assert resultado.tipo == tipo
    assert resultado.mime == mime


def test_ignora_la_extension_y_mira_el_contenido():
    contenido_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    assert detectar_tipo(contenido_png).tipo == "PNG"


def test_riff_desconocido_no_se_confunde_con_webp_ni_wav():
    assert detectar_tipo(b"RIFF\x00\x00\x00\x00XXXX\xff\xfe\x00").tipo == TIPO_DESCONOCIDO


def test_archivo_vacio():
    assert detectar_tipo(b"").tipo == "Vacío"


@pytest.mark.parametrize(
    ("carpeta", "tipo"),
    [("word/document.xml", "DOCX"), ("xl/workbook.xml", "XLSX"), ("ppt/presentation.xml", "PPTX")],
)
def test_distingue_documentos_office(carpeta, tipo):
    assert detectar_tipo(crear_zip("[Content_Types].xml", carpeta)).tipo == tipo


def test_zip_comun():
    resultado = detectar_tipo(crear_zip("foto.png", "notas.txt"))
    assert resultado.tipo == "ZIP"
    assert resultado.mime == "application/zip"


def test_zip_corrupto_se_reporta_como_zip():
    assert detectar_tipo(b"PK\x03\x04basura-que-no-es-un-zip").tipo == "ZIP"


def test_texto_utf8():
    resultado = detectar_tipo("Hola, ¿cómo estás? ñandú".encode("utf-8"))
    assert resultado.tipo == "Texto"
    assert resultado.mime == "text/plain"


def test_texto_con_caracter_cortado_al_final_de_la_muestra():
    # 8191 letras + "ñ" (2 bytes): la muestra de 8192 bytes corta la ñ por la mitad
    datos = b"a" * 8191 + "ñ".encode("utf-8")
    assert detectar_tipo(datos).tipo == "Texto"


@pytest.mark.parametrize(
    "datos",
    [
        b"\xff", b"hola\xff", b"hola\xc3",
        b"a" * 8191 + b"\xff" + b"a",
        b"a" * 8191 + b"\xc3(",
        b"a" * 8191 + b"\xe2\x82",
        b"a" * 8191 + b"\xf0\x9f\x98",
    ],
)
def test_utf8_invalido_o_incompleto_no_es_texto(datos):
    assert detectar_tipo(datos).tipo == TIPO_DESCONOCIDO


@pytest.mark.parametrize("caracter", ["ñ", "€", "😀"])
def test_completa_caracter_utf8_en_limite_de_muestra(caracter):
    datos = b"a" * 8191 + caracter.encode("utf-8")
    assert detectar_tipo(datos).tipo == "Texto"


def test_binario_desconocido():
    resultado = detectar_tipo(b"\x00\x01\x02\x03\xfe\xff")
    assert resultado.tipo == TIPO_DESCONOCIDO
    assert resultado.mime == MIME_DESCONOCIDO


def test_bytes_invalidos_sin_nulos_no_son_texto():
    assert detectar_tipo(b"\xc3\x28\xa0\xa1 hola").tipo == TIPO_DESCONOCIDO


def test_bytes_cabecera_alcanza_para_todas_las_firmas():
    assert BYTES_CABECERA == 262


@pytest.mark.parametrize(
    ("nombre", "extension"),
    [("foto.JPG", "jpg"), ("informe.final.pdf", "pdf"), ("README", ""), (".bashrc", "")],
)
def test_obtener_extension(nombre, extension):
    assert obtener_extension(nombre) == extension


def test_log_pdf_muestra_bits_compartidos_sin_volcar_archivo(caplog):
    with caplog.at_level(logging.DEBUG, logger="analizador.detector"):
        detectar_tipo(b"%PDF-1.7\n" + b"x" * 100 + b"CONTENIDO_PRIVADO")
    mensaje = caplog.text
    assert "muestra_bytes=16" in mensaje
    assert "tipo=PDF offset=0 longitud=4" in mensaje
    assert "esperado_hex=[25 50 44 46] encontrado_hex=[25 50 44 46]" in mensaje
    bits = "00100101 01010000 01000100 01000110"
    assert f"esperado_bits=[{bits}] encontrado_bits=[{bits}]" in mensaje
    assert "CONTENIDO_PRIVADO" not in mensaje


@pytest.mark.parametrize(
    ("datos", "tipo", "offsets"),
    [
        (b"RIFF\x00\x00\x00\x00WAVEfmt ", "WAV", [0, 8]),
        (b"\x00" * 257 + b"ustar", "TAR", [257]),
    ],
)
def test_log_firmas_en_distintas_posiciones(caplog, datos, tipo, offsets):
    with caplog.at_level(logging.DEBUG, logger="analizador.detector"):
        detectar_tipo(datos)
    coincidencias = [r.getMessage() for r in caplog.records if "Firma coincidente:" in r.getMessage()]
    assert len(coincidencias) == len(offsets)
    for mensaje, offset in zip(coincidencias, offsets):
        assert f"tipo={tipo} offset={offset} " in mensaje


@pytest.mark.parametrize(("datos", "tipo"), [(b"hola", "Texto"), (b"\x00\xff", "Desconocido")])
def test_log_sin_firma_no_inventa_coincidencias(caplog, datos, tipo):
    with caplog.at_level(logging.DEBUG, logger="analizador.detector"):
        detectar_tipo(datos)
    assert f"Sin firma coincidente: tipo={tipo}" in caplog.text
    assert "Firma coincidente:" not in caplog.text


def test_log_info_no_expone_bytes(caplog):
    with caplog.at_level(logging.INFO, logger="analizador.detector"):
        detectar_tipo(b"%PDF-1.7\n")
    assert "Resultado de deteccion: tipo=PDF" in caplog.text
    assert "bits=" not in caplog.text
    assert "hex=" not in caplog.text


def test_log_zip_distingue_firma_de_tipo_office(caplog):
    with caplog.at_level(logging.DEBUG, logger="analizador.detector"):
        detectar_tipo(crear_zip("word/document.xml"))
    assert "Firma coincidente: tipo=ZIP" in caplog.text
    assert "Resultado de deteccion: tipo=DOCX" in caplog.text

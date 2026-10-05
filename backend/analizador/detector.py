# vamos a intentar leer lso magic bytes
import codecs
import io
import logging
import zipfile
from dataclasses import dataclass
from pathlib import PurePath

TIPO_DESCONOCIDO = "Desconocido"
MIME_DESCONOCIDO = "application/octet-stream"
logger = logging.getLogger(__name__)
BYTES_MUESTRA_LOG = 16


def _bits(datos: bytes) -> str:
    return " ".join(f"{byte:08b}" for byte in datos)


def _registrar_coincidencia(firma: "Firma", datos: bytes) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return
    for offset, esperado in firma.patrones:
        encontrado = datos[offset:offset + len(esperado)]
        logger.debug(
            "Firma coincidente: tipo=%s offset=%d longitud=%d "
            "esperado_hex=[%s] encontrado_hex=[%s] "
            "esperado_bits=[%s] encontrado_bits=[%s]",
            firma.tipo, offset, len(esperado), esperado.hex(" "),
            encontrado.hex(" "), _bits(esperado), _bits(encontrado),
        )


@dataclass(frozen=True)
class Firma:

    #una firma guarda 3 cosas

    patrones: tuple[tuple[int, bytes], ...]
    tipo: str
    mime: str

    def coincide(self, datos: bytes) -> bool:
        return all(
            datos[offset:offset + len(esperado)] == esperado
            for offset, esperado in self.patrones
        )


@dataclass(frozen=True)
class Resultado:
    tipo: str
    mime: str


def _firma(tipo: str, mime: str, *patrones: tuple[int, bytes]) -> Firma:
    return Firma(patrones=patrones, tipo=tipo, mime=mime)


FIRMAS: tuple[Firma, ...] = (
    # Documentos
    _firma("PDF", "application/pdf", (0, b"%PDF")),
    _firma("RTF", "application/rtf", (0, b"{\\rtf")),
    # Imágenes
    _firma("PNG", "image/png", (0, b"\x89PNG\r\n\x1a\n")),
    _firma("JPEG", "image/jpeg", (0, b"\xff\xd8\xff")),
    _firma("GIF", "image/gif", (0, b"GIF87a")),
    _firma("GIF", "image/gif", (0, b"GIF89a")),
    _firma("WEBP", "image/webp", (0, b"RIFF"), (8, b"WEBP")),
    _firma("BMP", "image/bmp", (0, b"BM")),
    _firma("ICO", "image/x-icon", (0, b"\x00\x00\x01\x00")),
    _firma("TIFF", "image/tiff", (0, b"II*\x00")),
    _firma("TIFF", "image/tiff", (0, b"MM\x00*")),
    # Audio y video
    _firma("WAV", "audio/wav", (0, b"RIFF"), (8, b"WAVE")),
    _firma("AVI", "video/x-msvideo", (0, b"RIFF"), (8, b"AVI ")),
    _firma("MP3", "audio/mpeg", (0, b"ID3")),
    _firma("MP3", "audio/mpeg", (0, b"\xff\xfb")),
    _firma("FLAC", "audio/flac", (0, b"fLaC")),
    _firma("OGG", "audio/ogg", (0, b"OggS")),
    _firma("MP4", "video/mp4", (4, b"ftyp")),
    _firma("MKV", "video/x-matroska", (0, b"\x1a\x45\xdf\xa3")),
    # Comprimidos
    _firma("ZIP", "application/zip", (0, b"PK\x03\x04")),
    _firma("ZIP", "application/zip", (0, b"PK\x05\x06")),  # zip vacío
    _firma("RAR", "application/vnd.rar", (0, b"Rar!\x1a\x07")),
    _firma("7Z", "application/x-7z-compressed", (0, b"7z\xbc\xaf\x27\x1c")),
    _firma("GZIP", "application/gzip", (0, b"\x1f\x8b")),
    _firma("TAR", "application/x-tar", (257, b"ustar")),
    # Ejecutables y otros
    _firma("EXE", "application/vnd.microsoft.portable-executable", (0, b"MZ")),
    _firma("ELF", "application/x-elf", (0, b"\x7fELF")),
    _firma("SQLite", "application/vnd.sqlite3", (0, b"SQLite format 3\x00")),
)

_OFFICE_POR_CARPETA = (
    ("word/", Resultado("DOCX", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
    ("xl/", Resultado("XLSX", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
    ("ppt/", Resultado("PPTX", "application/vnd.openxmlformats-officedocument.presentationml.presentation")),
)

BYTES_CABECERA = max(off + len(esp) for f in FIRMAS for off, esp in f.patrones)


def obtener_diagnostico(datos: bytes, resultado: Resultado) -> dict:
    """Detalle breve para la consola del navegador, sin almacenar el contenido."""
    muestra = datos[:BYTES_MUESTRA_LOG]
    firma = next((firma for firma in FIRMAS if firma.coincide(datos)), None)
    coincidencias = []
    if firma is not None:
        for offset, esperado in firma.patrones:
            encontrado = datos[offset:offset + len(esperado)]
            coincidencias.append({
                "firma": firma.tipo, "offset": offset, "longitud": len(esperado),
                "esperado_hex": esperado.hex(" "), "encontrado_hex": encontrado.hex(" "),
                "esperado_bits": _bits(esperado), "encontrado_bits": _bits(encontrado),
            })
    return {
        "tamano": len(datos), "muestra_bytes": len(muestra),
        "muestra_hex": muestra.hex(" "), "muestra_bits": _bits(muestra),
        "tipo_detectado": resultado.tipo, "mime": resultado.mime,
        "coincidencias": coincidencias,
    }


def detectar_tipo(datos: bytes) -> Resultado:
    """Devuelve el tipo de archivo según su contenido."""
    if logger.isEnabledFor(logging.DEBUG):
        muestra = datos[:BYTES_MUESTRA_LOG]
        logger.debug(
            "Inicio de deteccion: tamano=%d muestra_bytes=%d "
            "muestra_hex=[%s] muestra_bits=[%s]",
            len(datos), len(muestra), muestra.hex(" "), _bits(muestra),
        )
    if not datos:
        logger.info("Resultado de deteccion: tipo=Vacío (sin contenido)")
        return Resultado("Vacío", "application/x-empty")

    for firma in FIRMAS:
        if firma.coincide(datos):
            _registrar_coincidencia(firma, datos)
            if firma.tipo == "ZIP":
                resultado = _refinar_zip(datos)
            else:
                resultado = Resultado(firma.tipo, firma.mime)
            logger.info("Resultado de deteccion: tipo=%s mime=%s", resultado.tipo, resultado.mime)
            return resultado

    if _es_texto(datos):
        logger.info("Sin firma coincidente: tipo=Texto (muestra UTF-8 válida)")
        return Resultado("Texto", "text/plain")

    logger.info("Sin firma coincidente: tipo=%s", TIPO_DESCONOCIDO)
    return Resultado(TIPO_DESCONOCIDO, MIME_DESCONOCIDO)


def _refinar_zip(datos: bytes) -> Resultado:
    try:
        with zipfile.ZipFile(io.BytesIO(datos)) as zf:
            nombres = zf.namelist()
    except zipfile.BadZipFile:
        return Resultado("ZIP", "application/zip")

    for carpeta, resultado in _OFFICE_POR_CARPETA:
        if any(nombre.startswith(carpeta) for nombre in nombres):
            return resultado
    return Resultado("ZIP", "application/zip")


def _es_texto(datos: bytes, muestra: int = 8192) -> bool:
    """Comprueba una muestra UTF-8, completando el carácter cortado si lo hay."""
    fragmento = datos[:muestra]
    if b"\x00" in fragmento:
        return False
    decoder = codecs.getincrementaldecoder("utf-8")()
    try:
        decoder.decode(fragmento, final=len(datos) <= muestra)
        # Un carácter UTF-8 puede necesitar hasta tres bytes adicionales.
        for offset in range(muestra, min(len(datos), muestra + 3)):
            if not decoder.getstate()[0]:
                break
            decoder.decode(datos[offset:offset + 1])
        decoder.decode(b"", final=True)
    except UnicodeDecodeError:
        return False
    return True


def obtener_extension(nombre: str) -> str:
    return PurePath(nombre).suffix.lstrip(".").lower()

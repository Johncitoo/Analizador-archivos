# vamos a intentar leer lso magic bytes
import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePath

TIPO_DESCONOCIDO = "Desconocido"
MIME_DESCONOCIDO = "application/octet-stream"


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


# El orden importa: las firmas más específicas van primero
# (por ejemplo, WEBP y WAV comparten el prefijo "RIFF").
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

# Los formatos de Office modernos (docx, xlsx, pptx) son archivos ZIP por dentro;
# se distinguen por la carpeta interna que contienen.
_OFFICE_POR_CARPETA = (
    ("word/", Resultado("DOCX", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
    ("xl/", Resultado("XLSX", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
    ("ppt/", Resultado("PPTX", "application/vnd.openxmlformats-officedocument.presentationml.presentation")),
)

# Cuantos bytes del inicio hacen falta para revisar todas las firmas.
BYTES_CABECERA = max(off + len(esp) for f in FIRMAS for off, esp in f.patrones)


def detectar_tipo(datos: bytes) -> Resultado:
    """Devuelve el tipo de archivo según su contenido."""
    if not datos:
        return Resultado("Vacío", "application/x-empty")

    for firma in FIRMAS:
        if firma.coincide(datos):
            if firma.tipo == "ZIP":
                return _refinar_zip(datos)
            return Resultado(firma.tipo, firma.mime)

    if _es_texto(datos):
        return Resultado("Texto", "text/plain")

    return Resultado(TIPO_DESCONOCIDO, MIME_DESCONOCIDO)


def _refinar_zip(datos: bytes) -> Resultado:
    """Distingue DOCX/XLSX/PPTX de un ZIP común mirando sus carpetas internas."""
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
    """Un archivo es texto si no tiene bytes nulos y se puede leer como UTF-8."""
    fragmento = datos[:muestra]
    if b"\x00" in fragmento:
        return False
    try:
        fragmento.decode("utf-8")
    except UnicodeDecodeError as error:
        # Si el corte de la muestra partió un carácter multibyte al final, sigue siendo texto
        return error.start >= len(fragmento) - 3
    return True


def obtener_extension(nombre: str) -> str:
    """'Foto.JPG' -> 'jpg'. Devuelve '' si el nombre no tiene extensión."""
    return PurePath(nombre).suffix.lstrip(".").lower()

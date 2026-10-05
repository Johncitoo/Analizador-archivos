"""Imprime el diagnóstico del backend en la consola del navegador."""

import json

import streamlit.components.v1 as components


def crear_script_consola(resultados: list[dict]) -> str | None:
    reportes = [
        {"nombre": resultado["nombre"], "diagnostico": resultado["diagnostico"]}
        for resultado in resultados if "diagnostico" in resultado
    ]
    if not reportes:
        return None
    # Impide que un nombre con </script> cierre la etiqueta y ejecute HTML.
    payload = json.dumps(reportes, ensure_ascii=True).replace("<", "\\u003c")
    return """<script>
    for (const reporte of REPORTES) {
        const d = reporte.diagnostico;
        console.group("Analizador de archivos:", reporte.nombre);
        console.log("Muestra inicial (" + d.muestra_bytes + " bytes)");
        console.log("Hexadecimal:", d.muestra_hex);
        console.log("Bits:", d.muestra_bits);
        if (d.coincidencias.length) {
            console.log("Patrones coincidentes (offset desde cero):");
            console.table(d.coincidencias);
        } else {
            console.log("Sin coincidencia con las firmas registradas.");
        }
        console.log("Resultado:", d.tipo_detectado, "MIME:", d.mime);
        console.groupEnd();
    }
    </script>""".replace("REPORTES", payload)


def registrar_en_navegador(resultados: list[dict]) -> None:
    script = crear_script_consola(resultados)
    if script is not None:
        components.html(script, height=0)

"""Pantallas del frontend (Streamlit). Solo muestra datos: toda la lógica vive en el backend."""

import pandas as pd
import streamlit as st

import api
from diagnostico import registrar_en_navegador

TAMANO_MAXIMO = 20 * 1024 * 1024


def formatear_tamano(num_bytes: int) -> str:
    for unidad in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unidad == "GB":
            return f"{num_bytes:.0f} {unidad}" if unidad == "B" else f"{num_bytes:.1f} {unidad}"
        num_bytes /= 1024


def mostrar_error(error: api.ErrorAPI) -> None:
    st.error(str(error))


st.set_page_config(page_title="Analizador de Archivos", layout="wide")
st.title("Analizador de Archivos")
st.caption("Detecta el tipo real de un archivo leyendo sus primeros bytes (magic bytes), sin importar su extensión.")

tab_analizar, tab_estadisticas, tab_historial = st.tabs(["Analizar", "Estadísticas", "Historial"])

# --- Analizar ---------------------------------------------------------------
with tab_analizar:
    archivos = st.file_uploader(
        "Selecciona uno o más archivos (máximo 20 MB cada uno)",
        accept_multiple_files=True,
    )

    if st.button("Analizar", type="primary", disabled=not archivos):
        resultados = []
        for archivo in archivos:
            if archivo.size > TAMANO_MAXIMO:
                st.error(f"{archivo.name}: El archivo supera el máximo de 20 MB.")
                continue
            try:
                resultados.append(api.subir_archivo(archivo.name, archivo.getvalue()))
            except api.ErrorAPI as error:
                st.error(f"{archivo.name}: {error}")

        if resultados:
            registrar_en_navegador(resultados)
            st.success(f"Se analizaron {len(resultados)} archivo(s).")
            tabla = pd.DataFrame(resultados)
            st.dataframe(
                pd.DataFrame({
                    "Nombre": tabla["nombre"],
                    "Extensión": tabla["extension"],
                    "Tipo detectado": tabla["tipo_detectado"],
                    "MIME": tabla["mime"],
                    "Tamaño": tabla["tamano"].map(formatear_tamano),
                }),
                hide_index=True,
                width="stretch",
            )

# --- Estadísticas -----------------------------------------------------------
with tab_estadisticas:
    try:
        estadisticas = api.obtener_estadisticas()
    except api.ErrorAPI as error:
        mostrar_error(error)
    else:
        if estadisticas["total_archivos"] == 0:
            st.info("Aún no se han analizado archivos.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Archivos analizados", estadisticas["total_archivos"])
            col2.metric("Tipos distintos", len(estadisticas["por_tipo"]))
            col3.metric("Tamaño total", formatear_tamano(estadisticas["tamano_total"]))

            por_tipo = pd.DataFrame(estadisticas["por_tipo"]).rename(columns={
                "tipo_detectado": "Tipo",
                "cantidad": "Cantidad",
                "tamano_total": "Tamaño total",
            })
            por_tipo["Porcentaje"] = (por_tipo["Cantidad"] / estadisticas["total_archivos"] * 100).round(1)

            col_tabla, col_grafico = st.columns(2)
            with col_tabla:
                st.subheader("Archivos por tipo")
                st.dataframe(
                    por_tipo.assign(**{"Tamaño total": por_tipo["Tamaño total"].map(formatear_tamano)}),
                    hide_index=True,
                    width="stretch",
                    column_config={"Porcentaje": st.column_config.NumberColumn(format="%.1f %%")},
                )
            with col_grafico:
                st.subheader("Distribución")
                st.bar_chart(por_tipo.set_index("Tipo")["Cantidad"])

# --- Historial --------------------------------------------------------------
with tab_historial:
    try:
        historial = api.listar_archivos()
    except api.ErrorAPI as error:
        mostrar_error(error)
    else:
        if not historial:
            st.info("Aún no se han analizado archivos.")
        else:
            tabla = pd.DataFrame(historial)
            st.dataframe(
                pd.DataFrame({
                    "Fecha": pd.to_datetime(tabla["fecha"]).dt.strftime("%d-%m-%Y %H:%M"),
                    "Nombre": tabla["nombre"],
                    "Extensión": tabla["extension"],
                    "Tipo detectado": tabla["tipo_detectado"],
                    "MIME": tabla["mime"],
                    "Tamaño": tabla["tamano"].map(formatear_tamano),
                }),
                hide_index=True,
                width="stretch",
            )

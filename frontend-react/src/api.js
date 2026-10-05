// Cliente de la API REST del backend. Todas las llamadas HTTP pasan por aquí,
// así que son visibles en la pestaña Network del navegador.

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000/api").replace(/\/$/, "");

async function pedir(ruta, opciones) {
  let respuesta;
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, opciones);
  } catch {
    throw new Error("No se pudo conectar con el backend.");
  }

  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    throw new Error(mensajeDeError(datos) || `El backend respondió con error ${respuesta.status}.`);
  }
  return datos;
}

function mensajeDeError(datos) {
  if (!datos) return null;
  if (datos.detail) return datos.detail;
  // Errores de validación de DRF: { "archivo": ["mensaje"] }
  return Object.values(datos).flat().join(" ");
}

export function subirArchivo(archivo) {
  const formulario = new FormData();
  formulario.append("archivo", archivo);
  return pedir("/archivos/", { method: "POST", body: formulario });
}

export function listarArchivos() {
  return pedir("/archivos/");
}

export function obtenerEstadisticas() {
  return pedir("/archivos/estadisticas/");
}

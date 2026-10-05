import { registrarDiagnostico } from "./diagnostico.js";

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
  return Object.values(datos).flat().join(" ");
}

export async function subirArchivo(archivo) {
  const formulario = new FormData();
  formulario.append("archivo", archivo);
  const resultado = await pedir("/archivos/?diagnostico=1", { method: "POST", body: formulario });
  registrarDiagnostico(resultado);
  return resultado;
}

export function listarArchivos() {
  return pedir("/archivos/");
}

export function obtenerEstadisticas() {
  return pedir("/archivos/estadisticas/");
}

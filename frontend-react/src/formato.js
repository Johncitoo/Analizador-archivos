export function formatearTamano(bytes) {
  const unidades = ["B", "KB", "MB", "GB"];
  let valor = bytes;
  let i = 0;
  while (valor >= 1024 && i < unidades.length - 1) {
    valor /= 1024;
    i++;
  }
  return i === 0 ? `${valor} B` : `${valor.toFixed(1)} ${unidades[i]}`;
}

export function formatearFecha(iso) {
  return new Date(iso).toLocaleString("es-CL", {
    timeZone: "America/Santiago",
    dateStyle: "short",
    timeStyle: "short",
  });
}

const EQUIVALENCIAS = { jpg: "jpeg", tif: "tiff", gz: "gzip", tgz: "gzip", m4a: "mp4", mov: "mp4" };

const SIN_COMPARAR = ["texto", "desconocido", "vacío"];

export function extensionNoCoincide(extension, tipo) {
  const tipoNormalizado = tipo.toLowerCase();
  if (!extension || SIN_COMPARAR.includes(tipoNormalizado)) return false;
  return (EQUIVALENCIAS[extension] || extension) !== tipoNormalizado;
}

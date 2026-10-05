// Los datos llegan del detector; no se generan firmas en el navegador.
export function registrarDiagnostico(resultado) {
  const diagnostico = resultado.diagnostico;
  if (!diagnostico) return;

  console.group("Analizador de archivos:", resultado.nombre);
  console.log(`Muestra inicial (${diagnostico.muestra_bytes} bytes)`);
  console.log("Hexadecimal:", diagnostico.muestra_hex);
  console.log("Bits:", diagnostico.muestra_bits);
  if (diagnostico.coincidencias.length) {
    console.log("Patrones coincidentes (offset desde cero):");
    console.table(diagnostico.coincidencias);
  } else {
    console.log("Sin coincidencia con las firmas registradas.");
  }
  console.log("Resultado:", diagnostico.tipo_detectado, "MIME:", diagnostico.mime);
  console.groupEnd();
}

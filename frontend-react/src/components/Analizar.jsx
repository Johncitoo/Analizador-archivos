import { useState } from "react";

import { subirArchivo } from "../api.js";
import TablaArchivos from "./TablaArchivos.jsx";

const TAMANO_MAXIMO = 20 * 1024 * 1024; // 20 MB

export default function Analizar() {
  const [archivos, setArchivos] = useState([]);
  const [resultados, setResultados] = useState([]);
  const [errores, setErrores] = useState([]);
  const [cargando, setCargando] = useState(false);

  async function analizar(evento) {
    evento.preventDefault();
    setCargando(true);
    setResultados([]);
    setErrores([]);

    const nuevosResultados = [];
    const nuevosErrores = [];
    for (const archivo of archivos) {
      if (archivo.size > TAMANO_MAXIMO) {
        nuevosErrores.push(`${archivo.name}: supera el máximo de 20 MB.`);
        continue;
      }
      try {
        nuevosResultados.push(await subirArchivo(archivo));
      } catch (error) {
        nuevosErrores.push(`${archivo.name}: ${error.message}`);
      }
    }

    setResultados(nuevosResultados);
    setErrores(nuevosErrores);
    setCargando(false);
  }

  return (
    <section>
      <form onSubmit={analizar} className="subida">
        <label htmlFor="archivos">Selecciona uno o más archivos (máximo 20 MB cada uno)</label>
        <input
          id="archivos"
          type="file"
          multiple
          onChange={(evento) => setArchivos([...evento.target.files])}
        />
        <button type="submit" disabled={archivos.length === 0 || cargando}>
          {cargando ? "Analizando..." : "Analizar"}
        </button>
      </form>

      {errores.map((error) => (
        <p key={error} className="mensaje error">{error}</p>
      ))}

      {resultados.length > 0 && (
        <>
          <p className="mensaje exito">Se analizaron {resultados.length} archivo(s).</p>
          <TablaArchivos archivos={resultados} />
        </>
      )}
    </section>
  );
}

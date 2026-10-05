import { useEffect, useState } from "react";

import { listarArchivos } from "../api.js";
import TablaArchivos from "./TablaArchivos.jsx";

export default function Historial() {
  const [archivos, setArchivos] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    listarArchivos().then(setArchivos).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="mensaje error">{error}</p>;
  if (!archivos) return <p className="mensaje">Cargando...</p>;
  if (archivos.length === 0) return <p className="mensaje">Aún no se han analizado archivos.</p>;

  return (
    <section>
      <TablaArchivos archivos={archivos} mostrarFecha />
    </section>
  );
}

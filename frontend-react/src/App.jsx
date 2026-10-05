import { useState } from "react";

import Analizar from "./components/Analizar.jsx";
import Estadisticas from "./components/Estadisticas.jsx";
import Historial from "./components/Historial.jsx";

const PESTANAS = [
  { id: "analizar", titulo: "Analizar", componente: Analizar },
  { id: "estadisticas", titulo: "Estadísticas", componente: Estadisticas },
  { id: "historial", titulo: "Historial", componente: Historial },
];

export default function App() {
  const [activa, setActiva] = useState("analizar");
  const Pestana = PESTANAS.find((p) => p.id === activa).componente;

  return (
    <main>
      <header>
        <h1>Analizador de Archivos</h1>
        <p className="subtitulo">
          Detecta el tipo real de un archivo leyendo sus primeros bytes (magic bytes), sin importar su extensión.
        </p>
      </header>

      <nav>
        {PESTANAS.map((p) => (
          <button
            key={p.id}
            className={p.id === activa ? "activa" : ""}
            onClick={() => setActiva(p.id)}
          >
            {p.titulo}
          </button>
        ))}
      </nav>

      {/* key fuerza a recargar los datos cada vez que se entra a la pestaña */}
      <Pestana key={activa} />
    </main>
  );
}

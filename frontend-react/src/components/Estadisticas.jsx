import { useEffect, useState } from "react";

import { obtenerEstadisticas } from "../api.js";
import { formatearTamano } from "../formato.js";

export default function Estadisticas() {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    obtenerEstadisticas().then(setDatos).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="mensaje error">{error}</p>;
  if (!datos) return <p className="mensaje">Cargando...</p>;
  if (datos.total_archivos === 0) return <p className="mensaje">Aún no se han analizado archivos.</p>;

  const maximo = Math.max(...datos.por_tipo.map((fila) => fila.cantidad));

  return (
    <section>
      <div className="metricas">
        <div className="metrica">
          <span className="valor">{datos.total_archivos}</span>
          <span className="etiqueta">Archivos analizados</span>
        </div>
        <div className="metrica">
          <span className="valor">{datos.por_tipo.length}</span>
          <span className="etiqueta">Tipos distintos</span>
        </div>
        <div className="metrica">
          <span className="valor">{formatearTamano(datos.tamano_total)}</span>
          <span className="etiqueta">Tamaño total</span>
        </div>
      </div>

      <div className="columnas">
        <div>
          <h2>Archivos por tipo</h2>
          <table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th className="numero">Cantidad</th>
                <th className="numero">Porcentaje</th>
                <th className="numero">Tamaño total</th>
              </tr>
            </thead>
            <tbody>
              {datos.por_tipo.map((fila) => (
                <tr key={fila.tipo_detectado}>
                  <td>{fila.tipo_detectado}</td>
                  <td className="numero">{fila.cantidad}</td>
                  <td className="numero">{((fila.cantidad / datos.total_archivos) * 100).toFixed(1)} %</td>
                  <td className="numero">{formatearTamano(fila.tamano_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <h2>Distribución</h2>
          <div className="grafico">
            {datos.por_tipo.map((fila) => (
              <div key={fila.tipo_detectado} className="barra-fila">
                <span className="barra-etiqueta">{fila.tipo_detectado}</span>
                <div className="barra-fondo">
                  <div className="barra" style={{ width: `${(fila.cantidad / maximo) * 100}%` }} />
                </div>
                <span className="barra-valor">{fila.cantidad}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

import { extensionNoCoincide, formatearFecha, formatearTamano } from "../formato.js";

export default function TablaArchivos({ archivos, mostrarFecha = false }) {
  return (
    <table>
      <thead>
        <tr>
          {mostrarFecha && <th>Fecha</th>}
          <th>Nombre</th>
          <th>Extensión</th>
          <th>Tipo detectado</th>
          <th>MIME</th>
          <th className="numero">Tamaño</th>
        </tr>
      </thead>
      <tbody>
        {archivos.map((archivo) => {
          const noCoincide = extensionNoCoincide(archivo.extension, archivo.tipo_detectado);
          return (
            <tr key={archivo.id}>
              {mostrarFecha && <td>{formatearFecha(archivo.fecha)}</td>}
              <td>{archivo.nombre}</td>
              <td>{archivo.extension || "-"}</td>
              <td>
                {archivo.tipo_detectado}
                {noCoincide && <span className="alerta">no coincide con la extensión</span>}
              </td>
              <td className="mime">{archivo.mime}</td>
              <td className="numero">{formatearTamano(archivo.tamano)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

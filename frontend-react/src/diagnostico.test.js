import { beforeEach, describe, expect, it, vi } from "vitest";
import { registrarDiagnostico } from "./diagnostico.js";

const patron = {
  firma: "PDF", offset: 0, longitud: 4,
  esperado_hex: "25 50 44 46", encontrado_hex: "25 50 44 46",
  esperado_bits: "00100101 01010000 01000100 01000110",
  encontrado_bits: "00100101 01010000 01000100 01000110",
};

function resultado(coincidencias = [patron], tipo = "PDF") {
  return {
    nombre: "prueba.jpg",
    diagnostico: {
      muestra_bytes: 4, muestra_hex: patron.encontrado_hex,
      muestra_bits: patron.encontrado_bits, tipo_detectado: tipo,
      mime: "application/pdf", coincidencias,
    },
  };
}

describe("diagnóstico en la consola del navegador", () => {
  beforeEach(() => {
    for (const metodo of ["group", "groupEnd", "log", "table"]) {
      vi.spyOn(console, metodo).mockImplementation(() => {});
    }
  });

  it("muestra los bits y la tabla exacta recibidos del detector", () => {
    registrarDiagnostico(resultado());
    expect(console.group).toHaveBeenCalledWith("Analizador de archivos:", "prueba.jpg");
    expect(console.log).toHaveBeenCalledWith("Bits:", patron.encontrado_bits);
    expect(console.table).toHaveBeenCalledWith([patron]);
    expect(console.log).toHaveBeenCalledWith("Resultado:", "PDF", "MIME:", "application/pdf");
    expect(console.groupEnd).toHaveBeenCalledOnce();
  });

  it("no imprime nada si el backend omite el diagnóstico", () => {
    registrarDiagnostico({ nombre: "prueba.pdf", tipo_detectado: "PDF" });
    expect(console.group).not.toHaveBeenCalled();
    expect(console.log).not.toHaveBeenCalled();
    expect(console.table).not.toHaveBeenCalled();
  });

  it.each(["Texto", "Desconocido"])("no inventa firmas para %s", (tipo) => {
    registrarDiagnostico(resultado([], tipo));
    expect(console.log).toHaveBeenCalledWith("Sin coincidencia con las firmas registradas.");
    expect(console.table).not.toHaveBeenCalled();
  });

  it("conserva todos los patrones de una firma con varias posiciones", () => {
    const patrones = [{ ...patron, offset: 0 }, { ...patron, offset: 8 }];
    registrarDiagnostico(resultado(patrones));
    expect(console.table).toHaveBeenCalledWith(patrones);
  });

  it("trata un nombre manipulado como texto y no inserta HTML", () => {
    const datos = resultado();
    datos.nombre = '</script><img src=x onerror="alert(1)">';
    const contenidoAntes = document.body.innerHTML;
    registrarDiagnostico(datos);
    expect(console.group).toHaveBeenCalledWith("Analizador de archivos:", datos.nombre);
    expect(document.body.innerHTML).toBe(contenidoAntes);
    expect(document.querySelector("img")).toBeNull();
  });
});

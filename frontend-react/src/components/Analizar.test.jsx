import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { subirArchivo } from "../api.js";
import Analizar from "./Analizar.jsx";

vi.mock("../api.js", () => ({ subirArchivo: vi.fn() }));
const LIMITE = 20 * 1024 * 1024;

function archivoConTamano(nombre, tamano) {
  const archivo = new File(["contenido"], nombre);
  // Simula el tamaño reportado por el navegador sin reservar 20 MiB por prueba.
  Object.defineProperty(archivo, "size", { value: tamano });
  return archivo;
}

function respuesta(nombre, id = 1) {
  return { id, nombre, extension: "pdf", tipo_detectado: "PDF", mime: "application/pdf", tamano: 4 };
}

describe("subida de archivos", () => {
  beforeEach(() => vi.clearAllMocks());

  async function analizar(archivos) {
    const user = userEvent.setup();
    render(<Analizar />);
    await user.upload(screen.getByLabelText(/Selecciona uno o más archivos/), archivos);
    await user.click(screen.getByRole("button", { name: "Analizar" }));
  }

  it("desactiva Analizar si no se seleccionó ningún archivo", () => {
    render(<Analizar />);
    expect(screen.getByRole("button", { name: "Analizar" }).disabled).toBe(true);
  });

  it("acepta un archivo de exactamente 20 MiB", async () => {
    const archivo = archivoConTamano("limite.pdf", LIMITE);
    subirArchivo.mockResolvedValue(respuesta(archivo.name));
    await analizar([archivo]);
    expect(await screen.findByText("Se analizaron 1 archivo(s).")).toBeTruthy();
    expect(subirArchivo).toHaveBeenCalledExactlyOnceWith(archivo);
  });

  it("rechaza un byte sobre el límite sin llamar a la API", async () => {
    await analizar([archivoConTamano("grande.pdf", LIMITE + 1)]);
    expect(await screen.findByText("grande.pdf: supera el máximo de 20 MB.")).toBeTruthy();
    expect(subirArchivo).not.toHaveBeenCalled();
  });

  it("continúa con el archivo válido después de uno demasiado grande", async () => {
    const valido = archivoConTamano("valido.pdf", 4);
    subirArchivo.mockResolvedValue(respuesta(valido.name));
    await analizar([archivoConTamano("grande.pdf", LIMITE + 1), valido]);
    expect(await screen.findByText("Se analizaron 1 archivo(s).")).toBeTruthy();
    expect(screen.getByText("grande.pdf: supera el máximo de 20 MB.")).toBeTruthy();
    expect(subirArchivo).toHaveBeenCalledExactlyOnceWith(valido);
  });

  it("permite analizar varios archivos en una misma selección", async () => {
    const archivos = [archivoConTamano("uno.pdf", 4), archivoConTamano("dos.pdf", 4)];
    subirArchivo.mockResolvedValueOnce(respuesta("uno.pdf", 1)).mockResolvedValueOnce(respuesta("dos.pdf", 2));
    await analizar(archivos);
    expect(await screen.findByText("Se analizaron 2 archivo(s).")).toBeTruthy();
    expect(subirArchivo).toHaveBeenCalledTimes(2);
    expect(screen.getByText("uno.pdf")).toBeTruthy();
    expect(screen.getByText("dos.pdf")).toBeTruthy();
  });

  it("muestra un rechazo de la API y permite analizar el siguiente archivo", async () => {
    subirArchivo.mockRejectedValueOnce(new Error("Extensión demasiado larga.")).mockResolvedValueOnce(respuesta("valido.pdf"));
    await analizar([archivoConTamano("invalido.pdf", 4), archivoConTamano("valido.pdf", 4)]);
    expect(await screen.findByText("Se analizaron 1 archivo(s).")).toBeTruthy();
    expect(screen.getByText("invalido.pdf: Extensión demasiado larga.")).toBeTruthy();
  });
});

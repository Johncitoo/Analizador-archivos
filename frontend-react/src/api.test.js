import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { subirArchivo } from "./api.js";
import { registrarDiagnostico } from "./diagnostico.js";

vi.mock("./diagnostico.js", () => ({ registrarDiagnostico: vi.fn() }));

describe("cliente de subidas", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.clearAllMocks();
  });
  afterEach(() => vi.unstubAllGlobals());

  it("envía el archivo y solicita diagnóstico sin fijar Content-Type", async () => {
    const archivo = new File(["%PDF"], "foto.jpg");
    const resultado = { nombre: "foto.jpg", tipo_detectado: "PDF", diagnostico: { coincidencias: [] } };
    fetch.mockResolvedValue({ ok: true, json: async () => resultado });
    expect(await subirArchivo(archivo)).toEqual(resultado);
    const [url, opciones] = fetch.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/archivos/?diagnostico=1");
    expect(opciones.method).toBe("POST");
    expect(opciones.body.get("archivo")).toBe(archivo);
    expect(opciones.headers).toBeUndefined();
    expect(registrarDiagnostico).toHaveBeenCalledWith(resultado);
  });

  it("acepta respuestas de producción sin diagnóstico", async () => {
    const resultado = { nombre: "foto.png", tipo_detectado: "PNG" };
    fetch.mockResolvedValue({ ok: true, json: async () => resultado });
    expect(await subirArchivo(new File(["contenido"], "foto.png"))).toEqual(resultado);
  });

  it("muestra el error de validación sin imprimir un diagnóstico falso", async () => {
    fetch.mockResolvedValue({ ok: false, status: 400, json: async () => ({ archivo: ["Extensión demasiado larga."] }) });
    await expect(subirArchivo(new File(["hola"], "prueba.txt"))).rejects.toThrow("Extensión demasiado larga.");
    expect(registrarDiagnostico).not.toHaveBeenCalled();
  });
});

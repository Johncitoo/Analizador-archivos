# Ejemplos para probar UTF-8

- `utf8_valido.txt`: 8191 letras `a` seguidas por una `ñ` (bytes `C3 B1`). La muestra de 8192 bytes corta la `ñ`; el resultado esperado es **Texto**.
- `byte_invalido.bin`: `hola` seguido por el byte `FF`, que no es válido en UTF-8. El resultado esperado es **Desconocido**.

Selecciona ambos archivos en la pestaña Analizar de http://localhost:5173 y pulsa Analizar. Con el backend en desarrollo (`DJANGO_DEBUG=1`), abre F12 → Consola para ver la muestra y el diagnóstico. Texto y Desconocido no muestran patrones coincidentes porque se clasifican sin una firma del catálogo.

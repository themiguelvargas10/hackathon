# AquaGuard

**Un panel local que detecta intervalos sospechosos de agua y energía y explica qué revisar.** Proyecto de preparación para AguaSegura AI, 22 de octubre de 2026. Equipo de cinco personas.

Todos los datos son simulados. Una alerta no confirma fuga, ataque ni ahorro.

## Abrir en dos pasos

1. Extrae todo el ZIP a una carpeta. Necesitas Python 3.12 instalado.
2. En Windows, abre **INICIAR_WINDOWS.cmd** con doble clic. Se abrirá el navegador.

La aplicación está en **http://127.0.0.1:8501**. Mantén abierta la terminal. Ctrl+C detiene el servidor.

En macOS/Linux: `sh INICIAR_MAC_LINUX.sh` desde la carpeta extraída.

También puedes ejecutar `python server.py` (o `py -3.12 server.py` en Windows).
Si el puerto está ocupado: `python server.py --port 8502`.
Para no abrir navegador automáticamente: `python server.py --no-browser`.

**No necesitas pip, entornos virtuales, cuentas, claves de API, GPU ni internet para ejecutar el proyecto.** Si aún no tienes Python, su instalación debe hacerse previamente. Usa https://www.python.org/downloads/ o el soporte de tu institución. No abras index.html directamente: necesita el servidor local.

## Qué incluye

- Monitor de tres sitios ficticios con filtros de fechas UTC, sitio, partición y detector.
- Agua, energía, PUE e intensidad hídrica con agregación correcta.
- Gráficas sin CDN y tabla accesible de todos los intervalos seleccionados.
- Fichas de alertas con evidencia, mediana histórica y comprobaciones humanas.
- Reglas explicables y una implementación educativa de Isolation Forest por sitio.
- Comparación con las mismas entradas numéricas y eventos OT separados.
- Falsos positivos, falsos negativos, precisión, recall y F1.
- Medición repetida de inferencia, separada del entrenamiento; sin inventar consumo energético.
- Exportación CSV, informe JSON y medición JSON.
- Validación de datos y pruebas automáticas sin paquetes externos.
- Guion de demo, reparto de tareas y ficha metodológica en `docs/`.

## Ruta tecnológica

Se conserva Python y el CSV del kit CIFOX. La interfaz es HTML/CSS/JavaScript servido por la biblioteca estándar de Python. La descarga de dependencias no estaba disponible durante la construcción, por lo que esta entrega funciona sin Streamlit ni scikit-learn. Isolation Forest es una implementación educativa propia y **no se presenta como equivalente validado de scikit-learn**. Todo se ejecuta en un proceso local, sin servicio de nube.

## Recorrido de prueba

1. Abre el panel: semana completa, 504 registros y 21 alertas con reglas.
2. Comprueba los totales: 31,593.1444 L; 105,256.0051 kWh totales; 82,656.4237 kWh IT.
3. PUE esperado: 1.27341591117. Intensidad hídrica: 0.38222249386 L/kWh IT.
4. Pulsa **Recorrer un caso**: selecciona SIM-B y evaluación, y abre evidencia.
5. Cambia a **Evaluación del detector**, restablece filtros y compara los métodos.
6. Con los datos originales, las reglas numéricas detectan 16/16 y no producen falsas alarmas; Isolation Forest detecta 16/16 y produce 23 falsas alarmas en evaluación. Estas cifras no prueban eficacia externa.
7. Pulsa **Medir ahora** y descarga el resultado. El benchmark siempre usa toda la evaluación.
8. Prueba un periodo fuera del CSV: muestra ausencia de datos y cocientes indefinidos.
9. Repite sin conexión a internet.

## Pruebas y resultados

Desde la raíz:

```text
python -m unittest discover -s tests -v
python tools/export_report.py
```

En Windows puedes sustituir `python` por `py -3.12`. El informe se escribe en `results/local_report.json` y contiene hash del CSV, métricas, evaluación y tiempos del equipo que lo ejecuta. `results/verification.json` documenta la corrida de entrega, no el rendimiento de tu equipo.

## Estructura

```text
AquaGuard/
  server.py                  Servidor y API local
  aquaguard/core.py          Validación, métricas, detectores y evaluación
  web/                      Interfaz sin dependencias externas
  data/                     CSV original CIFOX
  tests/                    Pruebas de cálculos, datos, aislamiento y API
  tools/export_report.py    Informe reproducible desde terminal
  docs/                     Método, demo y plan de equipo
  results/                  Evidencia de verificación
  LICENSE                   Licencia MIT original CIFOX
  NOTICE.md                 Atribución y aportaciones
```

## Contrato de API

- `GET /api/health`: estado del servidor y número de filas.
- `GET /api/dashboard`: métricas, serie, alertas y comparación.
- `GET /api/export.json`: mismo informe para descargar.
- `GET /api/alerts.csv`: alertas filtradas.
- `POST /api/benchmark`: tres mediciones de inferencia sin filtros.

Filtros: `site=all|SIM-A|SIM-B|SIM-C`, `start=AAAA-MM-DD`, `end=AAAA-MM-DD`, `split=all|referencia|evaluacion`, `method=rules|forest`. Las fechas incluyen el día completo UTC. Parámetros inválidos devuelven 400; rutas desconocidas 404. No hay endpoints de carga ni modificación.

## Límites de la entrega

- Los umbrales son didácticos. Los datos se construyeron para que las reglas detectaran las anomalías.
- El modelo aprende de referencia y el umbral se calibra en esa misma referencia. No existe conjunto independiente para calibración; una validación real necesitaría más datos.
- Los eventos OT no entran al experimento numérico y se muestran por separado.
- Cada sitio representa una refrigeración distinta, con condiciones distintas: no permite una comparación causal de tecnologías.
- La intensidad hídrica es captación local, sin agua indirecta ni retornos; no acredita WUE normalizada, potabilidad ni ahorro.
- La medición es tiempo de ejecución, no energía, carbono o agua. Corridas cortas pueden ser ruidosas.
- Servidor solo local, de demostración: sin autenticación ni controles para producción. No conectarlo a OT ni usar datos reales.
- No se han verificado las bases oficiales completas. Confirmar tamaño del equipo, reutilización de código, IA generativa, horarios y entregables con la organización.
- Las 16 pruebas automatizadas y la sintaxis JavaScript pasaron. El entorno bloqueó la conexión del navegador al servidor local: la revisión visual e interacción de extremo a extremo siguen pendientes en la laptop del equipo. Ver `docs/VERIFICACION.md`.

## Si algo falla

**Python no encontrado:** instala Python 3.12; vuelve a abrir la terminal o el lanzador.

**No aparece la página:** abre la URL impresa en la terminal y comprueba que el proceso siga activo.

**Puerto ocupado:** usa `--port 8502` y abre la nueva dirección.

**CSV inválido:** la terminal indica la fila problemática. Restaura el CSV incluido o corrige el dato antes de volver a iniciar. El servidor carga los datos al arrancar: reinícialo después de editar el CSV.

**Los filtros no encuentran datos:** el CSV solo contiene del 12 al 18 de octubre de 2026. Referencia abarca los tres primeros días; evaluación los cuatro siguientes.

**Más alertas con IA:** el modelo produce falsos positivos en este conjunto. La evaluación los muestra expresamente. No ajustes el umbral mirando evaluación si vas a reportarla como independiente.

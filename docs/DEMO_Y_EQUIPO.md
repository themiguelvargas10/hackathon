# Demo y plan de equipo

## Guion de práctica (3 minutos)

**0:00-0:30 — Problema.** “Una persona operadora necesita saber qué intervalos de agua y energía revisar. AquaGuard reúne señales y evidencia.”

**0:30-1:00 — Alcance.** Mostrar DATOS SIMULADOS. Explicar tres sitios y una semana. PUE e intensidad hídrica son cocientes de sumas; no potabilidad ni ahorro demostrado.

**1:00-2:00 — Caso.** Pulsar Recorrer un caso. Abrir una alerta de SIM-B. Leer el valor, referencia y comprobación humana. Mostrar la gráfica y la tabla.

**2:00-2:30 — Evaluación.** Restablecer filtros y abrir evaluación. Reglas detectan las 16 anomalías numéricas sin falsas alarmas; el bosque detecta 16 y genera 23 falsas alarmas. Explicar que el dataset favorece a las reglas. Mostrar tiempos solo si ya se midieron en la laptop de demo.

**2:30-3:00 — Aportación y límites.** Fichas explicables, evaluación con entradas iguales, ejecución local y exportación. Tres límites: datos sintéticos, comparación de sitios no causal y tiempo no equivalente a energía. Próximo paso: validación independiente con operadores.

Los tres minutos son práctica sugerida por la guía, no un requisito oficial confirmado.

## Reparto

| Persona | Entrega | Archivos principales |
|---|---|---|
| 1: integración | Versión que todos pueden arrancar | server.py, README.md |
| 2: datos | Fórmulas y calidad verificadas | aquaguard/core.py, data/, docs/METODO_Y_DATOS.md |
| 3: detector | Evaluación y comparación | aquaguard/core.py, tests/ |
| 4: interfaz | Recorrido legible y accesible | web/ |
| 5: comunicación | Pitch, pruebas de usuario y respaldo | docs/, capturas propias |

Personas 2 y 3 deben coordinar cambios en core.py. Una sola persona integra la versión final. Usen Git si ya lo dominan; de otro modo, intercambien archivos delimitados y eviten sobrescribir trabajo sin comparar.

## Antes de salir

- Ejecutar pruebas y recorrido en laptop principal.
- Ejecutar en una segunda laptop con Python instalado.
- Arrancar sin internet, guardar CSV, ZIP y capturas o vídeo.
- Llevar cargadores y acordar quién presenta.
- Todos saben explicar datos, mejora y límites.

## Al recibir las bases

Confirmar tamaño del equipo, código previo, herramientas generativas, reutilización del kit, reto, rúbrica, hora y plataforma de entrega, duración del pitch y propiedad intelectual. Este proyecto debe adaptarse a esas reglas; no se afirma elegibilidad anticipada.

Distribuir el tiempo: 10 % reglas y alcance, 45 % adaptación e integración, 20 % pruebas, 15 % documentación y 10 % ensayo. No ampliar funciones durante el último bloque.

## Respuestas cortas para preguntas del jurado

**¿Dónde está la IA?** En el bosque de aislamiento ajustado por sitio sobre referencia, ejecutado en CPU. Es educativo y no usa servicios externos.

**¿La IA es mejor?** No en este ejemplo: detecta las anomalías numéricas pero genera falsas alarmas. Mostramos la comparación para decidir con evidencia.

**¿Cuánta agua ahorraron?** No se demostró ahorro. Se construyó una herramienta de revisión sobre datos simulados.

**¿Qué hicieron ustedes?** Adaptar y comprender la solución, explicar la arquitectura y evaluación, revisar cada componente, y declarar el uso de asistencia de IA según las reglas. No atribuirse código generado como escrito íntegramente a mano.

**¿Sirve en una instalación real?** Harían falta datos y validación operativa independiente, calibración y controles de producción.

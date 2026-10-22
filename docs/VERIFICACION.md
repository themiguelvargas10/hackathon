# Verificación de la entrega

Entorno: Python 3.12, Windows. Sin dependencias externas instaladas.

## Comprobado

- 16 pruebas unitarias y del contrato HTTP aprobadas.
- Fórmulas contrastadas con los valores de referencia publicados en el kit CIFOX.
- Vacíos, fechas inválidas, duplicados, números no finitos, dominios inválidos y huecos horarios.
- Invariancia de predicciones al cambiar etiquetas y escenarios.
- Invariancia del ajuste al cambiar las filas de evaluación.
- Separación de objetivo numérico y eventos OT.
- Filtros y exportaciones JSON/CSV.
- Respuestas HTTP serializadas, rutas estáticas, códigos de error y rechazo de origen ajeno al medir.
- Sintaxis de JavaScript comprobada con Node.
- Arranque del servidor local confirmado: anuncia la URL y carga los 504 registros.
- Informe reproducible en results/verification.json.

## Limitación de verificación

Las conexiones al servidor local están bloqueadas en el entorno de construcción. El navegador integrado devolvió ERR_CONNECTION_TIMED_OUT. Por ello **no se completó la revisión visual ni el recorrido interactivo en navegador**. Las pruebas HTTP ejercitan el parser y las respuestas en memoria, no una conexión TCP real.

El archivo de arranque para Windows y el script macOS/Linux se entregan, pero no se accionaron mediante doble clic en una instalación externa. La portabilidad a macOS/Linux no se ejecutó en este entorno.

Antes de presentar: arrancar con INICIAR_WINDOWS.cmd, seguir el recorrido del README y revisar vista de escritorio, filtros, pestañas, ficha de alerta, exportaciones y medición. Repetir sin conexión y en una segunda laptop.

Estas limitaciones de entorno no equivalen a una certificación de que la interfaz esté libre de fallos. No se afirma revisión visual completa.

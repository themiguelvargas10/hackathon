# AquaGuard Hotel: SIEM para monitoreo y triage de agua

## Propuesta de valor

Para hoteles de Mérida: reunir mediciones de agua y actividad operativa en una consola que detecta consumos atípicos, prioriza revisiones y conserva evidencia de la respuesta. El hotel obtiene trazabilidad de incidentes y puede verificar cambios de consumo con ocupación y actividad comparables. No se promete ahorro antes de una línea base y un piloto medido.

## Lo que aporta el documento recibido

Se agregó como referencia local [`estadisticas_agua_hoteles.pdf`](referencias/estadisticas_agua_hoteles.pdf). Describe rangos generales: 140–400 L por huésped/noche; 300–1,200 L por habitación/día; posibles fugas de hasta 750 L/día por inodoros; y varios porcentajes sobre distribución de usos y pérdidas.

El PDF no identifica fuentes, establecimientos, tamaños de muestra, periodo, método, ubicación ni definición precisa de “desperdicio”. Por ello:

- No usar esos rangos como límite automático, meta comercial o ahorro esperado.
- Los porcentajes por uso no necesariamente comparten denominador; sumarlos podría exceder el consumo total.
- Las cifras de 5 % adicional y 32–68 % del gasto total por fugas parecen describir alcances diferentes y no son comparables sin fuente y definición.
- Usarlos solo como preguntas para entrevistas y para orientar qué áreas medir. Validar contra lecturas del hotel y fuentes técnicas primarias antes de publicarlos como hechos.

## Alcance funcional del SIEM hídrico

El sistema reúne señales de medidores y registros operativos para detectar desviaciones. No reemplaza un medidor fiscal, una inspección, análisis de laboratorio ni juicio técnico.

**Fuentes iniciales:** medidor general, submedidores de habitaciones o bloques, lavandería, cisterna y bombas; ocupación agregada; órdenes de mantenimiento; horarios de riego y operación. Solo se ingieren fuentes autorizadas. Para la demo se usan eventos sintéticos.

**Campos normalizados mínimos:** `event_id`, `timestamp_utc`, `hotel_id`, `meter_id`, `zone`, `volume_l` o `flow_l_min`, `interval_seconds`, `occupancy` agregado cuando aplique, `source`, `quality_flag`, `activity_context`, `config_version`. Mantener unidades, zona horaria y granularidad explícitas. No incluir nombres ni identificadores de huéspedes.

**Detecciones candidatas:** flujo sostenido en horario de baja actividad; aumento abrupto contra el patrón del mismo medidor y hora; diferencia entre medidor general y submedidores, descontando tolerancias y zonas sin instrumentar; consumo por habitación ocupada o por kg de ropa fuera de su línea base; lectura congelada, imposible o perdida; anomalía de bomba correlacionada con caudal o nivel de cisterna.

Los umbrales se calibran por hotel, medidor, zona, calidad de señal y periodo estacional. Las cifras del PDF no se codifican como umbrales. Primero se ejecuta en modo observación para medir falsos positivos.

## Flujo de triage

1. **Nueva señal:** detectar y deduplicar lecturas; comprobar calidad y estado del medidor.
2. **Prioridad:** ordenar por persistencia, volumen observado, zona, confianza de medición y actividad declarada. Prioridad significa orden de revisión, no diagnóstico.
3. **Contexto:** enlazar ocupación agregada, riego, lavandería, bombeo, mantenimiento y cambios autorizados de configuración.
4. **Asignación:** enviar a responsable humano con un SLA operativo que el hotel configure.
5. **Investigación:** registrar observaciones, evidencia, causa confirmada o desconocida y acción realizada.
6. **Verificación y cierre:** volver a observar el medidor bajo condiciones comparables; documentar lectura previa/posterior, periodo y limitaciones.

Estados recomendados: `new`, `acknowledged`, `investigating`, `resolved`, `false_positive`, `monitoring`. Cada cambio guarda actor, hora, nota y transición. Cerrar requiere evidencia; si no se encontró causa, se registra como desconocida y no se atribuye ahorro.

**Prioridades preliminares a validar:** P1 para flujo persistente o desbordamiento con lectura confiable y sin operación declarada; P2 para desviación sostenida de intensidad o desbalance de medidores; P3 para anomalía aislada o calidad insuficiente. El protocolo de emergencias y el umbral real los determina el hotel, no el SIEM.

## Seguridad y límites

La demo actual escucha solo en `127.0.0.1`, usa eventos sintéticos, token temporal para modificar triage y bitácora SQLite local. No cuenta con identidades multiusuario, RBAC real, TLS, gestión central de secretos ni respaldo inmutable. Esos controles no deben presentarse como funciones ya implementadas.

Antes de integrar infraestructura hotelera: validar autorización por escrito y análisis de riesgos; red segmentada; credenciales únicas por dispositivo y mínimo privilegio; autenticación y cifrado de transporte; validación de esquema y protección contra repetición; almacenamiento y retención definidos; RBAC integrado con identidad corporativa; auditoría protegida, respaldo y recuperación; gestión de vulnerabilidades; monitoreo del propio colector. Mantener el sistema de agua en solo lectura. No enviar comandos a PLC, bombas o válvulas desde este prototipo.

## Cómo demostrar ahorro sin inventar cifras

Definir un perímetro y periodo; registrar agua de entrada, ocupación y actividades pertinentes; validar medidores y huecos; calcular una línea base representativa; documentar la reparación; medir después en condiciones comparables; informar resultado, método, incertidumbre y datos faltantes.

`reducción estimada = consumo esperado ajustado - consumo observado`

`reducción porcentual = reducción estimada / consumo esperado ajustado × 100`

Reportar ahorro solo cuando una medición lo respalde. Separar alerta detectada, incidencia confirmada, intervención ejecutada y reducción verificada. El ejemplo de 100 a 85 m³ es ilustrativo, no pronóstico.

## Marco normativo: referencias iniciales, aplicación por confirmar

- **NOM-003-SEMARNAT-1997:** aplica a calidad de agua residual tratada que se reúsa en servicios al público; no define por sí sola consumos eficientes ni límites de fugas. Estado listado como vigente por Secretaría de Economía al revisar este proyecto: [ficha oficial](https://platiica.economia.gob.mx/normalizacion/nom-003-semarnat-1997/).
- **NOM-245-SSA1-2010:** requisitos sanitarios y calidad de agua de albercas, cuando exista una instalación dentro de su ámbito. La ficha oficial la lista vigente: [Secretaría de Economía](https://platiica.economia.gob.mx/normalizacion/nom-245-ssa1-2010/).
- **NOM-001-SEMARNAT-2021 / NOM-002-SEMARNAT-1996:** revisar según receptor de descarga; la autoridad y condiciones del permiso dependen del caso.
- **ISO 46001 e ISO 50001:** marcos voluntarios para sistemas de gestión de eficiencia hídrica y energía; no son permisos ni certificación automática.
- **Ley General de Aguas / Ley de Aguas Nacionales:** el PDF recibido menciona una ley de 2025. El DOF publicó el 11 de diciembre de 2025 un decreto que expide la Ley General de Aguas y reforma la Ley de Aguas Nacionales; también incluye transitorios y plazos regulatorios. Consultar el texto vigente y reglas posteriores para el caso específico [DOF](https://www.dof.gob.mx/nota_detalle.php?codigo=5775799&fecha=11/12/2025).
- **Mérida:** confirmar licencia municipal, tratamiento/descarga, abastecimiento y permisos aplicables con las autoridades correspondientes. No todos los hoteles tienen el mismo arreglo de agua y descarga.

Este documento es una guía de diseño, no dictamen jurídico, sanitario ni certificación ISO. Consultar el texto oficial vigente y asesoría calificada antes de implantar controles de cumplimiento.

## Referencias

1. Archivo recibido por el usuario: `docs/referencias/estadisticas_agua_hoteles.pdf`; sin bibliografía identificable dentro del documento.
2. Diario Oficial de la Federación, decreto de Ley General de Aguas, 11-12-2025: https://www.dof.gob.mx/nota_detalle.php?codigo=5775799&fecha=11/12/2025
3. Secretaría de Economía, NOM-003-SEMARNAT-1997: https://platiica.economia.gob.mx/normalizacion/nom-003-semarnat-1997/
4. Secretaría de Economía, NOM-245-SSA1-2010: https://platiica.economia.gob.mx/normalizacion/nom-245-ssa1-2010/

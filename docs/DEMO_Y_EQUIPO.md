# Plan inmediato · 4 personas

Objetivo del MVP: demostrar que una lectura anómala puede revisarse junto con eventos OT del mismo sitio, de forma trazable y con cálculo local ligero.

| Persona | Entrega | Qué cuenta |
|---|---|---|
| 1 · Integración / contacto | Docker healthy, CSV autorizado, respaldo local | Problema y objetivo |
| 2 · Datos / IA | Filtros, métricas y comparación verificadas | Cómo detectamos y qué errores hay |
| 3 · Cyber | Revisión OT, ventana temporal y evidencia | Por qué revisar juntos no prueba un ataque |
| 4 · Producto / pitch | Presentación, tiempos y propuesta hídrica | Impacto, GreenAI, negocio y límites |

## Próximos 90 minutos (plan propuesto)

- 0–15: persona 1 levanta Docker; 2 verifica esquema; 3 busca casos OT del kit; 4 confirma tiempo del pitch y rúbrica con organización.
- 15–40: 1 y 2 comprueban API y pruebas; 3 prepara una ficha cyber; 4 arma siete diapositivas usando evidencia real de la demo.
- 40–60: congelar versión, probar inicio tras reinicio, guardar capturas localmente y preparar respaldo sin internet.
- 60–75: ensayo de 5 minutos y preguntas difíciles.
- 75–90: corregir solo bloqueos, comprobar Docker y ensayar transición entre cuatro voces.

## Guion de 5 minutos (ajustable al tiempo oficial)

1. Persona 1, 0:00–0:45: “AquaGuard convierte mediciones de agua y energía en alertas revisables. Añadimos contexto OT para priorizar investigación.”
2. Persona 2, 0:45–2:00: mostrar SIM-B, alerta, cocientes de sumas y comparación de reglas/modelo. Aclarar datos simulados y límites.
3. Persona 3, 2:00–3:15: mostrar Revisión cyber; mismo sitio, ±1 hora, IDs y horas. Si no hay coincidencia, explicar OT aislado sin inventar un ataque. Revisar autorización y sensor; no ejecutar acciones.
4. Persona 4, 3:15–4:30: procesamiento CPU local y medición de tiempos. Propuesta de circuito cerrado con aporte no potable como diseño pendiente de validar. Modelo de negocio propuesto: piloto de monitoreo y servicio por sitio, sin cifras comerciales inventadas.
5. Persona 1, 4:30–5:00: cerrar con demo reproducible, evidencias y siguientes pasos de validación.

## Siete diapositivas

Problema y objetivo → datos del kit → arquitectura Docker → caso operacional y OT → evaluación → GreenAI / balance hídrico → equipo, negocio y siguientes pasos.

Si Docker falla durante el pitch: usar capturas locales obtenidas de la misma versión, diciendo explícitamente que son resultados guardados. No afirmar que una demo grabada está corriendo en vivo.

Pendientes externos: tiempo del pitch, formato de entrega, pesos, evidencia requerida para bonus y permiso para alojar datos. Nada de esto se inventa a partir de la rúbrica fotografiada.

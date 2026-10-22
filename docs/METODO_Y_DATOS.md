# Datos, método y evaluación

## Dataset

Archivo: data/operaciones_simuladas.csv. Origen: kit CIFOX, datos íntegramente sintéticos. 504 filas y 14 campos; tres sitios, 168 horas por sitio. Del 12 de octubre de 2026 00:00 UTC al 18 de octubre 23:00 UTC. Semilla del generador original: 22102026.

Campos: timestamp, site_id, cooling_type, energy_it_kwh, energy_total_kwh, water_l, load_pct, outdoor_temp_c, inlet_temp_c, ot_event, split, scenario, simulated_anomaly, is_simulated.

Cada fila representa un intervalo horario que comienza en timestamp. La energía es kWh/intervalo, agua L/intervalo, carga porcentaje y temperaturas °C. water_l significa captación local simulada; no consumo neto ni huella hídrica completa.

Primeras 72 horas por sitio: referencia (216 filas). Siguientes 96: evaluación (288). Anomalías inyectadas: 8 de ineficiencia, 8 de agua y 5 de OT. Referencia no tiene anomalías inyectadas.

## Indicadores

PUE del periodo = suma(energy_total_kwh) / suma(energy_it_kwh).

Intensidad hídrica = suma(water_l) / suma(energy_it_kwh), en L/kWh IT.

Los datos vacíos producen cocientes null. Un total de agua cero con filas válidas sí es distinto de ausencia de datos. Los sitios sin registros se identifican como tales. Todos los filtros se aplican al mismo perímetro.

## Entradas de ambos detectores

1. PUE horario.
2. Intensidad hídrica horaria.
3. Temperatura de entrada.

Las reglas alertan si alguna supera 1.6, 1.5 L/kWh IT o 29 °C, respectivamente. Estos umbrales vienen del kit y no son estándares de seguridad.

Isolation Forest usa un bosque por sitio: 64 árboles, submuestra de 64 filas sin reemplazo (o menos si no hay 64), profundidad ceil(log2(n)), dimensión aleatoria entre las variables con variación y corte uniforme en su rango. Las hojas añaden longitud esperada c(n), calculada con números armónicos. La puntuación es 2^(-camino medio/c(n)); valores mayores indican mayor aislamiento. No es una probabilidad.

La semilla base es 22102026, más el índice de sitio. El umbral es el percentil empírico 95 de referencia, definido por el elemento ceil(0.95*n)-1 de los scores ordenados. Se alerta con score estrictamente mayor. Empates impiden garantizar exactamente 5 % de alertas. No se normaliza: los cortes aleatorios ya trabajan en el rango de cada variable.

No se usan etiquetas, escenarios, fechas, particiones ni eventos OT como entradas. El split solo decide qué filas ajustan y cuáles evalúan. Se comprueba que referencia sea anterior a evaluación. El modelo se ajusta una vez al arrancar; los filtros no reentrenan.

## Comparación y objetivos

Los dos métodos se evalúan en las mismas filas y con el mismo conjunto de variables. El objetivo numérico se obtiene de simulated_anomaly y de scenario en {ineficiencia, fuga_agua}. scenario se usa exclusivamente para definir el objetivo de evaluación y describir errores. Las cinco anomalías OT no son positivos del objetivo numérico: se reportan aparte. Si un método las marca por sus valores numéricos se consideran falsas alarmas numéricas según estas etiquetas sintéticas.

El panel operativo combina alertas numéricas del método elegido con eventos OT no normales. Por ello el total operativo no tiene por qué coincidir con TP+FP de la tabla: puede incluir referencia y eventos OT.

Con el CSV original, en evaluación: reglas TP=16, FP=0, FN=0, TN=272; bosque TP=16, FP=23, FN=0, TN=249. Un desempeño perfecto de reglas está favorecido por el diseño del dataset. El bosque no mejora esa línea base aquí. Se conservan sus falsos positivos para mostrar la limitación, sin ajustar sobre evaluación.

## Evidencia y revisión

Se muestran valor observado y mediana de las primeras 72 horas del sitio. La mediana es contexto, no una atribución del score ni causalidad. Las recomendaciones son comprobaciones humanas redactadas, no acciones automáticas.

## Tiempo de ejecución

Tres repeticiones después de una corrida de calentamiento por método. Se usan todas las filas de evaluación originales y las mismas variables precomputadas. Se excluyen carga de CSV, extracción de variables y ajuste. Se presentan mediana, mínimo, máximo y muestras. La carga de fondo y la resolución del reloj de CPU pueden producir ceros en corridas muy cortas.

El tiempo de entrenamiento inicial se informa aparte y no es una media de repeticiones. No se estiman kWh, CO2, RAM ni litros. No se extrapola de esta implementación Python a bibliotecas optimizadas.

## Próxima validación necesaria

Más datos, conjunto de calibración separado, eventos más diversos, evaluación temporal independiente, revisión de falsas alarmas con personas operadoras y medición física si se quiere hablar de energía. Cambiar solamente ruido o semilla del generador original no crea un examen independiente.

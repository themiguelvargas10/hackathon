# NÁCAR SIEM: enfoque vigente para jueces

El objetivo es supervisar ciberseguridad OT de sistemas de enfriamiento y relacionar anomalías operativas con agua, energía y costos. Los hoteles son un sector posible; no son el eje del alcance actual.

## Implementado en el módulo local
- Lectura del kit autorizado, validación y filtros por sitio y periodo.
- Reglas explicables y modelo Isolation Forest educativo por sitio.
- Correlación temporal de eventos OT y alertas numéricas: mismo sitio, ±1 hora inclusiva. Coincidencia no demuestra ataque.
- FastAPI, interfaz web y ejecución local en CPU; Docker con kit montado en solo lectura.

## Demostración pública
Portal y presentación estáticos con escenarios inventados independientes del kit. Calculadora ilustrativa de costo directo de agua y energía. No reproduce la ejecución del modelo local ni contiene el CSV confidencial.

## Costos y sustentabilidad
Costo directo = litros/1000 × tarifa de agua + kWh × tarifa eléctrica. Comparar periodos equivalentes por carga y condiciones. No incluye cargos por demanda, impuestos, tratamiento, mantenimiento ni indisponibilidad. No representa ahorro real.
Evaluar agua y energía simultáneamente. Reúso, circuito cerrado y condensado son propuestas futuras sujetas a viabilidad y calidad del agua; no se ha demostrado huella cero.

## Seguridad futura
Separación OT/IT, ingesta autenticada y de solo lectura, cifrado, permisos por rol, auditoría protegida y gestión de cambios. No hay control de válvulas ni certificación industrial. Normas, permisos y requisitos específicos requieren revisión antes de implementar; no se afirman beneficios fiscales ni certificaciones ISO.

## Verificación disponible
12 pruebas de datos/cálculos y 2 de correlación aprobadas en el módulo original. Sintaxis JavaScript de consola válida. Pruebas HTTP pendientes por bloqueo del entorno de dependencias. Docker y piloto industrial no verificados en esta revisión.

Los PDF y capturas hoteleras anteriores se conservan como antecedentes; no sustituyen este alcance vigente.

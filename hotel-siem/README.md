# NÁCAR SIEM - triage local

Prototipo de SIEM de agua. Solo eventos sintéticos. No se conecta a medidores reales ni controla válvulas, bombas o sistemas OT. La consola comparte la identidad visual editorial de la portada NÁCAR SIEM: crema cálido, azul tinta, cobalto y tipografía serif.

La interfaz usa Newsreader para encabezados y DM Sans para lectura operativa, con iconos SVG de trazo basados en Lucide para mantener una navegación clara y ligera. Las fuentes web tienen alternativas de sistema si no hay conexión.

La versión pública de GitHub Pages muestra la portada y una consola de demostración estática en `/console/`. En Pages, las acciones de triage y los eventos se guardan solo en el navegador actual y pueden reiniciarse desde ese navegador. Para la bitácora SQLite protegida por token, ejecuta el backend local con las instrucciones de abajo.

## Ejecutar en Windows de esta laptop

Abre `INICIAR_WINDOWS.cmd`. Al iniciar, la terminal muestra un token temporal para acciones del operador. Mantén esa terminal abierta. Abre http://127.0.0.1:8765 para ver la portada NÁCAR; elige **Explorar la consola** para abrir el triage y estimador de costo directo en http://127.0.0.1:8765/console.

El token se pide al registrar una revisión o simular evento y se conserva solo en la sesión de esa pestaña. La API solo escucha en localhost. Las acciones se guardan en SQLite en `demo.sqlite3`, con usuario local `operador_local`, evento, nota y hora. No uses el servidor de demostración con sensores reales.

Para otras máquinas: instala Python 3.12, `python -m pip install -r requirements.txt`, luego `python server.py`; abre el mismo URL. El backend conserva las notas en demo.sqlite3 al reiniciar. Elimina ese archivo si deseas reiniciar la demostración y su bitácora.

## Propuesta de valor

Para la empresa hotelera: priorizar revisiones de agua, dar seguimiento a incidencias y contar con evidencia para comparar consumo bajo condiciones de ocupación y actividad semejantes. No promete un porcentaje de ahorro hasta medir un piloto.

El estimador solicita litros de pérdida medidos y tarifa por m³ del recibo. Calcula únicamente costo directo de agua. La tarifa `$40 MXN/m³` y las estadísticas del PDF son supuestos ilustrativos, no costos actuales de JAPAY ni benchmarks verificados.

## Triage

1. **Nueva:** señal detectada, todavía sin confirmar.
2. **Recibida:** un operador se hace cargo.
3. **En revisión:** se comprueba sensor, ocupación, actividad y mantenimiento.
4. **Resuelta:** se anota evidencia de la causa y acción; se vuelve a medir.

La severidad simulada es una regla ilustrativa. Prioridad alta si hay flujo persistente fuera de horario y sin actividad declarada; media para desviación de intensidad o cambio de configuración por confirmar. El backend conserva auditoría. Un cambio de configuración o patrón no confirma ataque o fuga.

## Seguridad del prototipo

- Loopback `127.0.0.1`, cabeceras defensivas, sin CORS ni documentación API abierta.
- Token aleatorio por ejecución protege escritura; comparar credencial en tiempo constante.
- Validación de campos, notas requeridas, evidencia mínima al cerrar y consultas SQLite parametrizadas.
- No se guarda token en el almacenamiento persistente del navegador; vive en sessionStorage hasta cerrar la pestaña.
- Roles de producción no implementados: solo se simula un operador local. Antes de usar con personal real habría que integrar identidades, roles, rotación/revocación de credenciales, retención, cifrado y pruebas de seguridad.
- No añadir datos de huéspedes identificables. Registrar ocupación agregada y limitar accesos a datos operativos.

## Producción futura

Ingesta autenticada y cifrada desde medidores; validar identidad y secuencia de dispositivo, unidades, límites y marcas de tiempo; cola resiliente; almacenamiento de series temporales con retención definida; reglas versionadas por área; alertas con deduplicación; RBAC real; bitácora protegida; backups y monitoreo. No conectar controladores OT al prototipo. Cualquier integración real requiere autorización, revisión de ciberseguridad y diseño de seguridad funcional.


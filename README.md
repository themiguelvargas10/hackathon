# NÁCAR SIEM · AguaSegura AI

**Nombre de propuesta:** NÁCAR SIEM, Núcleo de Análisis, Correlación y Atención de Riesgos Hídricos. **Propuesta de valor:** ayudar a hoteles de Mérida a detectar consumos atípicos, priorizar inspecciones y comprobar correcciones con lecturas comparables y evidencia de triage. El estimador calcula costo directo del agua con la tarifa ingresada por el hotel; no predice ahorros antes de medir un piloto.

La demo hotelera local con backend está en [`hotel-siem/`](hotel-siem/). Usa datos sintéticos, no opera sensores ni controla instalaciones. Revisa [`docs/SIEM_HOTEL_AGUA.md`](docs/SIEM_HOTEL_AGUA.md) para alcance, triage, seguridad y revisión de las cifras recibidas. Incluye un estimador de costo directo que requiere litros medidos y tarifa del recibo. Los dos PDF recibidos están en `docs/referencias/`.

El tablero original AquaGuard del reto CIFOX queda como módulo de referencia para refrigeración simulada. Sus datos y métricas no representan un hotel y no deben presentarse como resultados hoteleros.

Ruta B: FastAPI + interfaz web local + reglas explicables e Isolation Forest educativo por sitio. Docker ejecuta todo en CPU; sin nube ni servicios externos durante el análisis. El kit se monta localmente en solo lectura.

## Levantar con Docker (Windows, macOS o Linux)

1. Instala e inicia Docker Desktop (en Windows, contenedores Linux). Espera a que el motor esté listo. En Linux puedes usar Docker Engine con Compose v2. Verifica en una terminal:

```sh
docker --version
docker compose version
```

2. Si es la primera vez, clona el repositorio privado con tu cuenta autorizada:

```sh
git clone https://github.com/themiguelvargas10/hackathon.git
cd hackathon
```

Si ya lo tienes, entra en `hackathon` y ejecuta `git pull --ff-only`. Si Git avisa de cambios locales, consérvalos antes de actualizar; no uses un reset destructivo. Si modificaste el CSV previamente, haz una copia fuera del repositorio antes de actualizar.

3. Extrae el kit autorizado y copia **operaciones_simuladas.csv** a la carpeta `data` del proyecto. Debe quedar `hackathon/data/operaciones_simuladas.csv`. No pegues el ZIP ni los Papers. El CSV tiene 14 columnas: timestamp, site_id, cooling_type, energy_it_kwh, energy_total_kwh, water_l, load_pct, outdoor_temp_c, inlet_temp_c, ot_event, split, scenario, simulated_anomaly, is_simulated. No lo subas al repositorio.

4. Desde la carpeta que contiene `compose.yaml`, ejecuta:

```sh
docker compose up --build -d
docker compose ps
docker compose logs --tail=50 aquaguard
```

La primera construcción necesita internet para obtener Python y dependencias. Espera el estado **healthy** (normalmente unos segundos después del arranque). Abre **http://127.0.0.1:8501**. La API responde en http://127.0.0.1:8501/api/health con `status: ok` y 504 filas para el kit original.

En PowerShell puedes comprobarla así:

```powershell
Invoke-RestMethod http://127.0.0.1:8501/api/health
```

También puedes usar `INICIAR_WINDOWS.cmd` o `sh INICIAR_MAC_LINUX.sh` después de preparar Docker y el CSV.

## Recorrido de la demo

1. Monitor: pulsa **Recorrer un caso** para revisar SIM-B y su consumo de agua.
2. Abre una alerta y explica valor observado, referencia y comprobación humana.
3. Restablece los filtros y abre **Revisión cyber**: muestra eventos OT, coincidencias a ±1 hora y señales sin coincidencia. Cada vínculo conserva sitio y hora. Cero coincidencias también es un resultado válido; no se modificó el kit para forzarlas.
4. Evaluación: compara reglas e Isolation Forest con las mismas entradas y filas de evaluación. OT se cuenta aparte.
5. Pulsa **Medir ahora**: compara tiempo de inferencia local; no lo presentes como medición de electricidad o agua ahorrada.

## Detener, reiniciar y actualizar

```sh
docker compose down
docker compose up -d
```

Después de cambiar el CSV: `docker compose restart aquaguard` (los modelos se recalculan al arrancar). Después de cambiar código: `docker compose up --build -d`.

Problemas frecuentes:
- Motor no disponible: abre Docker Desktop y espera a que termine de iniciar.
- CSV ausente o inválido: revisa `docker compose logs --tail=80 aquaguard`; confirma nombre, columnas y que no esté dentro de una subcarpeta adicional.
- Puerto ocupado: cambia únicamente `127.0.0.1:8501:8000` por `127.0.0.1:8502:8000` en `compose.yaml`, recrea y abre el puerto 8502.
- Error descargando paquetes: revisa la conexión y repite la construcción antes de la presentación.
- No aparece la actualización: reconstruye y recarga el navegador.
- Linux y permiso de lectura: el usuario 10001 del contenedor necesita leer la carpeta y CSV; concede solo la lectura necesaria, no permisos globales de escritura.

## Desarrollo sin Docker (alternativa)

Con Python 3.12 y el CSV local:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python server.py
```

Abre http://127.0.0.1:8501. Las pruebas usan el kit original local; no descargan datos. Consulta `docs/VERIFICACION.md` para distinguir pruebas realizadas de pendientes.

## Alcance y recursos

- **Data / CSV del kit:** entrada real de esta demo. Datos sintéticos, tres sitios y siete días. No utiliza datos productivos.
- **Kit Stack Tecnológico:** base pedagógica de indicadores, umbrales y separación referencia/evaluación; esta ruta B añade FastAPI, Docker y correlación cyber.
- **Papers:** apoyo para argumentar el problema y límites; no se ingieren como datos ni se afirma validación científica por incluirlos.
- **CIFOX y fotos de las reglas:** encuadran el reto. Solo kit y entornos simulados; un contacto por equipo. Datos confidenciales y uso exclusivo del hackathon.

Señal → alerta → evidencia → revisión humana. No controla refrigeración, no escanea redes ni certifica ataques, fugas o potabilidad. ±1 hora es una decisión de diseño, no una regla del organizador. La correlación respeta los filtros: puede perder un vecino que quede fuera del periodo seleccionado. El modelo no aprende de etiquetas ni de eventos OT.

El bonus de +5 a +15 % exige una propuesta viable de cero agua dulce potable; este software por sí solo no lo demuestra. Propuesta a validar: refrigeración en circuito cerrado con aporte no potable autorizado, midiendo reposición, calidad, energía y pérdidas. No se afirma que cierre el balance total.

No se deducen de las fotos pesos de evaluación, duración del pitch, formato de entrega, criterios de aceptación del bonus ni permiso para alojar el kit en GitHub. Confírmenlo con organización.

## Confidencialidad

La versión actual excluye el CSV y los informes con registros del repositorio y de la imagen. El repositorio anterior los incluyó; **permanecen en el historial**. El repositorio es privado, pero eso no sustituye autorización del organizador. Mantén los originales localmente. No se reescribió el historial ni se cambió la visibilidad. Las exportaciones también contienen datos del kit: úsalas solo dentro del evento.

## Equipo de cuatro

Lee `docs/DEMO_Y_EQUIPO.md`: reparto, preparación inmediata y guion de cinco minutos (duración propuesta, pendiente de confirmar).

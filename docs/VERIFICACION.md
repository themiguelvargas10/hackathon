# Verificación · actualización del 22 octubre 2026

18 pruebas aprobadas en Python 3.12 / Windows con FastAPI TestClient: cálculo ponderado, vacíos y filtros, CSV inválido, independencia de etiquetas y evaluación, modelo, benchmark, API y exportaciones, rechazo de origen ajeno, correlación temporal inclusive y separación entre sitios.

Las pruebas de correlación usan fixtures sintéticos mínimos, separados del CSV oficial. No se modificó el kit ni se inventaron coincidencias para la demo.

La configuración Docker se entrega, pero no se pudo construir ni ejecutar aquí porque Docker no está instalado en este entorno. El equipo debe confirmar `docker compose up --build -d`, estado healthy y el recorrido de demo en su equipo. No presentar Docker como validado hasta hacerlo.

Dependencias principales fijadas en requirements.txt; imagen base y dependencias transitivas no quedan congeladas por digest. No se certifica un despliegue productivo. La app es local y no incorpora autenticación multiusuario.

Starlette emite un aviso de futura retirada del adaptador httpx usado por TestClient; las pruebas actuales pasan. No afecta el servidor uvicorn.

Verificación adicional: servidor Uvicorn iniciado y panel revisado en navegador, incluyendo la sección cyber. Con reglas y semana completa: 5 eventos OT, 0 coincidencias conjuntas, 16 alertas numéricas sin OT cercano. JavaScript validado con Node.

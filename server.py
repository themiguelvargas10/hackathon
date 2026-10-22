"""AquaGuard: API FastAPI local sobre un kit montado de solo lectura."""
import argparse
import csv
import io
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from aquaguard.core import Project, ROOT, DATA
from aquaguard.cyber import correlate

def create_app(data_path=None):
    @asynccontextmanager
    async def lifespan(app):
        path = Path(data_path or os.environ.get('AQUAGUARD_DATA', str(DATA)))
        if not path.is_file():
            raise RuntimeError('Falta el CSV del kit: colócalo en data/operaciones_simuladas.csv. Ruta: '+str(path))
        app.state.project = Project(path)
        yield

    app = FastAPI(title='AquaGuard Cyber', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware('http')
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.get('/api/health')
    def health(request: Request):
        return dict(status='ok', simulated=True, rows=len(request.app.state.project.rows))

    @app.post('/api/benchmark')
    def benchmark(request: Request):
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'error':'Origen no permitido.'},status_code=403)
        return request.app.state.project.benchmark()

    @app.get('/{path:path}')
    def get(path: str, request: Request):
        static = {'':('index.html','text/html'), 'app.js':('app.js','text/javascript'),
                  'style.css':('style.css','text/css'), 'favicon.svg':('favicon.svg','image/svg+xml')}
        if path in static:
            name, kind = static[path]
            return Response((ROOT/'web'/name).read_bytes(), media_type=kind)
        if path not in ('api/dashboard','api/export.json','api/alerts.csv'):
            return JSONResponse({'error':'Ruta no encontrada.'},status_code=404)
        pairs = list(request.query_params.multi_items())
        if any(k not in {'site','start','end','split','method'} for k,v in pairs) or len(dict(pairs)) != len(pairs):
            return JSONResponse({'error':'Parámetros desconocidos o repetidos.'},status_code=400)
        try:
            report = request.app.state.project.dashboard(**dict(pairs))
        except ValueError as exc:
            return JSONResponse({'error':str(exc)},status_code=400)
        report['cyber'] = correlate(report['alerts'])
        if path.endswith('.csv'):
            buffer = io.StringIO(newline='')
            writer = csv.writer(buffer)
            writer.writerow(['DATOS SIMULADOS - AquaGuard - alertas, no diagnóstico'])
            writer.writerow(['sitio','inicio_utc','detector','motivos','litros','pue','litros_kwh_it','temperatura_entrada_c','evento_ot'])
            for a in report['alerts']:
                writer.writerow([a['site'],a['timestamp'],report['method'],'; '.join(a['reasons']),a['water_l'],a['pue'],a['water_intensity'],a['inlet_temp_c'],a['ot_alert']])
            return Response(('\ufeff'+buffer.getvalue()).encode('utf-8'),media_type='text/csv',
                            headers={'Content-Disposition':'attachment; filename="aquaguard-alertas.csv"'})
        return JSONResponse(report, headers={'Content-Disposition':'attachment; filename="aquaguard-informe.json"'} if path.endswith('.json') else {})
    return app

app = create_app()

if __name__ == '__main__':
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8501)
    parser.add_argument('--no-browser',action='store_true',help='Compatibilidad; el navegador se abre manualmente.')
    args = parser.parse_args()
    uvicorn.run(app,host='127.0.0.1',port=args.port)

"""Servidor local de solo lectura. Ejecutar: python server.py"""
import argparse
import csv
import io
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from aquaguard.core import Project, ROOT


def make_handler(project):
    class Handler(BaseHTTPRequestHandler):
        def send(self, body, kind='application/json; charset=utf-8', status=200, filename=None):
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            if filename:
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, payload, status=200):
            self.send(json.dumps(payload, ensure_ascii=False, allow_nan=False), status=status)

        def do_GET(self):
            u = urlparse(self.path)
            static = {'/': ('index.html', 'text/html; charset=utf-8'),
                      '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                      '/style.css': ('style.css', 'text/css; charset=utf-8'),
                      '/favicon.svg': ('favicon.svg', 'image/svg+xml')}
            try:
                if u.path in static:
                    name, kind = static[u.path]
                    return self.send((ROOT/'web'/name).read_bytes(), kind)
                if u.path == '/api/health':
                    return self.send_json({'status': 'ok', 'simulated': True, 'rows':len(project.rows)})
                if u.path not in ('/api/dashboard','/api/export.json','/api/alerts.csv'):
                    return self.send_json({'error':'Ruta no encontrada.'},404)
                query = parse_qs(u.query, keep_blank_values=True)
                allowed = {'site','start','end','split','method'}
                if set(query)-allowed or any(len(v)!=1 for v in query.values()):
                    raise ValueError('Parámetros desconocidos o repetidos.')
                params = {k:v[0] for k,v in query.items()}
                report = project.dashboard(**params)
                if u.path.endswith('.csv'):
                    buffer = io.StringIO(newline='')
                    writer = csv.writer(buffer)
                    writer.writerow(['DATOS SIMULADOS - AquaGuard - alertas, no diagnóstico'])
                    writer.writerow(['sitio','inicio_utc','detector','motivos','litros','pue','litros_kwh_it','temperatura_entrada_c','evento_ot'])
                    for a in report['alerts']:
                        writer.writerow([a['site'],a['timestamp'],report['method'],'; '.join(a['reasons']),a['water_l'],a['pue'],a['water_intensity'],a['inlet_temp_c'],a['ot_alert']])
                    return self.send(('\ufeff'+buffer.getvalue()).encode('utf-8'),'text/csv; charset=utf-8',filename='aquaguard-alertas.csv')
                return self.send(json.dumps(report,ensure_ascii=False,allow_nan=False),
                                 filename='aquaguard-informe.json' if u.path.endswith('.json') else None)
            except ValueError as exc:
                return self.send_json({'error':str(exc)},400)
            except Exception:
                self.log_error('Error interno procesando la petición')
                return self.send_json({'error':'No se pudo completar la petición. Revisa la terminal.'},500)

        def do_POST(self):
            # Solo se acepta esta operación de cálculo desde el propio origen local.
            origin = self.headers.get('Origin')
            expected = 'http://127.0.0.1:' + str(self.server.server_port)
            if self.path != '/api/benchmark':
                return self.send_json({'error':'Método no permitido.'},405)
            if origin and origin != expected:
                return self.send_json({'error':'Origen no permitido.'},403)
            return self.send_json(project.benchmark())

    return Handler


def main():
    parser = argparse.ArgumentParser(description='AquaGuard - demo local con datos simulados')
    parser.add_argument('--port', type=int, default=8501)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    try:
        project = Project()
        server = ThreadingHTTPServer(('127.0.0.1',args.port), make_handler(project))
    except (ValueError,OSError) as exc:
        parser.exit(1,f'No se pudo iniciar AquaGuard: {exc}\nPrueba otro puerto con --port 8502.\n')
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'AquaGuard listo: {url}\nDATOS SIMULADOS | Ctrl+C para detener.',flush=True)
    if not args.no_browser:
        threading.Timer(.5,lambda:webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nAquaGuard detenido.')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()

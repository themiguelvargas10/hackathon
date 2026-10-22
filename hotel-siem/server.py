"""Backend local de la demo AquaGuard Hotel. Usa únicamente eventos sintéticos."""
from datetime import datetime, timezone
from pathlib import Path
import os
import secrets
import sqlite3

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('AQUAGUARD_HOTEL_DB', str(ROOT / 'demo.sqlite3')))
TOKEN = os.environ.get('AQUAGUARD_TRIAGE_TOKEN', '')

def db():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    return con

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def init():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS alerts (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, zone TEXT NOT NULL, timestamp TEXT NOT NULL,
          severity TEXT NOT NULL, signal TEXT NOT NULL, evidence TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'new', owner TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL)''')
        con.execute('''CREATE TABLE IF NOT EXISTS audit (
          seq INTEGER PRIMARY KEY AUTOINCREMENT, alert_id TEXT NOT NULL, action TEXT NOT NULL,
          actor TEXT NOT NULL, note TEXT NOT NULL, at TEXT NOT NULL)''')
        if con.execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == 0:
            ts=now()
            seed=[('AG-104','Flujo nocturno en cisterna','Cisterna','alta','water_flow',
                   '38 L/min durante 18 min; ocupación 42 %; no aparece riego programado.'),
                  ('AG-105','Lavandería sobre su patrón','Lavandería','media','water_intensity',
                   '14.2 L/kg frente a una referencia simulada de 10.8 L/kg.'),
                  ('AG-106','Cambio de configuración de bomba','Cisterna','media','config_change',
                   'Cambio simulado detectado; confirmar autorización y bitácora de mantenimiento.')]
            for id,title,zone,sev,signal,evidence in seed:
                con.execute('INSERT INTO alerts VALUES (?,?,?,?,?,?,?,\'new\',\'\',?)',
                            (id,title,zone,ts,sev,signal,evidence,ts))
            con.execute('INSERT INTO audit(alert_id,action,actor,note,at) VALUES(?,?,?,?,?)',
                        ('SYSTEM','demo_seed','sistema','Carga de eventos sintéticos para demostración.',ts))

class Triage(BaseModel):
    status: str
    note: str = Field(min_length=8,max_length=500)
    owner: str = Field(default='Mantenimiento',min_length=2,max_length=60)

class Estimate(BaseModel):
    loss_liters_per_day: float = Field(ge=0,le=10000000)
    tariff_mxn_per_m3: float = Field(gt=0,le=1000000)
    days: int = Field(default=30,ge=1,le=366)

app=FastAPI(title='AquaGuard Hotel local',docs_url=None,redoc_url=None,openapi_url=None)

@app.on_event('startup')
def startup():
    init()

@app.middleware('http')
async def security_headers(req,call_next):
    host=req.url.hostname
    if host not in ('127.0.0.1','localhost','testserver'):
        return __import__('fastapi').responses.JSONResponse({'detail':'Solo disponible en localhost.'},status_code=403)
    res=await call_next(req)
    res.headers['Cache-Control']='no-store'
    res.headers['X-Content-Type-Options']='nosniff'
    res.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    res.headers['Referrer-Policy']='no-referrer'
    return res

def operator(x_demo_token):
    if not TOKEN or not secrets.compare_digest(x_demo_token or '',TOKEN):
        raise HTTPException(401,'Acción protegida: ingresa el token de operador mostrado al iniciar la demo.')

@app.get('/')
def home(): return FileResponse(ROOT/'landing.html')

@app.get('/console')
def console(): return FileResponse(ROOT/'index.html')

@app.get('/api/dashboard')
def dashboard():
    with db() as con:
        alerts=[dict(r) for r in con.execute('SELECT * FROM alerts ORDER BY CASE severity WHEN \'alta\' THEN 0 WHEN \'media\' THEN 1 ELSE 2 END, timestamp DESC')]
        audits=[dict(r) for r in con.execute('SELECT * FROM audit ORDER BY seq DESC LIMIT 12')]
    return {'simulated':True,'alerts':alerts,'audit':audits,'triage':{'new':sum(a['status']=='new' for a in alerts),'investigating':sum(a['status']=='investigating' for a in alerts),'resolved':sum(a['status']=='resolved' for a in alerts)}}

@app.post('/api/estimate')
def estimate(payload:Estimate):
    """Estimate only metered direct water cost; excludes unprovided charges."""
    volume_m3=payload.loss_liters_per_day*payload.days/1000
    return {'simulated':True,'period_days':payload.days,
            'loss_liters_per_day':payload.loss_liters_per_day,
            'estimated_loss_m3':round(volume_m3,4),
            'tariff_mxn_per_m3':payload.tariff_mxn_per_m3,
            'direct_water_cost_mxn':round(volume_m3*payload.tariff_mxn_per_m3,2),
            'scope':'Estimación del costo directo del volumen indicado. Tarifa y pérdida deben validarse con medidor y recibo; no incluye saneamiento, energía, químicos ni reparación.'}

@app.post('/api/alerts/{alert_id}/triage')
def triage(alert_id:str, payload:Triage, x_demo_token:str|None=Header(default=None)):
    operator(x_demo_token)
    if payload.status not in {'acknowledged','investigating','resolved'}:
        raise HTTPException(422,'Estado no permitido.')
    if payload.status=='resolved' and len(payload.note.strip())<20:
        raise HTTPException(422,'Para cerrar el caso, registra evidencia de la revisión (20 caracteres mínimo).')
    with db() as con:
        if not con.execute('SELECT 1 FROM alerts WHERE id=?',(alert_id,)).fetchone():
            raise HTTPException(404,'Alerta no encontrada.')
        at=now()
        con.execute('UPDATE alerts SET status=?,owner=?,updated_at=? WHERE id=?',
                    (payload.status,payload.owner.strip(),at,alert_id))
        con.execute('INSERT INTO audit(alert_id,action,actor,note,at) VALUES(?,?,?,?,?)',
                    (alert_id,payload.status,'operador_local',payload.note.strip(),at))
    return {'ok':True,'alert_id':alert_id,'status':payload.status,'updated_at':at}

@app.post('/api/alerts/simulate')
def simulate(x_demo_token:str|None=Header(default=None)):
    operator(x_demo_token)
    id='AG-'+now().replace(':','').replace('-','')[-6:]
    at=now()
    with db() as con:
        con.execute('INSERT INTO alerts VALUES (?,?,?,?,?,?,?,\'new\',\'\',?)',
                    (id,'Pico simulado de flujo','Habitaciones',at,'media','water_spike',
                     'Lectura sintética 24 % sobre el patrón de esta hora; validar ocupación y medidor.',at))
        con.execute('INSERT INTO audit(alert_id,action,actor,note,at) VALUES(?,?,?,?,?)',
                    (id,'simulate','operador_local','Evento sintético agregado desde el panel.',at))
    return {'ok':True,'id':id}

if __name__=='__main__':
    import uvicorn
    import secrets as sec
    if not TOKEN:
        os.environ['AQUAGUARD_TRIAGE_TOKEN']=sec.token_urlsafe(18)
        TOKEN=os.environ['AQUAGUARD_TRIAGE_TOKEN']
        print('Token temporal de operador (guárdalo para esta sesión): '+TOKEN,flush=True)
    uvicorn.run(app,host='127.0.0.1',port=8765,proxy_headers=False)


"""Cálculos, validación y detección sin dependencias externas.

Las fórmulas y umbrales base proceden del kit CIFOX (ver LICENSE).
Isolation Forest es una implementación educativa propia, no scikit-learn.
"""
import csv
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from time import perf_counter, process_time

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'operaciones_simuladas.csv'
NUMERIC = ['energy_it_kwh', 'energy_total_kwh', 'water_l', 'load_pct',
           'outdoor_temp_c', 'inlet_temp_c']
REQUIRED = ['timestamp', 'site_id', 'cooling_type', *NUMERIC, 'ot_event',
            'split', 'scenario', 'simulated_anomaly', 'is_simulated']
SITES = {'SIM-A': 'aire', 'SIM-B': 'evaporativa', 'SIM-C': 'liquida'}
FEATURES = ['PUE horario', 'Litros / kWh IT horario', 'Temperatura de entrada (°C)']
SEED = 22102026


def load_data(path=DATA):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not set(REQUIRED).issubset(reader.fieldnames or []):
            raise ValueError('Faltan columnas obligatorias en el CSV.')
        rows = list(reader)
    if not rows:
        raise ValueError('El CSV está vacío.')
    seen = set()
    for line, r in enumerate(rows, 2):
        try:
            if any(r.get(k) in (None, '') for k in REQUIRED):
                raise ValueError('hay campos vacíos')
            if r['site_id'] not in SITES or r['cooling_type'] != SITES[r['site_id']]:
                raise ValueError('sitio o refrigeración no válido')
            if r['split'] not in ('referencia', 'evaluacion'):
                raise ValueError('partición no válida')
            if r['scenario'] not in ('base', 'ineficiencia', 'fuga_agua', 'evento_ot'):
                raise ValueError('escenario no válido')
            if r['ot_event'] not in ('normal', 'login_fallido', 'cambio_config_no_autorizado'):
                raise ValueError('evento no válido')
            if r['is_simulated'].lower() not in ('true', '1'):
                raise ValueError('solo se admiten datos declarados simulados')
            r['is_simulated'] = True
            if r['simulated_anomaly'] not in ('0', '1'):
                raise ValueError('etiqueta no válida')
            r['simulated_anomaly'] = int(r['simulated_anomaly'])
            dt = datetime.fromisoformat(r['timestamp'])
            if dt.utcoffset() is None or dt.utcoffset().total_seconds() != 0:
                raise ValueError('timestamp debe estar en UTC')
            if dt.minute or dt.second or dt.microsecond:
                raise ValueError('se requieren intervalos horarios')
            r['timestamp'] = dt.isoformat()
            key = (r['site_id'], r['timestamp'])
            if key in seen:
                raise ValueError('intervalo duplicado')
            seen.add(key)
            for k in NUMERIC:
                r[k] = float(r[k])
                if not math.isfinite(r[k]):
                    raise ValueError('valor numérico no finito')
            if r['energy_it_kwh'] <= 0 or r['energy_total_kwh'] < r['energy_it_kwh'] or r['water_l'] < 0:
                raise ValueError('energía o agua fuera de rango')
            if not 0 <= r['load_pct'] <= 100:
                raise ValueError('carga fuera de rango')
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f'Fila {line}: {exc}') from exc
    rows.sort(key=lambda r: (r['timestamp'], r['site_id']))
    for site in SITES:
        ref = [r['timestamp'] for r in rows if r['site_id'] == site and r['split'] == 'referencia']
        ev = [r['timestamp'] for r in rows if r['site_id'] == site and r['split'] == 'evaluacion']
        if len(ref) < 8 or not ev or max(ref) >= min(ev):
            raise ValueError(f'{site}: referencia insuficiente o separación temporal inválida.')
    return rows


def features(r):
    # No entran scenario, simulated_anomaly, split, ot_event ni timestamp.
    return [r['energy_total_kwh'] / r['energy_it_kwh'],
            r['water_l'] / r['energy_it_kwh'], r['inlet_temp_c']]


def numeric_reasons(r):
    pue, water, inlet = features(r)
    return [text for test, text in [
        (pue > 1.6, 'PUE horario > 1.6'),
        (water > 1.5, 'Agua > 1.5 L/kWh IT'),
        (inlet > 29, 'Temperatura de entrada > 29 °C')] if test]


def metrics(rows):
    it = sum(r['energy_it_kwh'] for r in rows)
    total = sum(r['energy_total_kwh'] for r in rows)
    water = sum(r['water_l'] for r in rows)
    return dict(rows=len(rows), energy_it_kwh=it, energy_total_kwh=total, water_l=water,
                pue=total / it if it else None, water_intensity=water / it if it else None)


def c_path(n):
    return 0.0 if n <= 1 else 2 * sum(1 / k for k in range(1, n)) - 2 * (n - 1) / n


class IsolationForest:
    """Árboles de aislamiento, puntuación original 2^(-E[h]/c(n)).

    Umbral: percentil 95 de referencia. Hiperparámetros fijos, sin etiquetas.
    No garantiza exactamente 5 % de alertas, por empates y muestra pequeña.
    """
    def __init__(self, trees=64, sample_size=64, seed=SEED):
        self.n_trees, self.sample_size, self.seed = trees, sample_size, seed

    def fit(self, xs):
        if len(xs) < 8:
            raise ValueError('Se necesitan al menos 8 muestras de referencia.')
        rng = random.Random(self.seed)
        self.n = min(self.sample_size, len(xs))
        max_depth = math.ceil(math.log2(self.n))

        def tree(points, depth):
            if depth >= max_depth or len(points) <= 1:
                return len(points)
            ranges = [(min(p[j] for p in points), max(p[j] for p in points)) for j in range(len(points[0]))]
            axes = [j for j, (a, b) in enumerate(ranges) if b > a]
            if not axes:
                return len(points)
            j = rng.choice(axes)
            a, b = ranges[j]
            cut = a + (b - a) * rng.random()
            left = [p for p in points if p[j] <= cut]
            right = [p for p in points if p[j] > cut]
            if not left or not right:
                return len(points)
            return (j, cut, tree(left, depth + 1), tree(right, depth + 1))

        self.trees = [tree(rng.sample(xs, self.n), 0) for _ in range(self.n_trees)]
        scores = sorted(self.score(x) for x in xs)
        self.threshold = scores[math.ceil(.95 * len(scores)) - 1]
        return self

    def score(self, x):
        def path(node, depth=0):
            if isinstance(node, int):
                return depth + c_path(node)
            axis, cut, left, right = node
            return path(left if x[axis] <= cut else right, depth + 1)
        return 2 ** (-(sum(path(t) for t in self.trees) / self.n_trees) / c_path(self.n))


def scores(actual, predicted):
    pairs = list(zip(actual, predicted))
    tp = sum(a and b for a, b in pairs)
    fp = sum(not a and b for a, b in pairs)
    fn = sum(a and not b for a, b in pairs)
    tn = sum(not a and not b for a, b in pairs)
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, n=len(pairs),
                precision=tp/(tp+fp) if tp+fp else None,
                recall=tp/(tp+fn) if tp+fn else None,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)


def filter_rows(rows, site='all', start='', end='', split='all'):
    if site not in ('all', *SITES) or split not in ('all', 'referencia', 'evaluacion'):
        raise ValueError('Filtro de sitio o partición inválido.')
    for day in (start, end):
        if day:
            if len(day) != 10 or datetime.strptime(day, '%Y-%m-%d').strftime('%Y-%m-%d') != day:
                raise ValueError('Usa fechas AAAA-MM-DD.')
    if start and end and start > end:
        raise ValueError('La fecha inicial debe ser anterior o igual a la final.')
    return [r for r in rows if (site == 'all' or r['site_id'] == site)
            and (split == 'all' or r['split'] == split)
            and (not start or r['timestamp'][:10] >= start)
            and (not end or r['timestamp'][:10] <= end)]


class Project:
    def __init__(self, path=DATA):
        self.rows = load_data(path)
        self.models, self.reference = {}, {}
        start = perf_counter()
        for i, site in enumerate(SITES):
            xs = [features(r) for r in self.rows if r['site_id'] == site and r['split'] == 'referencia']
            self.models[site] = IsolationForest(seed=SEED+i).fit(xs)
            self.reference[site] = [median(x[j] for x in xs) for j in range(3)]
        self.training_seconds = perf_counter() - start
        for r in self.rows:
            m = self.models[r['site_id']]
            r['forest_score'] = m.score(features(r))
            r['forest_threshold'] = m.threshold
            r['forest_alert'] = r['forest_score'] > m.threshold
            r['numeric_reasons'] = numeric_reasons(r)
            r['ot_alert'] = r['ot_event'] != 'normal'
            r['id'] = r['site_id'] + '|' + r['timestamp']

    def dashboard(self, method='rules', **filters):
        if method not in ('rules', 'forest'):
            raise ValueError('Detector inválido.')
        rows = filter_rows(self.rows, **filters)
        alerts = []
        for r in rows:
            numeric = bool(r['numeric_reasons']) if method == 'rules' else r['forest_alert']
            if not numeric and not r['ot_alert']:
                continue
            vals = features(r)
            reasons = r['numeric_reasons'][:] if method == 'rules' else (
                ['Patrón numérico inusual frente a la referencia del mismo sitio'] if numeric else [])
            checks = []
            if numeric:
                checks += ['Contrastar el registro con el sensor y con la carga del intervalo.',
                           'Revisar temperatura, mantenimiento y cambios operativos antes de concluir una causa.']
            if r['ot_alert']:
                reasons += ['Evento OT ficticio: ' + r['ot_event']]
                checks += ['Verificar el evento y su autorización con la persona responsable; no prueba un ataque.']
            alerts.append(dict(id=r['id'], timestamp=r['timestamp'], site=r['site_id'],
                reasons=reasons, checks=checks, pue=vals[0], water_intensity=vals[1],
                inlet_temp_c=vals[2], load_pct=r['load_pct'], outdoor_temp_c=r['outdoor_temp_c'],
                water_l=r['water_l'], energy_it_kwh=r['energy_it_kwh'],
                reference_medians=self.reference[r['site_id']], numeric_alert=numeric,
                ot_alert=r['ot_alert'], score=r['forest_score'], threshold=r['forest_threshold'],
                split=r['split']))
        groups = defaultdict(list)
        for r in rows:
            groups[r['timestamp']].append(r)
        alert_times = Counter(a['timestamp'] for a in alerts)
        timeline = [dict(timestamp=t, **metrics(rs), alerts=alert_times[t]) for t, rs in sorted(groups.items())]
        evaluation = [r for r in rows if r['split'] == 'evaluacion']
        # Etiquetas usadas SOLO para evaluación numérica: OT se reporta aparte.
        actual = [bool(r['simulated_anomaly']) and r['scenario'] in ('ineficiencia', 'fuga_agua') for r in evaluation]
        compare = {
            'rules': scores(actual, [bool(r['numeric_reasons']) for r in evaluation]),
            'forest': scores(actual, [r['forest_alert'] for r in evaluation]),
        }
        examples = []
        for r, truth in zip(evaluation, actual):
            pred = bool(r['numeric_reasons']) if method == 'rules' else r['forest_alert']
            if pred != truth:
                examples.append(dict(site=r['site_id'], timestamp=r['timestamp'],
                    result='Falso positivo' if pred else 'Falso negativo', scenario=r['scenario']))
        missing = []
        for site in SITES:
            ts = sorted(datetime.fromisoformat(r['timestamp']) for r in rows if r['site_id'] == site)
            gaps = sum(max(0, int((b-a).total_seconds()/3600)-1) for a,b in zip(ts,ts[1:]))
            if gaps:
                missing.append(dict(site=site, missing_intervals=gaps))
        return dict(simulated=True, method=method, filters=filters, metrics=metrics(rows),
            sites=[dict(site=s, cooling=SITES[s], **metrics([r for r in rows if r['site_id']==s]),
                        alerts=sum(a['site']==s for a in alerts)) for s in SITES],
            alerts=alerts, timeline=timeline, comparison=compare, errors=examples,
            numeric_positives=sum(actual), ot_events=sum(r['ot_alert'] for r in evaluation),
            quality=dict(missing_internal_intervals=missing, duplicates=0, invalid_values=0),
            metadata=dict(features=FEATURES, trees=64, sample_size=64, seed=SEED,
                threshold='Percentil 95 de referencia, por sitio',
                training_rows=sum(r['split']=='referencia' for r in self.rows),
                training_seconds=self.training_seconds,
                date_min=self.rows[0]['timestamp'][:10], date_max=self.rows[-1]['timestamp'][:10]))

    def benchmark(self):
        """Mismo conjunto; inferencia separada del entrenamiento; tres repeticiones."""
        rows = [r for r in self.rows if r['split'] == 'evaluacion']
        xs = [(r['site_id'], features(r)) for r in rows]
        def rules():
            return [x[0]>1.6 or x[1]>1.5 or x[2]>29 for _, x in xs]
        def forest():
            return [self.models[s].score(x)>self.models[s].threshold for s,x in xs]
        result = {}
        for name, fn in [('rules', rules), ('forest', forest)]:
            fn()  # calentamiento excluido
            wall, cpu = [], []
            for _ in range(3):
                t, c = perf_counter(), process_time()
                fn()
                cpu.append(process_time()-c);wall.append(perf_counter()-t)
            result[name] = dict(wall_seconds=wall, wall_median=median(wall),
                                wall_min=min(wall), wall_max=max(wall), cpu_seconds=cpu)
        import platform, sys
        return dict(results=result, rows=len(rows), repeats=3, python=sys.version.split()[0],
            platform=platform.platform(), training_seconds=self.training_seconds,
            scope=f'Inferencia en las {len(rows)} filas de evaluación del CSV cargado, sin filtros. Excluye CSV, entrenamiento y extracción de variables. Una corrida de calentamiento excluida.',
            limits='No mide energía, carbono, RAM ni agua. Corridas cortas y procesos de fondo afectan resultados.')

import copy
import csv
import json
import tempfile
import io
from types import SimpleNamespace
import unittest
from pathlib import Path
from http.client import HTTPResponse
from aquaguard.core import Project, DATA, REQUIRED, metrics, load_data, filter_rows, IsolationForest
from server import make_handler


class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = Project()

    def test_reference_matches_cifox_published_values(self):
        r = self.project.dashboard(split='referencia')
        self.assertEqual(r['metrics']['rows'], 216)
        self.assertAlmostEqual(r['metrics']['pue'], 1.2675626613531357)
        self.assertAlmostEqual(r['metrics']['water_intensity'], .36646215531320525)
        self.assertEqual(len(r['alerts']),0)

    def test_weighted_aggregation_not_mean_of_ratios(self):
        rows=[dict(energy_it_kwh=10,energy_total_kwh=20,water_l=5),
              dict(energy_it_kwh=90,energy_total_kwh=90,water_l=15)]
        m=metrics(rows)
        self.assertAlmostEqual(m['pue'],1.1)
        self.assertAlmostEqual(m['water_intensity'],.2)
        self.assertNotEqual(m['pue'],1.5)

    def test_empty_filters_produce_null_ratios(self):
        r=self.project.dashboard(start='2030-01-01')
        self.assertEqual(r['metrics']['rows'],0)
        self.assertIsNone(r['metrics']['pue'])
        self.assertIsNone(r['comparison']['forest']['precision'])
        self.assertEqual(r['alerts'],[])
        json.dumps(r,allow_nan=False)

    def test_site_and_day_filter_same_perimeter(self):
        r=self.project.dashboard(site='SIM-B',start='2026-10-16',end='2026-10-16')
        self.assertEqual(r['metrics']['rows'],24)
        self.assertEqual(len(r['timeline']),24)
        self.assertTrue(all(a['site']=='SIM-B' for a in r['alerts']))
        self.assertAlmostEqual(sum(t['water_l'] for t in r['timeline']),r['metrics']['water_l'])

    def test_evaluation_population_excludes_ot_from_numeric_target(self):
        r=self.project.dashboard()
        self.assertEqual(r['comparison']['rules']['n'],288)
        self.assertEqual(r['numeric_positives'],16)
        self.assertEqual(r['ot_events'],5)
        self.assertEqual(len(r['alerts']),21)
        self.assertEqual(r['comparison']['rules']['tp'],16)
        for score in r['comparison'].values():
            self.assertEqual(score['tp']+score['fp']+score['fn']+score['tn'],288)

    def test_invalid_filters(self):
        for args in [dict(site='unknown'),dict(split='training'),dict(method='x'),
                     dict(start='2026-10-20',end='2026-10-12'),dict(start='2026-02-30')]:
            with self.subTest(args=args),self.assertRaises(ValueError):
                self.project.dashboard(**args)

    def raw_rows(self):
        with DATA.open(encoding='utf8',newline='') as f:
            return list(csv.DictReader(f))

    def write_csv(self,folder,rows):
        path=Path(folder)/'sample.csv'
        with path.open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=REQUIRED);w.writeheader();w.writerows(rows)
        return path

    def test_invalid_csv_rejected(self):
        original=self.raw_rows()
        changes=[('energy_it_kwh','0'),('water_l','nan'),('load_pct','101'),
                 ('is_simulated','False'),('timestamp','2026-10-12T00:00:00'),
                 ('cooling_type','wrong'),('split','wrong')]
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            for k,v in changes:
                rows=copy.deepcopy(original);rows[0][k]=v
                with self.subTest(field=k),self.assertRaises(ValueError):
                    load_data(self.write_csv(tmp,rows))
            with self.assertRaises(ValueError):
                load_data(self.write_csv(tmp,original+[original[0]]))

    def test_labels_and_scenarios_cannot_change_predictions(self):
        rows=self.raw_rows()
        for r in rows:
            r['scenario']='base';r['simulated_anomaly']='0'
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            changed=Project(self.write_csv(tmp,rows))
        self.assertEqual([r['forest_score'] for r in changed.rows],
                         [r['forest_score'] for r in self.project.rows])

    def test_changing_evaluation_cannot_change_training_threshold(self):
        rows=self.raw_rows()
        for r in rows:
            if r['split']=='evaluacion':
                r['water_l']='999999'
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            changed=Project(self.write_csv(tmp,rows))
        for site,model in changed.models.items():
            self.assertEqual(model.threshold,self.project.models[site].threshold)

    def test_missing_hour_reported_not_filled(self):
        rows=self.raw_rows()
        rows=[r for r in rows if not(r['site_id']=='SIM-A' and r['timestamp'].startswith('2026-10-16T12:'))]
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            changed=Project(self.write_csv(tmp,rows)).dashboard()
        self.assertEqual(changed['metrics']['rows'],503)
        self.assertEqual(changed['quality']['missing_internal_intervals'],[{'site':'SIM-A','missing_intervals':1}])

    def test_isolation_scores_outlier_and_constant_reference(self):
        xs=[[i/64,(i%7)/10] for i in range(64)]
        model=IsolationForest().fit(xs)
        self.assertGreater(model.score([100,100]),model.score([.5,.3]))
        constant=IsolationForest().fit([[1,1]]*32)
        self.assertEqual(constant.score([1,1]),constant.threshold)

    def test_benchmark_reports_samples_not_energy(self):
        b=self.project.benchmark()
        self.assertEqual(b['rows'],288)
        for result in b['results'].values():
            self.assertEqual(len(result['wall_seconds']),3)
            self.assertGreaterEqual(result['wall_median'],0)
        self.assertNotIn('estimated_kwh',b)


class ApiTests(unittest.TestCase):
    """Ejercita el parser y la respuesta HTTP en memoria, sin requerir sockets."""
    @classmethod
    def setUpClass(cls):
        cls.handler = make_handler(Project())
        cls.handler.log_message = lambda *args: None

    def request(self, path, method='GET', origin=None):
        class Socket:
            def __init__(self, raw):
                self.input = io.BytesIO(raw)
                self.output = bytearray()
            def makefile(self, *args, **kwargs):
                return self.input
            def sendall(self, data):
                self.output.extend(data)
        headers = f'{method} {path} HTTP/1.0\r\nHost: 127.0.0.1:8501\r\nContent-Length: 0\r\n'
        if origin:
            headers += 'Origin: '+origin+'\r\n'
        sock = Socket((headers+'\r\n').encode('ascii'))
        self.handler(sock, ('127.0.0.1', 1234), SimpleNamespace(server_port=8501))
        response = HTTPResponse(Socket(bytes(sock.output)))
        response.begin()
        return response

    def test_dashboard_and_static_files(self):
        for path in ['/', '/app.js', '/style.css', '/favicon.svg', '/api/health']:
            with self.subTest(path=path):
                res = self.request(path)
                self.assertEqual(res.status, 200)
                self.assertGreater(len(res.read()), 10)
        res = self.request('/api/dashboard?site=SIM-B&split=evaluacion')
        self.assertEqual(json.loads(res.read())['metrics']['rows'], 96)
        self.assertIn("frame-ancestors 'none'", res.headers['Content-Security-Policy'])

    def test_invalid_requests_do_not_succeed(self):
        for path, status in [('/api/dashboard?site=x', 400), ('/api/dashboard?site=all&site=SIM-A', 400), ('/api/dashboard?extra=1', 400), ('/../server.py', 404)]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path).status, status)

    def test_exports_preserve_filters(self):
        res = self.request('/api/export.json?site=SIM-C')
        self.assertIn('attachment', res.headers['Content-Disposition'])
        self.assertEqual(json.loads(res.read())['metrics']['rows'], 168)
        text = self.request('/api/alerts.csv?site=SIM-B').read().decode('utf-8-sig')
        self.assertIn('DATOS SIMULADOS', text)
        self.assertIn('SIM-B', text)
        self.assertNotIn('SIM-A', text)

    def test_benchmark_rejects_foreign_origin(self):
        self.assertEqual(self.request('/api/benchmark', 'POST', 'http://example.com').status, 403)
        self.assertEqual(json.loads(self.request('/api/benchmark', 'POST').read())['repeats'], 3)
        self.assertEqual(self.request('/api/dashboard', 'POST').status, 405)


if __name__ == '__main__':
    unittest.main()

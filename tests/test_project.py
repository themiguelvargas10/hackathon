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
from server import create_app
from fastapi.testclient import TestClient
from aquaguard.cyber import correlate


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
    def setUp(self):
        self.client = TestClient(create_app(DATA))
        self.client.__enter__()
    def tearDown(self):
        self.client.__exit__(None,None,None)
    def test_dashboard_static_health(self):
        self.assertEqual(self.client.get('/api/health').json()['rows'],504)
        self.assertEqual(self.client.get('/').status_code,200)
        r=self.client.get('/api/dashboard?split=evaluacion')
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json()['cyber']['events']),5)
        self.assertIn("frame-ancestors 'none'",r.headers['content-security-policy'])
    def test_bad_filters_and_paths(self):
        for q in ['site=invalid','site=all&site=all','unknown=1','method=bad']:
            self.assertEqual(self.client.get('/api/dashboard?'+q).status_code,400)
        self.assertEqual(self.client.get('/data/operaciones_simuladas.csv').status_code,404)
        self.assertEqual(self.client.post('/api/dashboard').status_code,405)
    def test_exports(self):
        self.assertIn('cyber',self.client.get('/api/export.json').json())
        r=self.client.get('/api/alerts.csv')
        self.assertTrue(r.content.startswith(b'\xef\xbb\xbf'))
        self.assertIn('attachment',r.headers['content-disposition'])
    def test_benchmark_origin(self):
        self.assertEqual(self.client.post('/api/benchmark',headers={'Origin':'https://other.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/benchmark',headers={'Origin':'http://testserver'}).status_code,200)

class CyberTests(unittest.TestCase):
    def alert(self,hour,site='SIM-A',numeric=False,ot=False):
        ts=f'2026-10-15T{hour:02}:00:00+00:00'
        return dict(id=site+'|'+ts,site=site,timestamp=ts,numeric_alert=numeric,ot_alert=ot,reasons=[])
    def test_inclusive_window_and_site_isolation(self):
        rows=[self.alert(10,ot=True),self.alert(9,numeric=True),self.alert(11,numeric=True),self.alert(12,numeric=True),self.alert(10,'SIM-B',numeric=True)]
        c=correlate(rows)
        self.assertEqual(c['combined'],1)
        self.assertEqual(len(c['events'][0]['related_ids']),2)
        self.assertEqual(len(c['operational_only_ids']),2)
    def test_same_interval_and_no_coincidence(self):
        c=correlate([self.alert(10,numeric=True,ot=True),self.alert(14,ot=True)])
        self.assertEqual((c['combined'],c['ot_only']),(1,1))
        self.assertEqual(correlate([])['events'],[])

if __name__ == '__main__':
    unittest.main()

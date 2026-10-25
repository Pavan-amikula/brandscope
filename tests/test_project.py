import json
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analytics import campaign, segment
import server


class CommercialMath(unittest.TestCase):
    def test_matches_independent_treatment_control_ledger(self):
        # Baseline: 100 purchases * £50 * 40% = £2000 contribution.
        # Treatment: 140 purchases * (£50*.4 - £50*.1) - £200 = £1900.
        result=campaign(1000,.1,.04,50,.4,.1,200)
        self.assertAlmostEqual(result['contribution'],1900-2000)
        self.assertAlmostEqual(result['incremental_orders'],40)

    def test_zero_lift_still_pays_baseline_discounts(self):
        self.assertAlmostEqual(campaign(1000,.1,0,50,.4,.1,200)['contribution'],-700)

    def test_break_even_solves_profit_zero(self):
        r=campaign(2000,.05,.03,45,.45,.05,600)
        self.assertAlmostEqual(campaign(2000,.05,r['break_even_lift'],45,.45,.05,600)['contribution'],0)

    def test_unprofitable_margin_has_no_break_even(self):
        self.assertIsNone(campaign(1000,.1,.02,50,.1,.2,100)['break_even_lift'])

    def test_no_spend_roi_is_undefined(self):
        self.assertIsNone(campaign(1000,.1,.02,50,.4,0,0)['roi'])

    def test_invalid_inputs(self):
        for args in [(-1,.1,.1,50,.4,0,10),(100,.9,.2,50,.4,0,10),
                     (100,.1,.1,0,.4,0,10),(100,.1,.1,50,.4,1,10),
                     (100,.1,float('nan'),50,.4,0,10)]:
            with self.assertRaises(ValueError):campaign(*args)

    def test_segment_boundaries(self):
        self.assertEqual(segment(30,3,100,80),'Champions')
        self.assertEqual(segment(91,2,100,80),'At risk · high value')
        self.assertEqual(segment(90,2,100,80),'Loyal shoppers')
        self.assertEqual(segment(10,1,10,80),'New shoppers')


class DatasetAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads((ROOT/'web/data.json').read_text())

    def test_row_reconciliation(self):
        q=self.data['quality']
        self.assertEqual(q['raw_rows'],541909)
        self.assertEqual(q['raw_rows'],sum(q[x] for x in ['duplicates_removed','non_merchandise_or_invalid_removed','retained_rows']))
        self.assertEqual(q['positive_rows']+q['return_rows'],q['retained_rows'])

    def test_every_filter_financial_reconciliation(self):
        for windows in self.data['markets'].values():
            for d in windows.values():
                k=d['kpis']
                self.assertAlmostEqual(k['net_sales'],k['gross_sales']-k['returns'],places=6)
                self.assertAlmostEqual(sum(x['revenue'] for x in d['monthly']),k['gross_sales'],places=5)
                self.assertAlmostEqual(sum(x['revenue'] for x in d['segments']),k['identified_sales'],places=5)
                self.assertEqual(sum(x['customers'] for x in d['segments']),k['customers'])
                self.assertLessEqual(k['identified_sales'],k['gross_sales'])

    def test_sweden_is_small_observed_sample(self):
        k=self.data['markets']['Sweden']['full']['kpis']
        self.assertEqual(k['customers'],8)
        self.assertEqual(k['orders'],34)

    def test_holdout_probability_bounds_and_rank_sizes(self):
        for r in self.data['evaluation']:
            self.assertEqual(r['targeted'],int(r['eligible']*.2))
            self.assertLessEqual(r['rfm_precision'],1)
            self.assertGreater(r['overall_repurchase_rate'],0)
            self.assertEqual(r['horizon_days'],30)


class LiveAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.original=server.DB
        server.DB=Path(cls.tmp.name)/'events.sqlite';server.init_db()
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),partial(server.Handler,directory=str(ROOT/'web')))
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.http.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.thread.join();server.DB=cls.original;cls.tmp.cleanup()

    def request(self,path,obj=None,origin=None):
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        req=urllib.request.Request(self.base+path,data=json.dumps(obj).encode() if obj is not None else None,headers=headers)
        try:
            with urllib.request.urlopen(req) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)

    def test_health(self):self.assertEqual(self.request('/api/health')[1]['storage'],'SQLite')

    def test_idempotent_event_and_durable_storage(self):
        event=dict(event_id='unique-order-0001',market='Sweden',channel='CRM',amount_pence=4500,synthetic=True)
        self.assertEqual(self.request('/api/events',event)[0],201)
        self.assertEqual(self.request('/api/events',event)[0],200)
        payload=self.request('/api/events')[1]
        self.assertEqual(payload['totals']['events'],1)
        self.assertEqual(payload['totals']['amount_pence'],4500)
        with sqlite3.connect(server.DB) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)
        db.close()

    def test_bad_event_rejected(self):
        status,_=self.request('/api/events',dict(event_id='bad',amount_pence=-100))
        self.assertEqual(status,400)

    def test_cross_origin_write_rejected(self):
        self.assertEqual(self.request('/api/plans',{'title':'x'},'https://untrusted.example')[0],403)

    def test_campaign_api(self):
        status,r=self.request('/api/campaign',dict(audience=1000,baseline=.1,lift=.04,aov=50,margin=.4,discount=.1,cost=200))
        self.assertEqual(status,200);self.assertAlmostEqual(r['contribution'],-100)

    def test_saved_scenario(self):
        self.assertEqual(self.request('/api/plans',{'title':'Test brief','assumptions':True})[0],201)
        self.assertEqual(self.request('/api/plans')[1][0]['title'],'Test brief')

    def test_profile_prediction_api(self):
        model=json.loads((ROOT/'web/models/propensity.json').read_text())
        status,result=self.request('/api/predict',model['example'])
        self.assertEqual(status,200);self.assertGreaterEqual(result['probability'],0);self.assertLessEqual(result['probability'],1)

    def test_recommendation_api(self):
        model=json.loads((ROOT/'web/models/recommender.json').read_text())
        code=model['items'][0]['code'];status,result=self.request('/api/recommend',{'codes':[code]})
        self.assertEqual(status,200);self.assertEqual(len(result),5);self.assertNotIn(code,[p['code'] for p in result])

    def test_evidence_api(self):
        status,result=self.request('/api/ask',{'question':'How large is the Swedish sample?'})
        self.assertEqual(status,200);self.assertFalse(result['abstained'])

    def test_experiment_api(self):
        from experiments import parse_experiment_csv
        rows=parse_experiment_csv((ROOT/'web/models/synthetic-experiment.csv').read_text())
        status,result=self.request('/api/experiment',{'rows':rows})
        self.assertEqual(status,200);self.assertEqual(result['n'],8000);self.assertIn('Inconclusive',result['decision'])


if __name__=='__main__':unittest.main()

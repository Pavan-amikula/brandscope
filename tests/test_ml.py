"""Portable inference and data-contract tests; no ML library required at runtime."""
import copy
import csv
import io
import json
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ml_runtime import predict_profile,recommend,retrieve
from experiments import parse_experiment_csv,analyse_experiment


def artifact(name):return json.loads((ROOT/'web/models'/name).read_text(encoding='utf-8'))


class PortableModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=artifact('propensity.json');cls.reco=artifact('recommender.json');cls.knowledge=artifact('knowledge.json')

    def test_export_matches_sklearn_reference_cases(self):
        for case in artifact('parity_cases.json'):
            self.assertAlmostEqual(predict_profile(self.model,case['profile'])['probability'],case['probability'],places=7)

    def test_forest_path_contributions_reconcile(self):
        result=predict_profile(self.model,self.model['example'])
        baseline=sum(t['probability'][0] for t in self.model['model']['trees'])/len(self.model['model']['trees'])
        self.assertAlmostEqual(baseline+sum(x['contribution'] for x in result['explanation']),result['raw_probability'],places=10)

    def test_missing_profile_feature_is_rejected(self):
        p=dict(self.model['example']);p.pop('orders')
        with self.assertRaises(ValueError):predict_profile(self.model,p)

    def test_nonfinite_or_negative_feature_rejected(self):
        for v in [-1,float('nan'),float('inf'),'20']:
            p=dict(self.model['example']);p['orders']=v
            with self.assertRaises(ValueError):predict_profile(self.model,p)

    def test_inconsistent_purchase_history_rejected(self):
        p=dict(self.model['example']);p['orders_30d']=p['orders']+1
        with self.assertRaises(ValueError):predict_profile(self.model,p)

    def test_inconsistent_recency_or_spend_rejected(self):
        for changes in [dict(recency_days=100,orders_30d=1),dict(orders_30d=0,spend_30d=1)]:
            p={**self.model['example'],**changes}
            with self.assertRaises(ValueError):predict_profile(self.model,p)

    def test_fractional_purchase_count_rejected(self):
        p={**self.model['example'],'orders':2.5}
        with self.assertRaises(ValueError):predict_profile(self.model,p)

    def test_cold_start_profile_requires_a_separate_model(self):
        p={**self.model['example'],'orders':0,'orders_30d':0,'spend_30d':0,'gross_spend':0}
        with self.assertRaises(ValueError):predict_profile(self.model,p)

    def test_extrapolation_is_flagged(self):
        p=dict(self.model['example']);p['tenure_days']=100000
        self.assertTrue(predict_profile(self.model,p)['warnings'])

    def test_recommendation_excludes_seeds(self):
        seeds=[i['code'] for i in self.reco['items'][:2]]
        result=recommend(self.reco,seeds)
        self.assertEqual(len(result),5);self.assertFalse(set(r['code'] for r in result)&set(seeds))

    def test_repeated_seed_is_not_double_counted(self):
        code=self.reco['items'][0]['code']
        self.assertEqual(recommend(self.reco,[code]),recommend(self.reco,[code,code]))

    def test_unknown_product_rejected(self):
        with self.assertRaises(ValueError):recommend(self.reco,['NOT-A-PRODUCT'])

    def test_popularity_baseline_uses_purchase_invoice_counts(self):
        code=self.reco['items'][0]['code'];result=recommend(self.reco,[code],method='popularity')
        expected=sorted((p for p in self.reco['items'] if p['code']!=code),key=lambda p:(-p['orders'],p['code']))[:5]
        self.assertEqual([p['code'] for p in result],[p['code'] for p in expected])

    def test_unknown_evidence_question_abstains(self):
        self.assertTrue(retrieve(self.knowledge,'quasar nebula extragalactic')['abstained'])

    def test_swedish_question_retrieves_sample_boundary(self):
        result=retrieve(self.knowledge,'How large is the Swedish sample?')
        self.assertIn('Swedish',result['answer']);self.assertTrue(all(r['source'].startswith('https://github.com/Pavan-amikula/brandscope/') for r in result['matches']))

    def test_common_questions_return_relevant_project_evidence(self):
        result=retrieve(self.knowledge,'How do I analyse a randomized experiment?')
        self.assertFalse(result['abstained']);self.assertTrue(any('experiment' in r['id'] for r in result['matches']))
        model_result=retrieve(self.knowledge,'What did the machine learning model achieve?')
        self.assertEqual(model_result['matches'][0]['id'],'propensity')

    def test_final_month_never_used_for_model_selection(self):
        b=artifact('benchmark.json');self.assertLess(b['split']['validation'],b['split']['calibration']);self.assertLess(b['split']['calibration'],b['split']['test'])
        self.assertEqual(b['selected'],max(b['validation'],key=lambda r:(r['average_precision'],-r['brier']))['model'])


class ExperimentAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=parse_experiment_csv((ROOT/'web/models/synthetic-experiment.csv').read_text(encoding='utf-8'))

    def test_synthetic_example_keeps_inconclusive_profit_visible(self):
        r=analyse_experiment(self.rows)
        self.assertEqual(r['n'],8000);self.assertLess(r['contribution']['lower'],0);self.assertGreater(r['contribution']['upper'],0)
        self.assertGreater(r['conversion']['lower'],0);self.assertIn('Inconclusive',r['decision'])

    def test_duplicate_participant_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):analyse_experiment(self.rows+[self.rows[0]])

    def test_sample_ratio_imbalance_flagged(self):
        rows=[r for r in self.rows if r['arm']=='control']+[r for r in self.rows if r['arm']=='treatment'][:100]
        r=analyse_experiment(rows);self.assertLess(r['srm_p_value'],.01);self.assertIn('imbalance',r['decision'])

    def test_independent_difference_and_interval(self):
        rows=[]
        for arm,shift in [('control',0),('treatment',1)]:
            for i in range(40):rows.append(dict(participant_id=f'{arm}-{i}',arm=arm,converted=i%2,contribution=2*(i%2)+shift))
        r=analyse_experiment(rows)
        self.assertAlmostEqual(r['contribution']['difference'],1)
        self.assertAlmostEqual(r['contribution']['standard_error'],math.sqrt(2/39))

    def test_missing_columns_rejected(self):
        with self.assertRaisesRegex(ValueError,'Required'):parse_experiment_csv('user,arm\n1,control\n')

    def test_nonfinite_contribution_rejected(self):
        with self.assertRaises(ValueError):parse_experiment_csv('participant_id,arm,converted,contribution\na,control,1,NaN\n')

    def test_small_arms_rejected(self):
        with self.assertRaisesRegex(ValueError,'30'):analyse_experiment(self.rows[:20])

    def test_quoted_participant_id_supported(self):
        rows=parse_experiment_csv('participant_id,arm,converted,contribution\n"a,b",control,0,-0.1\n')
        self.assertEqual(rows[0]['participant_id'],'a,b')


if __name__=='__main__':unittest.main()

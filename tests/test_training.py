"""Feature-time contracts checked on a tiny fixture, without public raw data."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
HAS_ML=all(importlib.util.find_spec(m) for m in ['pandas','sklearn','scipy'])


@unittest.skipUnless(HAS_ML,'Optional model rebuild dependencies not installed')
class SnapshotContracts(unittest.TestCase):
    def setUp(self):
        import pandas as pd
        self.pd=pd
        self.df=pd.DataFrame([
            ['a','2010-12-10',1,'10000',1,1000],['b','2011-01-15',1,'10001',1,2000],
            ['c','2011-01-20',2,'10002',1,3000],['d','2011-02-02',1,'10003',1,4000],
            ['e','2011-03-05',999,'10004',1,1000]],columns=['InvoiceNo','InvoiceDate','CustomerID','StockCode','Quantity','pence'])
        self.df.InvoiceDate=pd.to_datetime(self.df.InvoiceDate)

    def test_future_transactions_cannot_change_features(self):
        from train_models import FEATURES,snapshot
        before=snapshot(self.df,'2011-02-01')
        modified=self.df.copy();modified.loc[modified.InvoiceDate>=self.pd.Timestamp('2011-02-01'),'pence']=99999999
        after=snapshot(modified,'2011-02-01')
        self.pd.testing.assert_frame_equal(before[FEATURES],after[FEATURES])

    def test_future_customer_is_not_eligible_before_first_purchase(self):
        from train_models import snapshot
        self.assertNotIn(999,snapshot(self.df,'2011-02-01').index)

    def test_label_window_is_subsequent_30_days(self):
        from train_models import snapshot
        x=snapshot(self.df,'2011-02-01');self.assertEqual(x.loc[1,'label'],1);self.assertEqual(x.loc[2,'label'],0)

    def test_incomplete_label_window_rejected(self):
        from train_models import snapshot
        with self.assertRaisesRegex(ValueError,'Incomplete'):snapshot(self.df,'2011-03-01')


if __name__=='__main__':unittest.main()

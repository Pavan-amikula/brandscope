"""Temporal repurchase benchmark and calibrated, portable inference artifacts.

Training: Mar–Aug monthly snapshots; selection: Sep; calibration: Oct;
final reporting: Nov. All labels use a subsequent 30-day purchase window.
"""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ml_runtime import predict_profile

FEATURES=['recency_days','orders','gross_spend','tenure_days','orders_30d','spend_30d','unique_products','average_order_value']
TRAIN_CUTS=['2011-03-01','2011-04-01','2011-05-01','2011-06-01','2011-07-01','2011-08-01']


def load_data():
    with closing(sqlite3.connect(ROOT/'data/retail.sqlite')) as db:
        df=pd.read_sql_query('SELECT InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country, pence FROM transactions',db)
    df['InvoiceDate']=pd.to_datetime(df.InvoiceDate)
    return df


def snapshot(df, cutoff, labelled=True):
    cut=pd.Timestamp(cutoff)
    history=df[(df.InvoiceDate<cut)&(df.Quantity>0)&df.CustomerID.notna()].copy()
    grouped=history.groupby('CustomerID')
    x=grouped.agg(last=('InvoiceDate','max'),first=('InvoiceDate','min'),orders=('InvoiceNo','nunique'),
        gross_spend=('pence','sum'),unique_products=('StockCode','nunique'))
    x['gross_spend']/=100
    x['recency_days']=(cut-x['last']).dt.days
    x['tenure_days']=(cut-x['first']).dt.days
    recent=history[history.InvoiceDate>=cut-pd.Timedelta(days=30)].groupby('CustomerID').agg(orders_30d=('InvoiceNo','nunique'),spend_30d=('pence','sum'))
    recent['spend_30d']/=100
    x=x.join(recent).fillna({'orders_30d':0,'spend_30d':0})
    x['average_order_value']=x.gross_spend/x.orders
    result=x[FEATURES].astype(float)
    if labelled:
        if df.InvoiceDate.max()<cut+pd.Timedelta(days=30):raise ValueError('Incomplete label window')
        future=set(df[(df.InvoiceDate>=cut)&(df.InvoiceDate<cut+pd.Timedelta(days=30))&(df.Quantity>0)].CustomerID.dropna())
        result['label']=[int(c in future) for c in result.index]
    result['cutoff']=cutoff
    return result


def rfm_scores(x):
    return (x.orders.rank(pct=True)+x.gross_spend.rank(pct=True)+(1-x.recency_days.rank(pct=True)))/3


def metric_set(y,score,probability=None):
    n=max(1,int(len(y)*.2));order=np.argsort(-np.asarray(score),kind='stable')[:n]
    rate=float(np.mean(y));precision=float(np.asarray(y)[order].mean())
    result=dict(n=len(y),positives=int(np.sum(y)),prevalence=rate,average_precision=float(average_precision_score(y,score)),
        roc_auc=float(roc_auc_score(y,score)),top20_n=n,precision_top20=precision,lift_top20=precision/rate,
        capture_top20=float(np.asarray(y)[order].sum()/np.sum(y)))
    if probability is not None:result.update(brier=float(brier_score_loss(y,probability)),log_loss=float(log_loss(y,probability)))
    return result


def export_model(name,model,scaler):
    if name=='Logistic regression':
        return dict(kind='logistic',mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),
                    coef=model.coef_[0].tolist(),intercept=float(model.intercept_[0]))
    trees=[]
    for estimator in model.estimators_:
        tree=estimator.tree_
        probability=(tree.value[:,0,1]/tree.value[:,0,:].sum(axis=1)).tolist()
        trees.append(dict(left=tree.children_left.tolist(),right=tree.children_right.tolist(),
            feature=tree.feature.tolist(),threshold=tree.threshold.tolist(),probability=probability))
    return dict(kind='forest',trees=trees)


def reliability(y,p):
    rows=[]
    for low in np.arange(0,1,.1):
        mask=(p>=low)&(p<low+.10000001)
        if mask.any():rows.append(dict(lower=round(float(low),1),n=int(mask.sum()),predicted=float(p[mask].mean()),observed=float(y[mask].mean())))
    return rows


def main():
    df=load_data();train=pd.concat([snapshot(df,c) for c in TRAIN_CUTS])
    validation=snapshot(df,'2011-09-01');calibration=snapshot(df,'2011-10-01');test=snapshot(df,'2011-11-01')
    X=np.log1p(train[FEATURES].to_numpy());scaler=StandardScaler().fit(X)
    candidates={
        'Logistic regression':LogisticRegression(C=1,max_iter=1000,random_state=42),
        'Random forest':RandomForestClassifier(n_estimators=120,max_depth=7,min_samples_leaf=30,max_features=.8,n_jobs=2,random_state=42)}
    validation_rows=[]
    for name,model in candidates.items():
        model.fit(scaler.transform(X) if name=='Logistic regression' else X,train.label)
        vx=np.log1p(validation[FEATURES].to_numpy())
        prediction=model.predict_proba(scaler.transform(vx) if name=='Logistic regression' else vx)[:,1]
        validation_rows.append(dict(model=name,**metric_set(validation.label,prediction,prediction)))
    selected=max(validation_rows,key=lambda row:(row['average_precision'],-row['brier']))['model']
    fitted=candidates[selected]
    def predict(frame):
        x=np.log1p(frame[FEATURES].to_numpy())
        return fitted.predict_proba(scaler.transform(x) if selected=='Logistic regression' else x)[:,1]
    raw_cal=predict(calibration);cal_x=np.log(np.clip(raw_cal,1e-9,1-1e-9)/np.clip(1-raw_cal,1e-9,1))[:,None]
    calibrator=LogisticRegression(C=1e6,max_iter=1000,random_state=42).fit(cal_x,calibration.label)
    raw_test=predict(test)
    probability=calibrator.predict_proba(np.log(np.clip(raw_test,1e-9,1-1e-9)/np.clip(1-raw_test,1e-9,1))[:,None])[:,1]
    final=[]
    for name,model in candidates.items():
        tx=np.log1p(test[FEATURES].to_numpy());p=model.predict_proba(scaler.transform(tx) if name=='Logistic regression' else tx)[:,1]
        final.append(dict(model=name+' (raw)',**metric_set(test.label,p,p)))
    final.append(dict(model=selected+' + October calibration',**metric_set(test.label,probability,probability)))
    final.append(dict(model='RFM rank',**metric_set(test.label,rfm_scores(test))))
    final.append(dict(model='Spend-only rank',**metric_set(test.label,test.gross_spend)))
    constant=np.repeat(float(train.label.mean()),len(test))
    final.append(dict(model='Training prevalence',**metric_set(test.label,constant,constant)))
    # Fixed-seed paired customer bootstrap for AP difference vs RFM. No model selection here.
    rng=np.random.default_rng(42);y=test.label.to_numpy();baseline=rfm_scores(test).to_numpy();diff=[]
    for _ in range(500):
        idx=rng.integers(0,len(y),len(y))
        diff.append(average_precision_score(y[idx],probability[idx])-average_precision_score(y[idx],baseline[idx]))
    ranges={f:dict(min=float(train[f].min()),max=float(train[f].max()),p05=float(train[f].quantile(.05)),p95=float(train[f].quantile(.95))) for f in FEATURES}
    artifact=dict(schema_version=1,version='repurchase-1.0',features=FEATURES,ranges=ranges,
        selected=selected,model=export_model(selected,fitted,scaler),
        calibrator=dict(coef=float(calibrator.coef_[0,0]),intercept=float(calibrator.intercept_[0])),
        example=dict(recency_days=15,orders=3,gross_spend=600,tenure_days=180,
                     orders_30d=1,spend_30d=200,unique_products=20,average_order_value=200))
    # Model portability and explanations are checked against actual sklearn scoring.
    cases=[]
    for idx in np.linspace(0,len(test)-1,12,dtype=int):
        profile=test.iloc[idx][FEATURES].to_dict();portable=predict_profile(artifact,profile)
        assert abs(portable['probability']-probability[idx])<1e-7
        cases.append(dict(profile=profile,probability=float(probability[idx])))
    importance=[]
    original=average_precision_score(y,raw_test)
    for f in FEATURES:
        changed=test.copy();changed[f]=rng.permutation(changed[f].to_numpy())
        importance.append(dict(feature=f,average_precision_drop=float(original-average_precision_score(y,predict(changed)))))
    # Coarse feature drift against the calibration population, not a production alarm guarantee.
    drift=[]
    for f in FEATURES:
        edges=np.unique(np.quantile(calibration[f],np.linspace(0,1,6)))
        if len(edges)<3:continue
        edges[0]=-np.inf;edges[-1]=np.inf
        expected=np.histogram(calibration[f],bins=edges)[0]/len(calibration)
        actual=np.histogram(test[f],bins=edges)[0]/len(test)
        e=np.clip(expected,.0001,None);a=np.clip(actual,.0001,None)
        drift.append(dict(feature=f,psi=float(np.sum((a-e)*np.log(a/e)))))
    capacity=[]
    ordering=np.argsort(-probability,kind='stable')
    for fraction in [.05,.1,.2,.3,.5,1]:
        n=max(1,int(fraction*len(test)));ids=ordering[:n]
        capacity.append(dict(fraction=fraction,n=n,expected_purchasers=float(probability[ids].sum()),
            observed_purchasers=int(y[ids].sum()),observed_precision=float(y[ids].mean())))
    report=dict(version=artifact['version'],source_sha256=json.loads((ROOT/'web/data.json').read_text())['quality']['sha256'],
        split=dict(train=TRAIN_CUTS,train_rows=len(train),validation='2011-09-01',calibration='2011-10-01',test='2011-11-01',test_end_exclusive='2011-12-01',horizon_days=30),
        selected=selected,selection_rule='Highest September average precision; Brier tie-break. October sigmoid calibration fixed before November reporting.',
        validation=validation_rows,test=final,reliability=reliability(y,probability),
        paired_bootstrap=dict(metric='Average precision difference vs RFM',replicates=500,seed=42,
            estimate=float(average_precision_score(y,probability)-average_precision_score(y,baseline)),
            lower=float(np.quantile(diff,.025)),upper=float(np.quantile(diff,.975))),
        importance=sorted(importance,key=lambda x:-x['average_precision_drop']),drift=drift,capacity=capacity,
        caveats=['One historical gift retailer; no treatment or offer-response labels.',
            'Customers recur across temporal snapshots; this is not customer-disjoint validation.',
            'November is a seasonal shift. Calibration may degrade after the October population.',
            'Permutation drops describe association and can be unstable for correlated features.',
            'Bootstrap interval is conditional on the fixed fitted model and one test month.',
            'High purchase propensity does not imply high incremental response to marketing.'])
    out=ROOT/'web/models';out.mkdir(exist_ok=True)
    (out/'propensity.json').write_text(json.dumps(artifact,separators=(',',':'),allow_nan=False),encoding='utf-8')
    (out/'benchmark.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    (out/'parity_cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
    digest=hashlib.sha256((out/'propensity.json').read_bytes()).hexdigest()
    (ROOT/'docs/outputs/ml-benchmark.json').write_text(json.dumps(dict(**report,model_sha256=digest),indent=2),encoding='utf-8')
    print(json.dumps(dict(selected=selected,validation=validation_rows,test=final,bootstrap=report['paired_bootstrap']),indent=2))


if __name__=='__main__':main()

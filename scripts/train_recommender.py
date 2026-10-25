"""Learn product embeddings and evaluate novel-product discovery out of time."""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'))
from train_models import load_data


def fit(df, cutoff, rank=32):
    history=df[(df.InvoiceDate<cutoff)&(df.Quantity>0)&df.CustomerID.notna()].copy()
    counts=history.groupby('StockCode').InvoiceNo.nunique().sort_values(ascending=False,kind='stable').head(500)
    catalog=list(counts.index);users=sorted(history.CustomerID.unique());ci={c:i for i,c in enumerate(catalog)};ui={u:i for i,u in enumerate(users)}
    interactions=history[history.StockCode.isin(catalog)].groupby(['CustomerID','StockCode']).InvoiceNo.nunique().reset_index(name='orders')
    matrix=csr_matrix((np.log1p(interactions.orders.to_numpy()),
        ([ui[u] for u in interactions.CustomerID],[ci[c] for c in interactions.StockCode])),shape=(len(users),len(catalog)))
    svd=TruncatedSVD(n_components=min(rank,len(catalog)-1),n_iter=7,random_state=42).fit(matrix)
    vectors=svd.components_.T
    names=history.groupby('StockCode').Description.last().to_dict()
    artifact=dict(schema_version=1,version='recommendations-1.0',training_cutoff=str(cutoff)[:10],rank=rank,
        items=[dict(code=c,name=names[c],orders=int(counts[c])) for c in catalog],vectors=np.round(vectors,8).tolist(),
        explained_variance=float(svd.explained_variance_ratio_.sum()),selected='svd')
    return artifact,history,users,matrix


def evaluate(df, cutoff, artifact, history, users, matrix, method):
    import pandas as pd
    cut=pd.Timestamp(cutoff)
    future=df[(df.InvoiceDate>=cut)&(df.InvoiceDate<cut+pd.Timedelta(days=30))&(df.Quantity>0)&df.CustomerID.notna()]
    past=history.groupby('CustomerID').StockCode.agg(set).to_dict()
    future_items=future.groupby('CustomerID').StockCode.agg(set).to_dict()
    vectors=np.array(artifact['vectors']);codes=[p['code'] for p in artifact['items']]
    counts=np.array([p['orders'] for p in artifact['items']]);all_scores=(matrix@vectors)@vectors.T if method=='svd' else None
    recalls=[];hits=[];precisions=[];rr=[];recommendations=set();covered=0;total_targets=0
    for row,user in enumerate(users):
        targets=future_items.get(user,set())-past[user]
        if not targets:continue
        scores=all_scores[row].copy() if method=='svd' else counts.astype(float).copy()
        for i,c in enumerate(codes):
            if c in past[user]:scores[i]=-np.inf
        ids=np.argsort(-scores,kind='stable')[:5]
        ranked=[codes[i] for i in ids if np.isfinite(scores[i])]
        overlap=set(ranked)&targets
        recalls.append(len(overlap)/len(targets));hits.append(int(bool(overlap)));precisions.append(len(overlap)/5)
        rr.append(next((1/(i+1) for i,c in enumerate(ranked) if c in targets),0))
        recommendations.update(ranked);covered+=len(targets&set(codes));total_targets+=len(targets)
    return dict(method=method,eligible=len(recalls),hit_rate_at5=float(np.mean(hits)),recall_at5=float(np.mean(recalls)),
        precision_at5=float(np.mean(precisions)),mrr_at5=float(np.mean(rr)),catalog_coverage=len(recommendations)/len(codes),
        target_catalog_coverage=covered/max(total_targets,1),candidate_items=len(codes),
        target_policy='All future novel products, including items outside the training top-500 catalog; known customers with at least one novel purchase only.')


def main():
    df=load_data();validation=[]
    for rank in [16,32]:
        art,hist,users,matrix=fit(df,'2011-09-01',rank)
        result=evaluate(df,'2011-09-01',art,hist,users,matrix,'svd');result['rank']=rank;validation.append(result)
    pop=evaluate(df,'2011-09-01',art,hist,users,matrix,'popularity');pop['rank']=None;validation.append(pop)
    chosen=max(validation,key=lambda x:(x['recall_at5'],x['hit_rate_at5']))
    best_rank=max([r for r in validation if r['method']=='svd'],key=lambda x:x['recall_at5'])['rank']
    artifact,hist,users,matrix=fit(df,'2011-11-01',best_rank)
    artifact['selected']=chosen['method']
    test=[evaluate(df,'2011-11-01',artifact,hist,users,matrix,m) for m in ['svd','popularity']]
    report=dict(validation_cutoff='2011-09-01',test_cutoff='2011-11-01',horizon_days=30,selected=chosen['method'],selected_rank=best_rank,
        selection_rule='Choose method/rank by September mean recall@5, hit-rate tie-break; refit history before November and evaluate once.',
        validation=validation,test=test,caveats=['Only known shoppers who buy a new product in the outcome month are eligible; not all shoppers.',
        'Top-500 candidate catalog is fitted from pre-cutoff history. Out-of-catalog future targets count as misses.',
        'Recommendations are co-purchase predictions, not causal sales lift or guaranteed relevance.',
        'Browser basket scoring uses supplied seeds; evaluation uses each shopper\'s full weighted history, a different input context.',
        'Item scores are ranking scores, not purchase probabilities; December seasonal generalization is untested.'])
    out=ROOT/'web/models';out.mkdir(exist_ok=True)
    (out/'recommender.json').write_text(json.dumps(artifact,separators=(',',':'),allow_nan=False),encoding='utf-8')
    (out/'recommendation-benchmark.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    (ROOT/'docs/outputs/recommendation-benchmark.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

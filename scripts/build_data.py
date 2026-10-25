"""Download UCI source, audit cleaning, produce reproducible aggregate artefacts."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import sys
import urllib.request
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analytics import segment

URL = 'https://archive.ics.uci.edu/static/public/352/online+retail.zip'


def records(df):
    return json.loads(df.to_json(orient='records', date_format='iso'))


def rfm(purchases, reference):
    identified = purchases.dropna(subset=['CustomerID'])
    r = identified.groupby('CustomerID').agg(last=('InvoiceDate', 'max'),
        frequency=('InvoiceNo', 'nunique'), monetary=('pence', 'sum'))
    r['recency'] = (reference-r['last']).dt.days
    high = r.monetary.quantile(.75) if len(r) else 0
    r['segment'] = [segment(row.recency, row.frequency, row.monetary, high) for row in r.itertuples()]
    return r


def aggregate(df, reference):
    pos = df[df.Quantity > 0].copy()
    returns = -int(df.loc[df.Quantity < 0, 'pence'].sum())
    gross = int(pos.pence.sum())
    orders = pos.InvoiceNo.nunique()
    customers = pos.CustomerID.nunique()
    r = rfm(pos, reference)
    seg = r.groupby('segment').agg(customers=('frequency','size'),revenue=('monetary','sum'),
                                 recency=('recency','median'),frequency=('frequency','median')).reset_index()
    seg['revenue'] = seg.revenue/100
    seg['share'] = seg.customers/max(len(r),1)
    monthly = pos.groupby(pos.InvoiceDate.dt.strftime('%Y-%m')).agg(revenue=('pence','sum'),orders=('InvoiceNo','nunique')).reset_index(names='month')
    monthly['revenue'] = monthly.revenue/100
    products = pos.groupby(['StockCode']).agg(name=('Description','first'),revenue=('pence','sum'),
        units=('Quantity','sum'),orders=('InvoiceNo','nunique')).sort_values('revenue',ascending=False).head(15).reset_index(names='code')
    products['revenue'] = products.revenue/100
    countries = pos.groupby('Country').agg(revenue=('pence','sum'),orders=('InvoiceNo','nunique')).sort_values('revenue',ascending=False).head(12).reset_index(names='country')
    countries['revenue'] = countries.revenue/100
    # Calendar-cohort retention; future cells are null, never represented as 0%.
    identified = pos.dropna(subset=['CustomerID']).copy()
    identified['period'] = identified.InvoiceDate.dt.to_period('M')
    first = identified.groupby('CustomerID').period.min()
    identified['cohort'] = identified.CustomerID.map(first)
    identified['age'] = [p.ordinal-c.ordinal for p,c in zip(identified.period,identified.cohort)]
    table = identified.groupby(['cohort','age']).CustomerID.nunique()
    cohorts=[]
    final_month = reference.to_period('M')
    for cohort in sorted(first.unique()):
        n = int(table.get((cohort,0),0))
        cohorts.append(dict(month=str(cohort),size=n,retention=[round(int(table.get((cohort,i),0))/max(n,1),4)
            if cohort.ordinal+i <= final_month.ordinal else None for i in range(7)]))
    # Restrict mining to 35 most frequently purchased products; count once per basket.
    top = pos.groupby('StockCode').InvoiceNo.nunique().nlargest(35).index
    baskets = pos[pos.StockCode.isin(top)].groupby('InvoiceNo').StockCode.agg(lambda s: sorted(set(s)))
    counts=Counter(); pairs=Counter()
    for basket in baskets:
        counts.update(basket); pairs.update(itertools.combinations(basket,2))
    names = pos.groupby('StockCode').Description.first().to_dict()
    rules=[]
    for (a,b), both in pairs.items():
        if both < 5: continue
        for a1,b1 in [(a,b),(b,a)]:
            rules.append(dict(a=names[a1],b=names[b1],baskets=both,support=both/max(orders,1),
                confidence=both/counts[a1],lift=both*orders/(counts[a1]*counts[b1])))
    rules=sorted(rules,key=lambda x:x['lift'],reverse=True)[:8]
    repeats = int((r.frequency>1).sum())
    return dict(kpis=dict(gross_sales=gross/100,returns=returns/100,net_sales=(gross-returns)/100,
        orders=int(orders),customers=int(customers),aov=gross/max(orders,1)/100,
        repeat_rate=repeats/max(len(r),1),identified_sales=float(r.monetary.sum())/100,
        units=int(pos.Quantity.sum()),rows=len(df)),segments=records(seg),monthly=records(monthly),
        products=records(products),countries=records(countries),cohorts=cohorts,rules=rules)


def holdout(df):
    pos=df[df.Quantity>0]
    rows=[]
    for date in ['2011-08-01','2011-09-01','2011-10-01']:
        cut=pd.Timestamp(date)
        r=rfm(pos[pos.InvoiceDate<cut],cut)
        future=set(pos[(pos.InvoiceDate>=cut)&(pos.InvoiceDate<cut+pd.Timedelta(days=30))].CustomerID.dropna())
        n=max(1, int(len(r)*.2))
        # Rule-based RFM ranking with ties resolved by ID. No outcome data in ranking.
        r['score'] = (r.frequency.rank(pct=True)+r.monetary.rank(pct=True)+(1-r.recency.rank(pct=True)))/3
        ranked=r.reset_index().sort_values(['score','CustomerID'],ascending=[False,True]).head(n)
        monetary=r.reset_index().sort_values(['monetary','CustomerID'],ascending=[False,True]).head(n)
        rate=sum(c in future for c in r.index)/max(len(r),1)
        precision=sum(c in future for c in ranked.CustomerID)/n
        mprecision=sum(c in future for c in monetary.CustomerID)/n
        rows.append(dict(cutoff=date,horizon_days=30,eligible=len(r),targeted=n,
            overall_repurchase_rate=rate,rfm_precision=precision,monetary_precision=mprecision,
            ranking_lift=precision/rate if rate else None))
    return rows


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zip',type=Path);args=parser.parse_args()
    rawdir=ROOT/'data/raw';rawdir.mkdir(parents=True,exist_ok=True)
    archive=args.zip or rawdir/'online-retail.zip'
    if not archive.exists():
        print('Downloading UCI Online Retail...');urllib.request.urlretrieve(URL,archive)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as z:
        with z.open('Online Retail.xlsx') as f: raw=pd.read_excel(f,engine='openpyxl')
    original=len(raw); clean=raw.drop_duplicates().copy();duplicates=original-len(clean)
    clean['StockCode']=clean.StockCode.astype(str)
    clean['InvoiceNo']=clean.InvoiceNo.astype(str)
    valid=clean.StockCode.str.fullmatch(r'\d{5}[A-Za-z]?') & clean.Description.notna() & (clean.UnitPrice>0) & (clean.Quantity!=0)
    excluded=len(clean)-int(valid.sum());clean=clean[valid].copy()
    clean['pence']=(clean.UnitPrice*100).round().astype('int64')*clean.Quantity.astype('int64')
    quality=dict(raw_rows=original,duplicates_removed=duplicates,non_merchandise_or_invalid_removed=excluded,
        retained_rows=len(clean),positive_rows=int((clean.Quantity>0).sum()),return_rows=int((clean.Quantity<0).sum()),
        missing_customer_rows=int(clean.CustomerID.isna().sum()),
        reconciliation_passed=bool(original==duplicates+excluded+len(clean)),sha256=digest)
    ref=clean.InvoiceDate.max().normalize()+pd.Timedelta(days=1)
    payload=dict(meta=dict(dataset='UCI Online Retail',source_url='https://archive.ics.uci.edu/dataset/352/online+retail',
        doi='10.24432/C5BW33',license='CC BY 4.0',currency='GBP',start=str(clean.InvoiceDate.min().date()),
        end=str(clean.InvoiceDate.max().date()),reference=str(ref.date()),
        caveat='Historical gift retailer with wholesale customers; not P&G or representative Swedish FMCG data.'),
        quality=quality,markets={},evaluation=holdout(clean))
    for market,countries in [('All markets',None),('United Kingdom',['United Kingdom']),('Sweden',['Sweden']),
                              ('Nordics',['Sweden','Norway','Denmark','Finland','Iceland'])]:
        subset=clean if countries is None else clean[clean.Country.isin(countries)]
        payload['markets'][market]={}
        for window in ['full','90d']:
            selected=subset if window=='full' else subset[subset.InvoiceDate>=ref-pd.Timedelta(days=90)]
            payload['markets'][market][window]=aggregate(selected,ref)
    (ROOT/'web/data.json').write_text(json.dumps(payload,indent=2,allow_nan=False),encoding='utf-8')
    (ROOT/'docs/results.json').write_text(json.dumps(dict(quality=quality,evaluation=payload['evaluation'],
        all_markets=payload['markets']['All markets']['full']['kpis'],
        sweden=payload['markets']['Sweden']['full']['kpis']),indent=2),encoding='utf-8')
    with sqlite3.connect(ROOT/'data/retail.sqlite') as db:
        clean.to_sql('transactions',db,if_exists='replace',index=False)
        db.execute('CREATE INDEX IF NOT EXISTS ix_country_date ON transactions(Country,InvoiceDate)')
    print(json.dumps(dict(quality=quality,kpis=payload['markets']['All markets']['full']['kpis'],evaluation=payload['evaluation']),indent=2))


if __name__=='__main__':main()

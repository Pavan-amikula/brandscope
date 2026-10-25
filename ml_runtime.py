"""Dependency-free inference for exported, versioned ML artifacts.

No pickle deserialization, API keys, network requests or customer identifiers.
The same JSON model contract is evaluated in the public browser.
"""
import math
import struct


def sigmoid(value):
    return 1/(1+math.exp(-max(-700,min(700,value))))


def predict_profile(artifact, profile):
    names=artifact['features']
    if set(profile)!=set(names):raise ValueError('Supply exactly the documented features')
    raw=[]
    warnings=[]
    for name in names:
        value=profile[name]
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:
            raise ValueError(f'{name} must be a finite nonnegative number')
        if name not in ['gross_spend','spend_30d','average_order_value'] and float(value)!=int(value):
            raise ValueError(f'{name} must be a whole number')
        raw.append(float(value))
        bounds=artifact['ranges'][name]
        if value<bounds['min'] or value>bounds['max']:warnings.append(name+' outside training range')
    if profile['orders_30d']>profile['orders'] or profile['spend_30d']>profile['gross_spend']:
        raise ValueError('30-day purchases cannot exceed all-history purchases')
    if profile['recency_days']>profile['tenure_days']:
        raise ValueError('Recency cannot exceed tenure')
    if profile['orders']<1 or profile['gross_spend']<=0 or profile['unique_products']<1:
        raise ValueError('The trained population requires prior positive purchases')
    if profile['recency_days']>30 and profile['orders_30d']>0:
        raise ValueError('A purchase over 30 days ago cannot have orders in the trailing 30 days')
    if (profile['orders_30d']==0)!=(profile['spend_30d']==0):
        raise ValueError('Trailing orders and spend must both be zero or both positive')
    x=[math.log1p(v) for v in raw]
    model=artifact['model']
    if model['kind']=='logistic':
        z=[(v-m)/s for v,m,s in zip(x,model['mean'],model['scale'])]
        terms=[v*c for v,c in zip(z,model['coef'])]
        probability=sigmoid(model['intercept']+sum(terms))
        explanations=[dict(feature=n,contribution=v) for n,v in zip(names,terms)]
    else:
        # sklearn forests convert features to float32 before traversing trees.
        # Preserve that contract at split boundaries in portable inference too.
        x=[struct.unpack('f',struct.pack('f',v))[0] for v in x]
        estimates=[]
        terms=[0.0]*len(names)
        for tree in model['trees']:
            node=0
            while tree['left'][node]!=-1:
                feature=tree['feature'][node]
                child=tree['left'][node] if x[feature]<=tree['threshold'][node] else tree['right'][node]
                terms[feature]+=(tree['probability'][child]-tree['probability'][node])/len(model['trees'])
                node=child
            estimates.append(tree['probability'][node])
        probability=sum(estimates)/len(estimates)
        explanations=[dict(feature=n,contribution=v) for n,v in zip(names,terms)]
    clipped=min(1-1e-9,max(1e-9,probability))
    cal=artifact['calibrator']
    calibrated=sigmoid(cal['intercept']+cal['coef']*math.log(clipped/(1-clipped)))
    return dict(probability=calibrated,raw_probability=probability,
                explanation=sorted(explanations,key=lambda r:abs(r['contribution']),reverse=True),
                warnings=warnings,model_version=artifact['version'],
                interpretation='Probability of a purchase in 30 days, not incremental response to marketing')


def recommend(artifact, codes, limit=5, method=None):
    if not isinstance(codes,list) or not 1<=len(codes)<=20 or not all(isinstance(c,str) for c in codes):
        raise ValueError('Supply 1–20 product codes')
    items=artifact['items'];indices={p['code']:i for i,p in enumerate(items)}
    if any(c not in indices for c in codes):raise ValueError('Unknown product code')
    chosen=set(indices[c] for c in codes)
    method=method or artifact['selected']
    if method not in ['svd','popularity']:raise ValueError('Unsupported recommendation method')
    if method=='svd':
        vectors=artifact['vectors']
        q=[sum(vectors[i][j] for i in chosen) for j in range(len(vectors[0]))]
        scores=[sum(a*b for a,b in zip(q,v)) for v in vectors]
    else:scores=[p['orders'] for p in items]
    ranking=sorted((i for i in range(len(items)) if i not in chosen),key=lambda i:(-scores[i],items[i]['code']))[:limit]
    return [dict(**items[i],score=float(scores[i]),method=method) for i in ranking]


def retrieve(artifact, question, limit=3):
    import re
    from collections import Counter
    if not isinstance(question,str) or not 3<=len(question.strip())<=1000:
        raise ValueError('Question must be 3–1000 characters')
    tokens=re.findall(r'(?u)\b\w\w+\b',question.lower())
    terms=artifact['vocabulary']; counts=Counter(t for t in tokens if t in terms)
    query={terms[t]:float(n)*artifact['idf'][terms[t]] for t,n in counts.items()}
    norm=math.sqrt(sum(v*v for v in query.values()))
    if not norm:return dict(answer=None,matches=[],abstained=True)
    scores=[]
    for chunk,vec in zip(artifact['chunks'],artifact['vectors']):
        score=sum(query.get(int(i),0)*v for i,v in vec)/norm
        if score>=artifact['threshold']:scores.append(dict(**chunk,similarity=score))
    scores.sort(key=lambda r:(-r['similarity'],r['id']))
    matches=scores[:limit]
    return dict(answer=matches[0]['text'] if matches else None,matches=matches,abstained=not bool(matches))

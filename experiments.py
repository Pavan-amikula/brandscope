"""Fixed-horizon, two-arm randomized experiment diagnostics.

Computes descriptive differences and large-sample confidence intervals, not
causality certification. Assignment and measurement validity require review.
"""
import csv
import io
import math
import statistics


def parse_experiment_csv(text):
    if not isinstance(text,str) or len(text)>2000000:raise ValueError('CSV must be at most 2 MB')
    reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    required={'participant_id','arm','converted','contribution'}
    if not required.issubset(reader.fieldnames or []):raise ValueError('Required columns: participant_id, arm, converted, contribution')
    rows=[];seen=set()
    for i,row in enumerate(reader,2):
        if len(rows)>=20000:raise ValueError('Maximum 20000 participants')
        participant=(row.get('participant_id') or '').strip()
        if not participant or participant in seen:raise ValueError(f'Row {i}: missing or duplicate participant_id')
        seen.add(participant)
        arm=(row.get('arm') or '').strip().lower()
        if arm not in ['control','treatment']:raise ValueError(f'Row {i}: arm must be control or treatment')
        converted=(row.get('converted') or '').strip()
        if converted not in ['0','1']:raise ValueError(f'Row {i}: converted must be 0 or 1')
        try:contribution=float(row['contribution'])
        except (ValueError,TypeError):raise ValueError(f'Row {i}: invalid contribution') from None
        if not math.isfinite(contribution) or abs(contribution)>1e8:raise ValueError(f'Row {i}: contribution outside bounds')
        rows.append(dict(participant_id=participant,arm=arm,converted=int(converted),contribution=contribution))
    return rows


def analyse_experiment(rows):
    if not isinstance(rows,list):raise ValueError('Rows must be a list')
    # Normalize through the CSV contract so API callers receive identical checks.
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=['participant_id','arm','converted','contribution'])
    writer.writeheader()
    try:writer.writerows(rows)
    except (ValueError,TypeError,AttributeError):raise ValueError('Invalid participant records') from None
    rows=parse_experiment_csv(out.getvalue())
    groups={arm:[r for r in rows if r['arm']==arm] for arm in ['control','treatment']}
    if min(map(len,groups.values()))<30:raise ValueError('At least 30 participants in each arm required')
    counts=[len(groups[a]) for a in ['control','treatment']];n=sum(counts)
    chi=sum((k-n/2)**2/(n/2) for k in counts);srm=math.erfc(math.sqrt(chi/2))
    summary={}
    for arm,items in groups.items():
        profits=[r['contribution'] for r in items]
        summary[arm]=dict(n=len(items),conversions=sum(r['converted'] for r in items),
            conversion=sum(r['converted'] for r in items)/len(items),mean_contribution=statistics.mean(profits),
            variance=statistics.variance(profits))
    c,t=summary['control'],summary['treatment']
    difference=t['mean_contribution']-c['mean_contribution']
    se=math.sqrt(t['variance']/t['n']+c['variance']/c['n'])
    conv_delta=t['conversion']-c['conversion']
    conv_se=math.sqrt(t['conversion']*(1-t['conversion'])/t['n']+c['conversion']*(1-c['conversion'])/c['n'])
    low,high=difference-1.959964*se,difference+1.959964*se
    rare=min(c['conversions'],t['conversions'],c['n']-c['conversions'],t['n']-t['conversions'])<10
    decision='Investigate assignment imbalance' if srm<.01 else 'Positive contribution evidence; review guardrails' if low>0 else 'Evidence of harm; stop and investigate' if high<0 else 'Inconclusive contribution; do not claim a win'
    return dict(n=n,arms=summary,srm_p_value=srm,expected_allocation='50:50',
        contribution=dict(difference=difference,lower=low,upper=high,standard_error=se),
        conversion=dict(difference=conv_delta,lower=conv_delta-1.959964*conv_se,upper=conv_delta+1.959964*conv_se),
        decision=decision,conversion_normal_approximation_warning=rare,
        caveats=['Large-sample independent-participant normal intervals; heavy-tailed contribution can invalidate approximation.',
        'No optional-stopping, clustering, multiple-testing or repeated-look correction.',
        'Conversion is secondary, not a substitute for contribution.',
        'Include all assigned eligible participants, including nonconverters; use original assignment.',
        'Source must supply consented randomized assignment, complete outcome windows, costs, returns and agreed guardrails.'])

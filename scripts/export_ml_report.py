"""Export exact benchmark tables and an optional recruiter-facing figure."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/outputs'
b=json.loads((ROOT/'web/models/benchmark.json').read_text())
r=json.loads((ROOT/'web/models/recommendation-benchmark.json').read_text())
with (OUT/'supervised-benchmark.csv').open('w',newline='',encoding='utf-8') as f:
    columns=['model','n','average_precision','roc_auc','precision_top20','brier','log_loss']
    writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(b['test'])
with (OUT/'recommendation-benchmark.csv').open('w',newline='',encoding='utf-8') as f:
    columns=['method','eligible','hit_rate_at5','recall_at5','precision_at5','mrr_at5','catalog_coverage']
    writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(r['test'])
text='''# AI/ML upgrade — measured evidence

All model metrics below are on historical November 2011 outcomes. No campaign was run and no retailer or recruitment outcome is claimed.

## Repurchase prediction

Training: March–August snapshots (15,063 rows). September selects between two fixed candidates. October fits a sigmoid probability calibrator. November is the final 30-day holdout (3,970 shoppers). Data after the feature cutoff never enter the features.

| Method | Average precision | ROC-AUC | Top-20% precision | Brier (lower better) |
| --- | ---: | ---: | ---: | ---: |
'''
for x in b['test']:
    text+=f"| {x['model']} | {x['average_precision']:.5f} | {x['roc_auc']:.5f} | {100*x['precision_top20']:.2f}% | {x['brier']:.5f} |\n" if 'brier' in x else f"| {x['model']} | {x['average_precision']:.5f} | {x['roc_auc']:.5f} | {100*x['precision_top20']:.2f}% | Not a probability model |\n"
text+='''
The constant prevalence model's top-20% precision depends on arbitrary tie order and has no targeting interpretation. The app suppresses that tied ranking result.

Selected forest + October calibration AP improvement vs RFM: 0.03307; 500-resample paired shopper bootstrap interval [0.02212, 0.04404]. Conditional on the fixed model and one month, not independent retailer validation.

Calibration does not improve November Brier score. Logistic regression slightly exceeds the selected forest on final-month AP. Those mixed findings are retained rather than choosing a new model after looking at the test month.

## Novel product recommendation

September selects 32-factor SVD by mean recall@5; the factorization is refit on pre-November purchases. Reported population: 1,247 known shoppers who purchase at least one novel product during the following 30 days. All future novel targets count, including those outside the top-500 candidate catalog.

| Method | Hit-rate@5 | Mean recall@5 | Precision@5 | MRR@5 | Catalog coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
'''
for x in r['test']:text+=f"| {x['method']} | {100*x['hit_rate_at5']:.2f}% | {100*x['recall_at5']:.2f}% | {100*x['precision_at5']:.2f}% | {x['mrr_at5']:.5f} | {100*x['catalog_coverage']:.1f}% |\n"
text+='''
Low recall remains important: only 36.74% of novel target products fall in the candidate catalog. The browser's one/two-seed interaction differs from the full-history evaluation context. Offline recommendation improvements are not measured sales uplift.

## Experiment and retrieval capabilities

The experiment analyser processes CSV outcomes using contribution difference, approximate 95% intervals, conversion difference and 50:50 sample-ratio diagnostics. Its 8,000-participant synthetic example has positive conversion evidence but an inconclusive contribution interval. The evidence assistant retrieves existing passages from a fitted TF-IDF index with source links and abstention; it is not a generative language model.

Full definitions, mixed results and model limitations: [MODEL_CARD.md](../MODEL_CARD.md). Research: [UPGRADE_RESEARCH.md](../UPGRADE_RESEARCH.md).
'''
(OUT/'ML_RESULTS.md').write_text(text,encoding='utf-8')
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(13,5.6),facecolor='#f6f4ef',gridspec_kw={'width_ratios':[1.3,1]})
    selected=[b['test'][i] for i in [0,2,3,4]]
    names=['Logistic regression','Selected forest + calibration','RFM baseline','Spend-only baseline']
    bars=axes[0].barh(names,[x['average_precision'] for x in selected],color=['#b18080','#722e46','#9ba39b','#c5c4bb'],height=.58)
    axes[0].invert_yaxis();axes[0].set_xlim(0,.75);axes[0].set_xlabel('Average precision · higher is better')
    for bar,x in zip(bars,selected):axes[0].text(bar.get_width()+.01,bar.get_y()+bar.get_height()/2,f"{x['average_precision']:.3f}",va='center')
    axes[0].set_title('30-day repurchase ranking',loc='left',fontweight='bold',pad=18)
    values=[x['hit_rate_at5']*100 for x in r['test']]
    bars=axes[1].bar(['SVD / 32 factors','Popularity baseline'],values,color=['#722e46','#9ba39b'],width=.5)
    axes[1].set_ylim(0,35);axes[1].set_ylabel('Historical hit-rate@5 (%)')
    for bar,v in zip(bars,values):axes[1].text(bar.get_x()+bar.get_width()/2,v+.7,f'{v:.2f}%',ha='center')
    axes[1].set_title('Novel-product recommendation',loc='left',fontweight='bold',pad=18)
    for ax in axes:ax.set_facecolor('#fffefa');ax.grid(axis='x' if ax is axes[0] else 'y',color='#e6e0d6',zorder=0);ax.set_axisbelow(True)
    fig.suptitle('BrandScope 2 · Out-of-time evidence',x=.025,ha='left',fontsize=19,fontweight='bold',color='#252a2b')
    fig.text(.025,.89,'November 2011 holdouts · 3,970 propensity shoppers / 1,247 eligible novel-product shoppers',fontsize=10,color='#66675f')
    fig.text(.025,.065,'Mixed results: calibration did not improve November Brier; recommendation mean recall@5 is only 3.20%.',fontsize=9,color='#722e46')
    fig.text(.025,.025,'One historical UK gift retailer. Ranking and recommendation metrics are not causal campaign lift or realized profit.',fontsize=9,color='#66675f')
    fig.subplots_adjust(left=.235,right=.97,top=.78,bottom=.20,wspace=.48)
    fig.savefig(OUT/'ml-evidence.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
    print('Exported model CSVs, report and benchmark figure.')
except ImportError:
    print('Exported model CSVs and report. Optional matplotlib figure skipped.')

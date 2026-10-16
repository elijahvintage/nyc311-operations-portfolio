from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, classification_report

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw' / 'nyc311_q1_2025.csv'
PROCESSED = ROOT / 'data' / 'processed'
OUT = ROOT / 'analysis'
CHARTS = ROOT / 'charts'
for p in [PROCESSED, OUT, CHARTS]: p.mkdir(parents=True, exist_ok=True)

sns.set_theme(style='whitegrid', context='talk')
PALETTE = '#0f766e'
ACCENT = '#d97706'
RED = '#b91c1c'

def savefig(name):
    plt.tight_layout()
    plt.savefig(CHARTS / name, dpi=180, bbox_inches='tight')
    plt.close()

def main():
    df = pd.read_csv(RAW, low_memory=False)
    raw_rows = len(df)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in ['created_date','closed_date']:
        df[c] = pd.to_datetime(df[c], errors='coerce')
    for c in ['agency','agency_name','complaint_type','descriptor','location_type','status','borough','open_data_channel_type']:
        df[c] = df[c].fillna('Unknown').astype(str).str.strip()
    df['incident_zip'] = df['incident_zip'].fillna('Unknown').astype(str)
    df['resolution_hours'] = (df['closed_date'] - df['created_date']).dt.total_seconds() / 3600
    df['closed_flag'] = df['closed_date'].notna() & df['status'].eq('Closed')
    df.loc[df['resolution_hours'] < 0, 'resolution_hours'] = np.nan
    df['closed_flag'] = df['closed_flag'] & df['resolution_hours'].notna()
    # A 72-hour threshold is a transparent operations triage assumption, not an official city SLA.
    df['sla_breach_72h'] = np.where(df['closed_flag'], df['resolution_hours'] > 72, np.nan)
    df['created_month'] = df['created_date'].dt.to_period('M').astype(str)
    df['created_dayofweek'] = df['created_date'].dt.day_name()
    df['created_hour'] = df['created_date'].dt.hour
    df['is_weekend'] = df['created_date'].dt.dayofweek >= 5
    df['open_at_extract'] = ~df['closed_flag']
    df.to_csv(PROCESSED / 'nyc311_q1_2025_clean.csv', index=False)

    closed = df[df['closed_flag']].copy()
    valid = df[df['created_date'].notna()].copy()
    summary = {
        'source': 'NYC Open Data 311 Service Requests from 2020 to Present',
        'source_id': 'erm2-nwe9',
        'period': '2025-01-01 through 2025-03-31 created requests',
        'raw_rows': int(raw_rows),
        'clean_rows': int(len(df)),
        'closed_rows': int(len(closed)),
        'open_at_extract_rows': int(df['open_at_extract'].sum()),
        'closure_rate': round(float(df['closed_flag'].mean()), 4),
        'median_resolution_hours': round(float(closed['resolution_hours'].median()), 2),
        'p90_resolution_hours': round(float(closed['resolution_hours'].quantile(.90)), 2),
        'breach_threshold_hours': 72,
        'breach_rate_closed': round(float(closed['sla_breach_72h'].mean()), 4),
        'negative_duration_rows_removed_from_duration': int(((df['closed_date']-df['created_date']).dt.total_seconds() < 0).sum()),
    }
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2))

    def group_metrics(col, min_n=100):
        x = closed.groupby(col).agg(requests=('unique_key','size'), median_hours=('resolution_hours','median'), p90_hours=('resolution_hours',lambda s:s.quantile(.90)), breach_rate=('sla_breach_72h','mean')).reset_index()
        x = x[x.requests >= min_n].sort_values(['breach_rate','requests'], ascending=[False,False])
        return x

    monthly = valid.groupby('created_month').agg(requests=('unique_key','size'), closed=('closed_flag','sum'), open_at_extract=('open_at_extract','sum')).reset_index()
    monthly['closure_rate'] = monthly['closed'] / monthly['requests']
    monthly.to_csv(OUT / 'monthly_volume.csv', index=False)
    agency = group_metrics('agency', 100)
    agency.to_csv(OUT / 'agency_performance.csv', index=False)
    complaint = group_metrics('complaint_type', 250)
    complaint.to_csv(OUT / 'complaint_performance.csv', index=False)
    borough = group_metrics('borough', 100)
    borough.to_csv(OUT / 'borough_performance.csv', index=False)
    channel = group_metrics('open_data_channel_type', 100)
    channel.to_csv(OUT / 'channel_performance.csv', index=False)
    hour = closed.groupby('created_hour').agg(requests=('unique_key','size'), breach_rate=('sla_breach_72h','mean'), median_hours=('resolution_hours','median')).reset_index()
    hour.to_csv(OUT / 'hour_performance.csv', index=False)

    # Priority score: high volume x high breach rate x severity proxy (median resolution).
    priority = complaint.copy()
    priority['priority_score'] = priority['requests'] * priority['breach_rate'] * priority['median_hours']
    priority = priority.sort_values('priority_score', ascending=False)
    priority.to_csv(OUT / 'priority_queue.csv', index=False)

    # Intake-time model: Jan-Feb train, March temporal holdout.
    model_df = valid.copy()
    model_df['breach_target'] = model_df['sla_breach_72h'].fillna(0).astype(int)
    model_df = model_df[model_df['closed_flag']].copy()
    train = model_df[model_df['created_date'] < pd.Timestamp('2025-03-01')]
    test = model_df[model_df['created_date'] >= pd.Timestamp('2025-03-01')]
    features = ['agency','complaint_type','location_type','borough','open_data_channel_type','created_dayofweek','created_hour','is_weekend']
    cats = ['agency','complaint_type','location_type','borough','open_data_channel_type','created_dayofweek']
    nums = ['created_hour','is_weekend']
    prep = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore', min_frequency=25), cats), ('num', StandardScaler(), nums)])
    model = Pipeline([('prep', prep), ('clf', LogisticRegression(max_iter=300, class_weight='balanced', C=.5))])
    model.fit(train[features], train['breach_target'])
    p = model.predict_proba(test[features])[:,1]
    metrics = {'train_rows': int(len(train)), 'test_rows': int(len(test)), 'test_breach_rate': round(float(test.breach_target.mean()),4), 'roc_auc': round(float(roc_auc_score(test.breach_target,p)),4), 'average_precision': round(float(average_precision_score(test.breach_target,p)),4)}
    (OUT / 'model_metrics.json').write_text(json.dumps(metrics, indent=2))
    test_out = test[['unique_key','created_date','agency','complaint_type','borough','open_data_channel_type','breach_target']].copy()
    test_out['predicted_breach_probability'] = p
    test_out.sort_values('predicted_breach_probability', ascending=False).head(1000).to_csv(OUT / 'march_high_risk_queue.csv', index=False)

    # Charts
    plt.figure(figsize=(11,5)); sns.lineplot(data=monthly, x='created_month', y='requests', marker='o', color=PALETTE); plt.title('NYC 311 intake volume by month — Q1 2025'); plt.xlabel('Created month'); plt.ylabel('Requests'); plt.xticks(rotation=30); savefig('01_monthly_volume.png')
    top = complaint.head(12).sort_values('breach_rate'); plt.figure(figsize=(10,7)); plt.barh(top['complaint_type'], top['breach_rate']*100, color=ACCENT); plt.title('Slow-resolution risk by high-volume problem type'); plt.xlabel('Closed requests breaching 72 hours (%)'); plt.ylabel(''); savefig('02_complaint_breach_rate.png')
    topa = agency.head(12).sort_values('breach_rate'); plt.figure(figsize=(10,6)); plt.barh(topa['agency'], topa['breach_rate']*100, color=PALETTE); plt.title('Agency-level resolution risk'); plt.xlabel('Closed requests breaching 72 hours (%)'); plt.ylabel(''); savefig('03_agency_breach_rate.png')
    plt.figure(figsize=(10,7)); sns.scatterplot(data=priority, x='requests', y='breach_rate', size='median_hours', hue='priority_score', palette='YlOrRd', sizes=(40,500), legend=False); plt.xscale('log'); plt.gca().yaxis.set_major_formatter(lambda x,pos:f'{x:.0%}'); plt.title('Where to focus operations attention'); plt.xlabel('Closed request volume (log scale)'); plt.ylabel('72-hour breach rate'); savefig('04_priority_matrix.png')
    hm = closed.pivot_table(index='borough', columns='created_month', values='sla_breach_72h', aggfunc='mean'); plt.figure(figsize=(10,5)); sns.heatmap(hm, annot=True, fmt='.0%', cmap='YlOrRd', vmin=0, vmax=1); plt.title('Resolution risk by borough and intake month'); plt.xlabel('Created month'); plt.ylabel('Borough'); savefig('05_borough_heatmap.png')
    print(json.dumps(summary, indent=2)); print(json.dumps(metrics, indent=2))

if __name__ == '__main__': main()

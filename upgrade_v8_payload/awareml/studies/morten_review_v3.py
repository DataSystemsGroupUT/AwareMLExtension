"""Shared study contracts and exact-stimulus human review; no inferred human labels."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from awareml.engine.pareto_spec import robust_unit, NORMALIZATION_ID

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'data/journal/trust_stimulus_bank_v3/frozen'
REVIEWS = ROOT / 'artifacts/phase16_v3/assessor_reviews.csv'
OBJECTIVES = {'Accuracy': ('accuracy', 'max'), 'Runtime': ('runtime_sec', 'min'),
              'Energy': ('energy_kwh', 'min'), 'CO2': ('co2_kg', 'min')}
EXPLANATION_ACTIONS = ('Use as shown', 'Correct before use', 'Do not use', 'Unsure')
SCOPE_CHOICES = ('Included study objectives', 'Requirements beyond the study objectives', 'Both', 'Unsure')
SCOPE_TEXT = ('This study ranks frameworks only on the included Accuracy, Runtime, Energy and CO₂ objectives. '
              'The included objectives are a study task specification based on prior human scenario annotation, '
              'not a complete interpretation of every scenario requirement. Privacy and security are not assessed. '
              'A favourable rank does not establish suitability for all real-world requirements. '
              'Judge the stated task; you may report limitations or withhold reliance because of broader concerns.')
PROVENANCE_TEXT = ('Researcher-constructed reference evidence for this study task, supplied to the explanation generator. '
                   'The table is authoritative within the task and is separate from the AI output being assessed. '
                   'It is not independently collected deployment evidence or a measured run on this textual scenario. '
                   'An explanation can misstate this reference; use the table to assess its factual claims.')
REVIEW_COLUMNS = ['bank_sha256', 'review_id', 'assessor_id', 'recommendation_verdict',
                  'explanation_verdict', 'claim_or_reason', 'reference_location', 'scope_clear']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def bank_rows(root=BANK):
    return json.loads((Path(root)/'stimuli_researcher.json').read_text(encoding='utf-8'))


def review_identity(row):
    return 'RV-' + digest(row['stimulus_id'])[:12].upper()


def review_template(assessor_id='', root=BANK):
    bank_sha = hashlib.sha256((Path(root)/'stimuli_researcher.json').read_bytes()).hexdigest()
    records = [dict.fromkeys(REVIEW_COLUMNS, '') for _ in bank_rows(root)]
    for rec, row in zip(records, bank_rows(root)):
        rec.update(bank_sha256=bank_sha, review_id=review_identity(row), assessor_id=assessor_id)
    return pd.DataFrame(records, columns=REVIEW_COLUMNS).sort_values('review_id').reset_index(drop=True)


def review_status(reviews: Optional[pd.DataFrame] = None, root=BANK):
    expected = {review_identity(r): r for r in bank_rows(root)}
    if reviews is None:
        reviews = pd.read_csv(REVIEWS, keep_default_na=False) if REVIEWS.exists() else pd.DataFrame()
    failures = []
    if reviews.empty or not set(REVIEW_COLUMNS).issubset(reviews.columns):
        return {'ready': False, 'reviewed_items': 0, 'required_items': len(expected), 'issues': ['Two independent complete assessor reviews are required.']}
    frame = reviews.copy().fillna('')
    bank_sha = hashlib.sha256((Path(root)/'stimuli_researcher.json').read_bytes()).hexdigest()
    if not frame['bank_sha256'].eq(bank_sha).all(): failures.append('Review belongs to a different stimulus version.')
    if not frame['assessor_id'].astype(str).str.strip().ne('').all(): failures.append('Assessor identifiers are missing.')
    if frame.duplicated(['review_id', 'assessor_id']).any(): failures.append('Duplicate assessor/item rows.')
    if set(frame['review_id']) - set(expected): failures.append('Unknown review item IDs.')
    complete = 0
    for rid, row in expected.items():
        g = frame[frame['review_id'].eq(rid)]
        target = 'Supported' if row['researcher_label'] == 'known_correct' else 'Incorrect'
        ok = (g['assessor_id'].nunique() >= 2 and g['recommendation_verdict'].eq('Supported').all()
              and g['explanation_verdict'].eq(target).all() and g['scope_clear'].eq('Yes').all()
              and g['claim_or_reason'].astype(str).str.strip().ne('').all()
              and g['reference_location'].astype(str).str.strip().ne('').all())
        if ok: complete += 1
        else: failures.append(rid + ': incomplete review, uncertainty, or unresolved disagreement with the reference audit.')
    return {'ready': not failures, 'reviewed_items': complete, 'required_items': len(expected), 'issues': failures}


def store_reviews(frame):
    if not set(REVIEW_COLUMNS).issubset(frame.columns): raise ValueError('Missing review CSV columns.')
    frame = frame[REVIEW_COLUMNS].fillna('').astype(str)
    if frame.duplicated(['review_id','assessor_id']).any(): raise ValueError('Duplicate review rows in upload.')
    if REVIEWS.exists():
        current = pd.read_csv(REVIEWS, keep_default_na=False)
        frame = pd.concat([current,frame],ignore_index=True).drop_duplicates(['review_id','assessor_id'], keep='last')
    status = review_status(frame)
    if any('different stimulus' in x or 'Unknown review' in x for x in status['issues']):
        raise ValueError('Review IDs or bank hash do not match the current exact stimuli.')
    REVIEWS.parent.mkdir(parents=True,exist_ok=True)
    if REVIEWS.exists():
        import time
        REVIEWS.replace(REVIEWS.with_name('assessor_reviews_backup_{}.csv'.format(time.time_ns())))
    frame.to_csv(REVIEWS,index=False)
    return status


def validate_claims(rows=None):
    issues=[]
    rows=rows if rows is not None else bank_rows()
    for row in rows:
        ev=row['evidence_summary']; refs={r['framework']:r for r in ev['frameworks']}
        top=min(ev['frameworks'],key=lambda x:x['rank'])
        if row['recommended_framework'] != top['framework']: issues.append(row['stimulus_id']+': recommendation mismatch')
        wrong=0
        for c in row['claims']:
            actual=float(refs[c['framework']][c['metric']])
            if not np.isclose(actual,float(c['reference']),rtol=0,atol=1e-12): issues.append('Reference audit mismatch')
            wrong += int(not c['supported'])
        if wrong != (0 if row['researcher_label']=='known_correct' else 1): issues.append(row['stimulus_id']+': incorrect error count')
    return issues


def scenario_coverage(responses, root=ROOT):
    catalog=pd.read_csv(Path(root)/'data/journal/objective_selection_benchmark_v2/frozen/primary_benchmark.csv')
    selected={r['scenario_id'] for r in bank_rows()}
    counts=responses['scenario_id'].value_counts().to_dict() if not responses.empty and 'scenario_id' in responses else {}
    return [{'benchmark_id':r['benchmark_id'],'scenario_id':r['scenario_id'],'included_in_track2':r['scenario_id'] in selected,
             'evaluations':int(counts.get(r['scenario_id'],0)),'expected_N34':34 if r['scenario_id'] in selected else 0,
             'expected_N40':40 if r['scenario_id'] in selected else 0} for _,r in catalog.iterrows()]


def paired_inference(gaps, seed=22026, iterations=10000):
    a=np.asarray(gaps,dtype=float); a=a[np.isfinite(a)]; n=len(a)
    out={'n_participants':n,'mean_gap':float(a.mean()) if n else None,'ci95':[None,None],'cohen_dz':None,
         'cohen_dz_ci95':[None,None],'p_two_sided':None,'seed':seed,'iterations':iterations}
    if n<2: return out
    rng=np.random.default_rng(seed); sample=rng.choice(a,(iterations,n),replace=True)
    out['ci95']=np.percentile(sample.mean(1),[2.5,97.5]).tolist()
    sd=a.std(ddof=1)
    if sd>0:out['cohen_dz']=float(a.mean()/sd)
    sds=sample.std(1,ddof=1); defined=sds>0
    if defined.any():out['cohen_dz_ci95']=np.percentile(sample[defined].mean(1)/sds[defined],[2.5,97.5]).tolist()
    # Exact for small n; Monte Carlo with plus-one correction otherwise.
    if n<=16:
        signs=1-2*((np.arange(2**n)[:,None]>>np.arange(n))&1)
        perm=np.abs((signs*a).mean(1));out['p_two_sided']=float((perm>=abs(a.mean())-1e-12).mean());out['test_method']='exact paired sign-flip'
    else:
        perm=np.abs((rng.choice([-1,1],(iterations,n))*a).mean(1))
        out['p_two_sided']=float((1+(perm>=abs(a.mean())-1e-12).sum())/(iterations+1));out['test_method']='Monte Carlo paired sign-flip'
    return out


def evidence_association(frame, iterations=5000):
    if frame.empty:return {'status':'insufficient_data'}
    f=frame.copy();f['sought_optional_evidence']=pd.to_numeric(f['evidence_question_count'],errors='coerce').fillna(0)>0
    out={'interpretation':'Exploratory association, not a causal effect of evidence seeking.',
         'action_by_optional_evidence':pd.crosstab(f['sought_optional_evidence'],f['decision_action']).reset_index().to_dict('records')}
    # Bootstrap whole participants to preserve dependence among their 20 responses.
    participants=list(f['participant_hash'].unique()); rng=np.random.default_rng(22027)
    for label,col,value in [('recommendation_accept','decision_action','Accept'),('explanation_use','explanation_action','Use as shown')]:
        if col not in f: continue
        z=f.assign(y=f[col].eq(value).astype(float))
        means=z.groupby('sought_optional_evidence')['y'].mean()
        observed=float(means[True]-means[False]) if len(means)==2 else None
        boot=[]
        if len(participants)>=2 and observed is not None:
            aggregates=[]
            for participant in participants:
                group=z[z['participant_hash'].eq(participant)]
                no=group[~group.sought_optional_evidence];yes=group[group.sought_optional_evidence]
                aggregates.append([no.y.sum(),len(no),yes.y.sum(),len(yes)])
            table=np.asarray(aggregates,float)
            sampled=table[rng.integers(0,len(participants),(iterations,len(participants)))].sum(axis=1)
            valid=(sampled[:,1]>0)&(sampled[:,3]>0)
            boot=(sampled[valid,2]/sampled[valid,3]-sampled[valid,0]/sampled[valid,1]).tolist()
        out[label]={'risk_difference_evidence_minus_no_evidence':observed,'participant_bootstrap_ci95':np.percentile(boot,[2.5,97.5]).tolist() if boot else [None,None]}
    out['initial_correctness_by_subsequent_evidence']=f.groupby('sought_optional_evidence')['perceived_correctness'].agg(['mean','count']).reset_index().to_dict('records')
    return out


def study_ranking(results, scenario, weights=None):
    names={'AutoStreamML','AutoClass','EvoAutoML','OAML','ChaCha'}
    if len(results)!=5 or {r.get('framework') for r in results}!=names:
        raise ValueError('Exactly one measured result for each of the five frameworks is required.')
    objs=[x.strip() for x in str(scenario.get('ground_truth') or '').split('|') if x.strip()]
    if not objs or set(objs)-set(OBJECTIVES): raise ValueError('No valid supported study objectives.')
    w={o:1.0 for o in objs} if weights is None else dict(weights)
    if set(w)!=set(objs) or any(not np.isfinite(float(v)) or float(v)<=0 for v in w.values()):
        raise ValueError('Provide a positive weight for every included objective and no others.')
    total=sum(float(v) for v in w.values());w={o:float(v)/total for o,v in w.items()}
    df=pd.DataFrame(results);score=pd.Series(0.0,index=df.index)
    for o in objs:
        col,direction=OBJECTIVES[o];values=pd.to_numeric(df.get(col),errors='coerce')
        if values is None or not np.isfinite(values).all():raise ValueError('Missing measured '+o+' for one or more frameworks.')
        if (values<0).any() or (o=='Accuracy' and (values>1).any()):raise ValueError('Invalid measured '+o+' values.')
        score+=w[o]*robust_unit(values,direction)
    df=df.assign(utility=score,scenario_fit_score=score).sort_values(['scenario_fit_score','framework'],ascending=[False,True]).reset_index(drop=True)
    df['rank']=range(1,6)
    return df.to_dict('records'),{'objective_weights':w,'normalization_id':NORMALIZATION_ID,
           'formula':'sum(weight * normalized objective); selected weights sum to 1; costs inverted; 5/95 percentile clipping; constant metric = 0.5',
           'tie_break':'Score descending then framework name; tied score does not establish a substantive difference.'}


def agency_evidence_association(responses, secondary, iterations=10000):
    """Comment 3 is anchored to critical_evaluation, not the final action question."""
    if responses.empty or not secondary:return {'status':'insufficient_data'}
    f=responses.copy();f['optional_evidence']=pd.to_numeric(f.evidence_question_count,errors='coerce').fillna(0).gt(0)
    counts=f.groupby('participant_hash').agg(evidence_trial_fraction=('optional_evidence','mean'),optional_questions=('evidence_question_count','sum'))
    ratings=[]
    for row in secondary:
        rating=json.loads(row['ratings_json']).get('critical_evaluation')
        if rating is not None:ratings.append({'participant_hash':row['participant_hash'],'critical_evaluation':rating})
    if not ratings:return {'status':'insufficient_data'}
    joined=counts.join(pd.DataFrame(ratings).set_index('participant_hash'),how='inner').dropna()
    out={'question':'I felt able to critically evaluate the recommendation provided by AwareML.',
         'analysis_unit':'Participant; agency rating versus fraction of their trials with optional evidence.',
         'n_participants':len(joined),'records':joined.reset_index().to_dict('records'),'spearman_rho':None,'permutation_p_two_sided':None,
         'interpretation':'Secondary exploratory association; neither evidence use nor self-reported agency establishes causality.'}
    if len(joined)>=3 and joined.critical_evaluation.nunique()>1 and joined.evidence_trial_fraction.nunique()>1:
        x=joined.critical_evaluation.rank().to_numpy();y=joined.evidence_trial_fraction.rank().to_numpy()
        rho=float(np.corrcoef(x,y)[0,1]);rng=np.random.default_rng(22028)
        perm=np.array([np.corrcoef(x,rng.permutation(y))[0,1] for _ in range(iterations)])
        out.update(spearman_rho=rho,permutation_p_two_sided=float((1+(np.abs(perm)>=abs(rho)-1e-12).sum())/(iterations+1)),permutations=iterations,seed=22028)
    return out

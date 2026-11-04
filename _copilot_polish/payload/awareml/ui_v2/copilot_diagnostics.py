"""Diagnostics for the current learned outcomes; presentation never changes selection."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from awareml.protocol_v3.common import OBJECTIVES, desirability, utilities
from .framework_labels import framework_label, display_frame, display_figure
from .state import ROOT


def pareto_flags(ranked, weights):
    active=[k for k in OBJECTIVES if float(weights.get(k,0))>0]
    values=ranked[active].to_numpy(dtype=float).copy()
    if 'accuracy' in active:values[:,active.index('accuracy')]*=-1
    return np.asarray([not any(np.all(other<=row+1e-12) and np.any(other<row-1e-12)
                       for other in values) for row in values])


def sensitivity_table(ranked, presets):
    rows=[]
    for name,weights in presets.items():
        values=utilities(ranked[list(OBJECTIVES)].to_numpy(),weights)
        order=np.argsort(-values,kind='stable')
        for position,index in enumerate(order,1):
            rows.append({'Profile':name,'Framework':str(ranked.iloc[index].framework),
                         'Rank':position,'Utility':float(values[index])})
    return pd.DataFrame(rows)


def render_dataset_diagnostics(state, ranked, weights, meta, signature, evidence_id):
    from .copilot_recommender import DATASET_PRESETS
    st.markdown('### Recommendation diagnostics and human review')
    why,uncertainty,sensitivity,decision=st.tabs(['Why this ranking?','Uncertainty','Sensitivity','Human decision'])
    with why:
        scores=desirability(ranked[list(OBJECTIVES)].to_numpy())
        rows=[{'Framework':framework_label(str(row.framework)), 'Objective':key.title().replace('Co2','CO₂'),
               'Contribution':float(scores[i,j]*weights[key])}
              for i,(_,row) in enumerate(ranked.iterrows()) for j,key in enumerate(OBJECTIVES)]
        fig=px.bar(pd.DataFrame(rows),x='Contribution',y='Framework',color='Objective',orientation='h',
                   title='How each objective contributes to preference utility')
        fig.update_layout(height=360,yaxis={'autorange':'reversed'},legend={'orientation':'h'})
        st.plotly_chart(fig,use_container_width=True,key='cop_current_contributions')
        st.caption('Contribution is weight × normalized desirability, using the same calculation as the recommender. The Pareto indicator uses the objectives with positive weights.')
    with uncertainty:
        from .copilot_polish import interval_figure
        cols=st.columns(2)
        for i,(key,label,scale) in enumerate([('accuracy','Accuracy (%)',100),('runtime','Runtime (s)',1),('energy','Energy (Wh)',1000),('co2','CO₂ (g)',1000)]):
            if key+'_lower' not in ranked or key+'_upper' not in ranked:continue
            with cols[i%2]:
                st.plotly_chart(interval_figure(ranked,key,label,scale),use_container_width=True,key='cop_interval_'+key)
        st.caption('Dots show point estimates; horizontal ranges show empirical intervals. Gold highlights the recommended framework. Overlap is not a significance test. Intervals do not change the ranking.')
    with sensitivity:
        table=sensitivity_table(ranked,DATASET_PRESETS)
        st.dataframe(display_frame(table),use_container_width=True,hide_index=True)
        st.caption('These profiles rerank the same predicted outcomes. Frameworks are not executed again.')
    with decision:
        st.markdown('**Human review of the dataset-aware recommendation**')
        choice=st.radio('How do you want to treat this recommendation?',
            ['Use as candidate plan','Keep as alternative','Reject recommendation'],horizontal=True,key='cop_current_human_decision')
        note=st.text_input('Decision note (optional)',key='cop_current_human_note')
        if st.button('Save dataset-aware review',key='cop_current_save_review',use_container_width=True):
            record={'record_type':'dataset_aware_recommender_human_review','review_id':'DAR-'+uuid.uuid4().hex[:10].upper(),
                'timestamp_utc':datetime.now(timezone.utc).isoformat(),'dataset_name':state.get('dataset_name'),
                'target':state.get('target'),'recommended_framework':str(ranked.iloc[0].framework),
                'ranking_utility':float(ranked.iloc[0].utility),'weights':dict(weights),
                'decision':choice,'note':note.strip() or None,'evidence_id':evidence_id,
                'recommendation_signature':signature,'recommender_retrained':False}
            path=ROOT/'artifacts/copilot/dataset_aware_recommender_reviews.jsonl'
            try:
                path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('a',encoding='utf-8') as handle:handle.write(json.dumps(record,sort_keys=True,default=str)+'\n')
                state['dataset_aware_human_review']=record
            except OSError as exc:st.error('Review could not be saved: '+str(exc))
        saved=state.get('dataset_aware_human_review') or {}
        if saved.get('recommendation_signature')==signature:st.success('Saved review: {} · {}'.format(saved['review_id'],saved['decision']))

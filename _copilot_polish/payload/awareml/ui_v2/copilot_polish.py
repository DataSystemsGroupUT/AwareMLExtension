"""Readable recommendation evidence and optional grounded LLM explanations."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from .framework_labels import framework_label,display_frame


def polish_css():
    st.markdown('''<style>
    [data-testid="stMetric"]{border:1px solid #dbe5f1;border-top:3px solid #5278d6;
    border-radius:16px;padding:16px 18px;background:linear-gradient(135deg,#fff,#f5f8ff);
    box-shadow:0 5px 16px rgba(25,54,95,.06);min-height:110px}
    [data-testid="stMetricLabel"]{color:#52677f;font-size:.8rem;letter-spacing:.02em}
    [data-testid="stMetricValue"]{font-size:clamp(1.15rem,2vw,1.85rem);color:#12345c}
    [data-testid="stMetricValue"]>div{white-space:normal!important;overflow-wrap:anywhere}
    </style>''',unsafe_allow_html=True)


def interval_figure(ranked,key,label,scale=1):
    fig=go.Figure()
    for i,(_,row) in enumerate(ranked.iterrows()):
        point=float(row[key])*scale;lo=float(row[key+'_lower'])*scale;hi=float(row[key+'_upper'])*scale
        color='#c58a16' if i==0 else '#5579b8'
        name=framework_label(str(row.framework))
        fig.add_trace(go.Scatter(x=[lo,hi],y=[name,name],mode='lines',line={'color':color,'width':7},opacity=.35,showlegend=False,hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=[point],y=[name],mode='markers',marker={'color':color,'size':12,'line':{'color':'white','width':2}},
            customdata=[[lo,hi]],showlegend=False,
            hovertemplate='%{y}<br>Estimate: %{x:.4g}<br>Interval: %{customdata[0]:.4g}–%{customdata[1]:.4g}<extra></extra>'))
    fig.update_layout(title=label+(' · higher is better' if key=='accuracy' else ' · lower is better'),height=310,
        template='plotly_white',margin={'l':10,'r':24,'t':52,'b':35},yaxis={'autorange':'reversed'},xaxis={'title':label,'rangemode':'tozero'})
    return fig


def render_preference_audit(ranked,presets):
    from .copilot_diagnostics import sensitivity_table
    with st.expander('Does changing priorities change the recommendation?',expanded=False):
        table=sensitivity_table(ranked,presets)
        winners=table.loc[table.Rank==1].copy()
        st.dataframe(display_frame(winners),use_container_width=True,hide_index=True)
        st.caption('Every profile recomputes utility from the same dataset-specific predictions. The winner can remain the same while scores and alternatives change.')


def explanation_evidence(ranked,weights,meta):
    columns=[k for k in ('rank','framework','utility','accuracy','runtime','energy','co2') if k in ranked]
    return {'objective_weights':dict(weights),'profile_observations':meta.get('profile',{}).get('profile_sample_size'),
            'outcome_scope':'predicted outcomes, not observed framework execution',
            'ranked_candidates':ranked[columns].to_dict(orient='records')}


def render_explainer(state,ranked,weights,meta,signature):
    st.markdown('### LLM-assisted recommendation explanation')
    st.caption('LLaMA explains the computed ranking and trade-offs. It does not choose or rerank frameworks. Raw dataset rows are not sent.')
    if st.button('Explain this recommendation',key='cop_current_explain',use_container_width=True):
        try:
            from awareml.llm import OllamaClient
            evidence=explanation_evidence(ranked,weights,meta)
            prompt=('Explain this already-computed AutoML recommendation using only the JSON evidence. '
                'Do not select or rerank frameworks. Distinguish predictions from measurements. '
                'Write four short sections: recommendation, weighted trade-offs, runner-up, what to validate after execution. '
                'Use ChaCha-OVR as the display name for ChaCha. Utility is not confidence. '
                'Do not invent values or claim statistical significance from interval overlap.\n'+json.dumps(evidence,default=str))
            client=OllamaClient(model='llama3:8b',timeout_sec=90.0)
            answer,_=client.generate_text(prompt)
            if isinstance(answer,dict):answer=answer.get('response') or answer.get('text')
            if not isinstance(answer,str) or not answer.strip():raise ValueError('The model returned no explanation.')
            state['cop_current_explanation']={'signature':signature,'text':answer}
        except Exception as exc:st.warning('Explanation service unavailable: '+str(exc))
    saved=state.get('cop_current_explanation') or {}
    if saved.get('signature')==signature:
        with st.container(border=True):st.markdown(saved['text'])
        st.caption('LLM-generated explanation. Check numerical claims against the prediction table above.')

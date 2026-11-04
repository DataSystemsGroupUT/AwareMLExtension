"""Identical stimulus rendering for participants and independent assessors."""
import pandas as pd
import streamlit as st
from awareml.studies.morten_review_v3 import SCOPE_TEXT, PROVENANCE_TEXT


def render_stimulus_card(trial):
    ev=trial.get('reference_evidence') or {}
    st.markdown('#### Scenario context')
    st.write(trial.get('scenario_text'))
    st.caption('Scenario {} · {}'.format(trial.get('scenario_id',''),trial.get('domain','')))
    st.markdown('#### Study task and included objectives')
    st.write(trial.get('prompt'))
    st.caption(SCOPE_TEXT)
    st.write('Included objectives and weights:',ev.get('objective_weights') or {})
    st.markdown('#### AI recommendation')
    st.write(trial.get('recommendation'))
    st.markdown('#### AI explanation supporting the recommendation')
    st.write(trial.get('explanation'))
    st.markdown('#### Study reference evidence')
    st.caption(PROVENANCE_TEXT)
    frame=pd.DataFrame(ev.get('frameworks') or []).rename(columns={
        'framework':'Framework','rank':'Reference rank','scenario_fit_score':'Scenario-fit score',
        'accuracy':'Accuracy','runtime_sec':'Runtime (s)','energy_kwh':'Energy (kWh)','co2_kg':'CO₂ (kg)'})
    cols=['Reference rank','Framework','Scenario-fit score','Accuracy','Runtime (s)','Energy (kWh)','CO₂ (kg)']
    st.dataframe(frame[[c for c in cols if c in frame]],hide_index=True,use_container_width=True)
    st.caption('Scenario-fit score = weighted mean of direction-normalized included objectives. '+str(ev.get('normalization',''))+'. This table is supplied study material, not another AI answer.')

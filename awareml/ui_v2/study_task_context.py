"""Shared, expanded task presentation for participants and assessors."""
import streamlit as st
from awareml.studies.task_context_revision import TASK_INSTRUCTION, require_information_context


def render_task(trial):
    st.markdown('### Scenario and decision context')
    st.write(trial['scenario_text'])
    st.caption('Scenario {} · {}'.format(trial.get('scenario_id',''),trial.get('domain','')))
    st.markdown('**Your decision task**')
    from awareml.ui_v2.final_study_language import decision_task
    st.write(decision_task(TASK_INSTRUCTION))
    st.caption('The scenario describes the situation. The table supports only the included study objectives; it does not validate every requirement in that situation.')


def render_information_task(ctx):
    scenario=require_information_context(ctx)
    st.markdown('### Scenario and decision context')
    st.write(scenario['scenario'])
    st.caption('Scenario {} · {}'.format(scenario.get('benchmark_id') or scenario.get('scenario_id',''),scenario.get('domain','')))
    st.markdown('**Your decision task**')
    st.write('Imagine advising the decision-maker in this scenario. Inspect the saved framework recommendation and its measured benchmark evidence. Decide whether to rely on it, propose a change or withhold reliance. Seek more information only if you need it; stopping without a question is valid.')
    st.caption('The scenario supplies decision context. The saved benchmark measurements are not measurements of deployment in this scenario. Questions and proposed changes do not recompute the recommendation.')

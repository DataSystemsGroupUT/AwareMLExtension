from __future__ import annotations
from html import escape
import streamlit as st
from .recommender_bridge import sync_copilot_evidence
from .copilot_design import badge, design

def render_copilot_workspace_header(state):
    design()
    status = sync_copilot_evidence(state)
    frame, target = state.get("dataset"), state.get("target")
    has_dataset = frame is not None and bool(target) and target in frame.columns
    active = state.get("copilot_workspace_path", "goal")
    if active not in {"goal", "historical", "dataset"}:
        active = "goal"
    st.markdown('<div class="cop-hero"><div class="cop-kicker">AwareML decision support</div><h1>From deployment goal to informed choice</h1><div class="cop-lead">Set your priorities, compare the evidence and choose how to proceed. Start with a goal, explore development results, or get a recommendation for your dataset.</div></div>', unsafe_allow_html=True)
    cards = [
        ("goal", "01", "Goal interpretation", "Turn your deployment goal into objective weights and human oversight requirements.", "Available", True),
        ("historical", "02", "Historical Preference Prior", "Compare frameworks using development results and your priorities. No dataset needed.", "Available" if status["ready"] else "Connect development evidence", status["ready"]),
        ("dataset", "03", "Dataset-aware ML Recommender", "Rank frameworks using your dataset’s first labeled observations and your priorities.", "Ready" if status["ready"] and has_dataset else "Add a dataset and target" if status["ready"] else "Connect trained models", status["ready"] and has_dataset)]
    for column, (key, number, title, copy, readiness, ready) in zip(st.columns(3), cards):
        with column:
            with st.container(border=True):
                st.markdown('<div class="cop-path-label">{} · {}</div><div class="cop-path-title">{}</div><div class="cop-path-copy">{}</div>'.format(number, "SELECTED" if active == key else "EXPLORE", escape(title), escape(copy)), unsafe_allow_html=True)
                badge(readiness, ready=ready, waiting=not ready)
                if st.button("Open " + title, key="copilot_workspace_open_" + key, use_container_width=True, type="primary" if active == key else "secondary"):
                    state["copilot_workspace_path"] = key; st.rerun()
    context = ("{} · Target: {}".format(state.get("dataset_name") or "Loaded dataset", target)
        if has_dataset else "No dataset selected · Goal interpretation and connected historical evidence remain available")
    st.caption(context)
    return active

def render_goal_framework_guidance(state, interpretation, proposal=None):
    from .copilot_recommender import render_current_goal_guidance
    return render_current_goal_guidance(state, interpretation, proposal)


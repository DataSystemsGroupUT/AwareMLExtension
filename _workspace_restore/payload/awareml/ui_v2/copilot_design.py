"""Shared rendering of the established Copilot workflow."""
from html import escape
import streamlit as st

def render_goal_steps():
    st.markdown("## How Goal Copilot works")
    rows=[
        ("01","Understand","AwareML interprets your deployment goal and identifies the objectives implied by the wording."),
        ("02","Weight","Review the objectives, their initial equal weights and the separate oversight requirements."),
        ("03","Predict","Compare development evidence or use a labeled dataset prefix to predict framework outcomes."),
        ("04","You decide","Inspect the interpretation and recommendation, then approve, adjust or reject the plan.")]
    for col,(number,title,copy) in zip(st.columns(4),rows):
        with col:
            st.markdown('<div class="awareml-flow-card"><div class="awareml-step">{}</div><div class="awareml-card-title">{}</div><div class="awareml-card-copy">{}</div></div>'.format(number,escape(title),escape(copy)),unsafe_allow_html=True)
    st.caption("Responsibility boundary: the LLM interprets the goal; the recommender ranks frameworks; the human makes the final decision.")

def asset_connection(status):
    from .recommender_assets import activate_assets, asset_settings
    from .recommender_bridge import historical_status
    with st.expander("Recommender setup",expanded=False):
        st.caption("Experiment packages in artifacts/dashboard_evidence are detected automatically.")
        if status.get("ready"):
            st.success("Current experiment evidence is available.")
        elif historical_status(status.get("directory") or None)["ready"]:
            st.success("Development results and historical comparison are available.")
            st.caption("Import the trained model package from Rocket to enable dataset-aware predictions.")
        else:
            st.caption("Place the exported model and report folders on this computer to populate the result panels.")
        advanced=st.checkbox("Advanced folder settings",key="cop_assets_advanced")
        if not advanced:return
        try:settings=asset_settings()
        except Exception as exc:st.error(str(exc));settings={}
        bundle=st.text_input("Trained model folder",value=settings.get("bundle",status.get("directory","")),key="cop_assets_bundle")
        development=st.text_input("Development evaluation folder (optional)",value=settings.get("development",""),key="cop_assets_development")
        external=st.text_input("External evaluation folder (optional)",value=settings.get("external",""),key="cop_assets_external")
        if st.button("Validate and connect",key="cop_assets_connect"):
            try:
                activate_assets(bundle,development or None,external or None);st.rerun()
            except Exception as exc:st.error(str(exc))


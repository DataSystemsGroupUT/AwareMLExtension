"""Shared presentation for the three Copilot paths."""
from html import escape
import streamlit as st

CSS = """<style>
.cop-hero{padding:12px 0 25px;border-bottom:1px solid rgba(148,163,184,.25);margin-bottom:22px}
.cop-kicker{font-size:.72rem;letter-spacing:.13em;font-weight:700;text-transform:uppercase;color:#4979cd;margin-bottom:8px}
.cop-hero h1{font-size:2.2rem;line-height:1.15;letter-spacing:-.045em;margin:0 0 12px;padding:0;font-weight:750;color:inherit}
.cop-lead{font-size:.96rem;line-height:1.65;max-width:850px;opacity:.78}
.cop-path-label{font-size:.75rem;font-weight:700;letter-spacing:.04em;opacity:.6;margin:4px 0 8px}
.cop-path-title{font-size:1.1rem;font-weight:700;line-height:1.3;min-height:44px;margin-bottom:8px}
.cop-path-copy{font-size:.86rem;line-height:1.55;opacity:.77;min-height:64px;margin-bottom:16px}
.cop-status{display:inline-flex;align-items:center;gap:7px;border-radius:20px;padding:4px 10px;background:rgba(100,116,139,.10);font-size:.75rem;font-weight:650;margin-bottom:12px;color:inherit}
.cop-status.ready{background:rgba(22,163,74,.10);color:#16834a}.cop-status.wait{background:rgba(217,119,6,.10);color:#a7640b}
.cop-status .dot{height:6px;width:6px;border-radius:50%;background:currentColor}
.cop-section{margin:24px 0 14px}.cop-section h2{font-size:1.7rem;letter-spacing:-.025em;margin:0 0 8px;padding:0;color:inherit}
.cop-section p{font-size:.94rem;line-height:1.65;opacity:.78;margin:0;max-width:900px}
.cop-result{padding:18px 0 20px}.cop-result-label{font-size:.74rem;text-transform:uppercase;letter-spacing:.08em;opacity:.6}
.cop-result-value{font-size:2rem;font-weight:750;letter-spacing:-.035em;margin:4px 0}
.cop-result-copy{font-size:.88rem;line-height:1.6;opacity:.78}
div[data-testid="stButton"] button[kind="primary"]{background:#275fce;color:#fff;border:1px solid #275fce;min-height:44px;font-weight:650;border-radius:10px}
div[data-testid="stButton"] button[kind="primary"]:hover{background:#2152bd;border-color:#2152bd;color:#fff}
div[data-testid="stButton"] button:focus-visible{outline:3px solid #8bb4ff;outline-offset:3px}
@media(max-width:900px){.cop-path-copy,.cop-path-title{min-height:0}.cop-hero h1{font-size:1.8rem}}
</style>"""

def design():
    st.markdown(CSS, unsafe_allow_html=True)

def section(title, copy):
    st.markdown('<div class="cop-section"><h2>{}</h2><p>{}</p></div>'.format(escape(title), escape(copy)), unsafe_allow_html=True)

def badge(text, ready=False, waiting=False):
    cls = "ready" if ready else "wait" if waiting else ""
    st.markdown('<div class="cop-status {}"><span class="dot"></span>{}</div>'.format(cls, escape(text)), unsafe_allow_html=True)

def recommendation(label, framework, copy):
    st.markdown('<div class="cop-result"><div class="cop-result-label">{}</div><div class="cop-result-value">{}</div><div class="cop-result-copy">{}</div></div>'.format(escape(label), escape(framework), escape(copy)), unsafe_allow_html=True)

def render_goal_steps():
    with st.expander("How your goal becomes a recommendation", expanded=False):
        for col, (title, copy) in zip(st.columns(4), [
            ("01  Interpret", "Identify Accuracy, Runtime, Energy and CO₂ priorities from your goal."),
            ("02  Review", "Review the objective weights and oversight requirements."),
            ("03  Compare", "Use development evidence or a dataset profile to compare frameworks."),
            ("04  Decide", "Inspect the evidence, then approve, adjust or reject the plan.")]):
            with col:
                st.markdown("**" + title + "**"); st.caption(copy)
        st.caption("The language model interprets your goal. The recommender ranks frameworks. You make the final decision.")

def asset_connection(status):
    from .recommender_assets import activate_assets, asset_settings
    with st.expander("Connect models and evaluation reports", expanded=False):
        st.caption("Choose local folders downloaded from your completed experiment. Use model files from your own trusted training run.")
        try:
            settings = asset_settings()
        except Exception as exc:
            st.error(str(exc)); settings = {}
        bundle = st.text_input("Trained model folder", value=settings.get("bundle", status.get("directory", "")), key="cop_assets_bundle")
        development = st.text_input("Development evaluation folder (optional)", value=settings.get("development", ""), key="cop_assets_development")
        external = st.text_input("External evaluation folder (optional)", value=settings.get("external", ""), key="cop_assets_external")
        if st.button("Validate and connect", key="cop_assets_connect"):
            try:
                activate_assets(bundle, development or None, external or None)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        st.caption("Connected files are checked before use. Missing local files do not mean that your experiment must be repeated.")


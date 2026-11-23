"""Development evidence and dataset-specific recommendations in Copilot."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st
from .recommender_bridge import (OBJECTIVES, bundle_status, evaluation_evidence,
    historical_prior, load_current_recommender, normalize_weights)
from .copilot_design import asset_connection, design, recommendation, section

LABELS = {"accuracy": "Accuracy", "runtime": "Runtime", "energy": "Energy", "co2": "CO₂"}

def _labels(frame):
    frame = frame.copy()
    frame["framework_label"] = frame.framework.replace({"ChaCha": "ChaCha-OVR"})
    return frame

def render_pending(status):
    if status["state"] == "invalid_bundle":
        st.error(status["message"])
    else:
        st.info("Connect your completed experiment’s model folder to enable framework rankings here. Goal interpretation is available now.")
    asset_connection(status)

def render_training_cards(status):
    if not status["ready"]:
        return
    values = [("Development datasets", status["development_datasets"]),
              ("Completed benchmark runs", status["underlying_runs"]),
              ("Frameworks", status["framework_count"]),
              ("Seeds per dataset / framework", len(status["seeds"]))]
    for column, (label, value) in zip(st.columns(4), values):
        column.metric(label, "{:,}".format(value))

def render_protocol(status):
    if status["ready"]:
        names = ["ChaCha-OVR" if f == "ChaCha" else f for f in status["manifest"]["frameworks"]]
        st.caption("Framework portfolio: " + " · ".join(names))

def render_development_results(status):
    with st.expander('Development benchmark results', expanded=False):
        try:
            frame=pd.read_csv(Path(status['directory'])/'development_aggregates.csv')
            columns=[c for c in ('dataset_id','framework','seed_count') if c in frame]
            for metric in ('accuracy','f1_macro','runtime_sec','energy_kwh','co2_kg','peak_process_tree_rss_mib'):
                columns.extend(c for c in (metric+'_mean',metric+'_std') if c in frame)
            st.caption('Seed-aggregated outcomes for each development dataset and framework. Column names retain the original units; standard deviations are shown where exported.')
            st.dataframe(frame[columns],use_container_width=True,hide_index=True)
            st.download_button('Download development results',frame.to_csv(index=False).encode('utf-8'),
                file_name='AwareML_Development_Results.csv',mime='text/csv',key='cop_development_download')
        except Exception as exc:
            st.warning(str(exc))

def render_validation(status):
    if not status["ready"]:
        return
    with st.expander("Recommendation performance", expanded=False):
        for kind, title in [("development", "Development validation"), ("external", "External evaluation")]:
            st.markdown("**" + title + "**")
            try:
                evidence = evaluation_evidence(kind, status["directory"])
                if evidence is None:
                    st.caption("Connect this evaluation report to display its results."); continue
                meta = evidence["metadata"]
                st.caption("{} datasets · {:,} preference cases per method".format(meta["n_datasets"], meta["n_preference_cases_per_method"]))
                table = pd.read_csv(Path(evidence["directory"]) / "baseline_summary.csv")
                st.dataframe(table, use_container_width=True, hide_index=True)
            except Exception as exc:
                st.warning(str(exc))
        st.caption("Each dataset is the statistical unit. External outcomes are used for evaluation, not model fitting.")
    asset_connection(status)

def _weight_controls(prefix):
    with st.container(border=True):
        st.markdown("**Your objective priorities**")
        st.caption("Move the sliders to express relative importance. Weights are normalized automatically.")
        values = {}
        for column, key in zip(st.columns(4), OBJECTIVES):
            values[key] = column.slider(LABELS[key], 0, 100, 25, key=prefix + key)
        if sum(values.values()) <= 0:
            st.warning("Give at least one objective a positive weight."); return None
        weights = normalize_weights(values)
        st.caption(" · ".join("{} {:.0%}".format(LABELS[k], weights[k]) for k in OBJECTIVES))
        return weights

def render_historical_preference_prior_tab():
    design()
    section("Historical Preference Prior", "Explore which frameworks performed well across the development datasets under your priorities. This starting point does not require an uploaded dataset.")
    status = bundle_status()
    if not status["ready"]:
        render_pending(status); return
    render_training_cards(status); render_protocol(status)
    weights = _weight_controls("current_prior_")
    if weights is None: return
    try:
        ranked, _ = historical_prior(weights, status["directory"]); ranked = _labels(ranked)
    except Exception as exc:
        st.error(str(exc)); return
    recommendation("Development evidence suggests", ranked.iloc[0].framework_label,
        "A global starting point based on seed-averaged development outcomes. It is not a prediction for your dataset.")
    table = ranked[["rank", "framework_label", "historical_utility", "win_count", "support_datasets"]].rename(columns={
        "rank": "Rank", "framework_label": "Framework", "historical_utility": "Mean preference score",
        "win_count": "Dataset wins", "support_datasets": "Supporting datasets"})
    st.dataframe(table, use_container_width=True, hide_index=True)
    with st.expander("How the historical comparison works", expanded=False):
        st.write("Each dataset–framework outcome is averaged over the declared seeds. Your weights determine utility within each dataset; those utilities are averaged across development datasets. The preference score is not a probability. Tied winners are all counted.")
    render_development_results(status)
    render_validation(status)

def render_dataset_aware_tab():
    from .state import ensure_research_state
    design(); state = ensure_research_state()
    section("Dataset-aware ML Recommender", "Compare predicted framework outcomes for your dataset, using its first labeled observations and the priorities you choose. You remain in control of the final choice.")
    status = bundle_status()
    if not status["ready"]:
        render_pending(status); return
    render_training_cards(status); render_protocol(status)
    frame, target = state.get("dataset"), state.get("target")
    if frame is None or not target or target not in frame.columns:
        st.info("Load a labeled classification dataset and select its target in Run Studio. That dataset is shared with this workspace.")
        render_validation(status); return
    cap = int(status["manifest"]["profile_size"])
    st.caption("{} · Target: {} · Profiling up to {:,} labeled observations".format(state.get("dataset_name") or "Loaded dataset", target, cap))
    weights = _weight_controls("current_dataset_")
    if weights is None: return
    try:
        ranked, meta = load_current_recommender(status["directory"]).recommend_dataframe(frame, target, weights)
        ranked = _labels(ranked)
    except Exception as exc:
        st.error("The dataset could not be profiled: " + str(exc)); return
    recommendation("Recommended for your dataset", ranked.iloc[0].framework_label,
        "Learned objective models produce this ranking. The language model may explain the evidence, while the framework choice remains yours.")
    table = ranked[["rank", "framework_label", "utility", "accuracy", "runtime", "energy", "co2"]].copy()
    table["accuracy"] = table.accuracy * 100
    table = table.rename(columns={"rank": "Rank", "framework_label": "Framework", "utility": "Preference score",
        "accuracy": "Predicted accuracy (%)", "runtime": "Runtime (s)", "energy": "Energy (kWh)", "co2": "CO₂ (kg)"})
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption("All values above are predictions. Preference scores compare the available frameworks; they are not confidence scores.")
    with st.expander("Inspect the dataset profile and prediction intervals", expanded=False):
        profile = meta.get("profile", {})
        st.dataframe(pd.DataFrame([{"Profile feature": k.replace("_", " ").capitalize(), "Value": str(v)} for k, v in profile.items()]), use_container_width=True, hide_index=True)
        interval_columns = ["framework_label"] + [c for k in OBJECTIVES for c in (k + "_lower", k + "_upper") if c in ranked.columns]
        if len(interval_columns) > 1:
            st.dataframe(ranked[interval_columns], use_container_width=True, hide_index=True)
            st.caption("Intervals reflect development residuals; their observed external coverage is reported separately.")
    render_development_results(status)
    render_validation(status)

def render_current_goal_guidance(state, interpretation, proposal=None):
    st.markdown("## Framework guidance")
    status = bundle_status()
    if not status["ready"]:
        st.caption("Your goal can be interpreted and reviewed now. Connect trained models to add framework guidance."); return
    data = interpretation.model_dump() if hasattr(interpretation, "model_dump") else dict(interpretation or {})
    weights = state.get("copilot_human_corrected_weights") or data.get("primary_weights") or {}
    if hasattr(weights, "normalized_dict"): weights = weights.normalized_dict()
    try:
        ranked, _ = historical_prior(weights, status["directory"]); ranked = _labels(ranked)
        recommendation("Historical starting point", ranked.iloc[0].framework_label, "Based on development evidence and the current priorities.")
        if proposal is not None:
            data = proposal.model_dump() if hasattr(proposal, "model_dump") else dict(proposal)
            value = data.get("ml_recommender_framework", "Unavailable")
            recommendation("Dataset-aware recommendation", "ChaCha-OVR" if value == "ChaCha" else value, "Based on the observed dataset profile and the current priorities.")
        with st.expander("Historical alternatives", expanded=False):
            st.dataframe(ranked, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.warning(str(exc))


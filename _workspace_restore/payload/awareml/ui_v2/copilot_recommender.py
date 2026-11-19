"""Earlier Copilot presentation backed by current development and prefix-model evidence."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from .recommender_bridge import (OBJECTIVES, bundle_status, historical_status, evaluation_evidence, historical_prior,
    load_current_recommender, normalize_weights)
from .framework_labels import framework_label, display_frame, display_figure

LABELS={"accuracy":"Accuracy","runtime":"Runtime","energy":"Energy","co2":"CO₂"}
PRESETS={
    "Accuracy first":{"accuracy":55,"runtime":15,"energy":15,"co2":15},
    "Balanced":{"accuracy":25,"runtime":25,"energy":25,"co2":25},
    "Fast response":{"accuracy":25,"runtime":50,"energy":15,"co2":10},
    "Low energy":{"accuracy":25,"runtime":15,"energy":50,"co2":10},
    "Low CO₂":{"accuracy":25,"runtime":15,"energy":10,"co2":50}}
DATASET_PRESETS={
    "Balanced":{"accuracy":25,"runtime":25,"energy":25,"co2":25},
    "Accuracy focused":{"accuracy":70,"runtime":10,"energy":10,"co2":10},
    "Runtime focused":{"accuracy":10,"runtime":70,"energy":10,"co2":10},
    "Energy focused":{"accuracy":10,"runtime":10,"energy":70,"co2":10},
    "CO₂ focused":{"accuracy":10,"runtime":10,"energy":10,"co2":70},
    "Sustainability":{"accuracy":20,"runtime":10,"energy":35,"co2":35}}
COLORS={"AutoStreamML":"#2563eb","AutoClass":"#16a34a","EvoAutoML":"#ea580c","OAML":"#ca8a04","ChaCha-OVR":"#9333ea"}

def _weights_text(weights):
    return " · ".join("{} {:.0%}".format(LABELS[k],weights[k]) for k in OBJECTIVES)

def _latest_weights(state):
    override=state.get("copilot_human_corrected_weights")
    if override:return normalize_weights(override)
    item=state.get("copilot_context_free_interpretation") or state.get("copilot_proposal")
    if hasattr(item,"model_dump"):item=item.model_dump()
    if isinstance(item,dict):
        data=item.get("interpretation",item)
        if hasattr(data,"model_dump"):data=data.model_dump()
        if data.get("primary_weights"):return normalize_weights(data["primary_weights"])
    return None

def _set_weights(prefix,values):
    for key in OBJECTIVES:st.session_state[prefix+key]=int(round(float(values[key])*100)) if sum(values.values())<2 else int(values[key])

def _weight_controls(prefix,state=None,presets=None):
    presets=presets or PRESETS
    latest=_latest_weights(state or {})
    if latest and st.button("Use latest Goal Copilot priorities",key=prefix+"goal"):
        _set_weights(prefix,latest);st.rerun()
    for col,(name,values) in zip(st.columns(len(presets)),presets.items()):
        if col.button(name,key=prefix+"preset_"+name,use_container_width=True):
            _set_weights(prefix,values);st.rerun()
    raw={}
    for col,key in zip(st.columns(4),OBJECTIVES):
        st.session_state.setdefault(prefix+key,25)
        raw[key]=col.slider(LABELS[key]+(" ↑" if key=="accuracy" else " ↓"),0,100,key=prefix+key)
    if not sum(raw.values()):
        st.warning("Give at least one objective a positive weight.");return None
    weights=normalize_weights(raw)
    st.info("Normalized priorities: "+_weights_text(weights))
    return weights

def render_pending(status):
    history=historical_status(status.get('directory') or None)
    if history['ready']:
        st.info("The development and external results are available locally. Copy AwareML_Dashboard_Evidence.zip from Rocket and import it to enable live dataset-aware recommendations.")
        return
    if status["state"]=="invalid_bundle":st.error(status["message"])
    else:st.info("The experiment files are not available on this computer yet. Add the exported evidence package through Recommender setup in the sidebar.")

def render_training_cards(status,dataset_view=False):
    if dataset_view:
        external="—"
        if status["ready"]:
            try:
                evidence=evaluation_evidence("external",status["directory"])
                if evidence:external=evidence["metadata"]["n_datasets"]
            except Exception:pass
        values=[("Development datasets",status.get("development_datasets","—")),
                ("Training profiles",status.get("training_rows","—")),
                ("Underlying runs",status.get("underlying_runs","—")),("External evaluation datasets",external)]
    else:
        values=[("Historical runs",status.get("underlying_runs","—")),("Development datasets",status.get("development_datasets","—")),
                ("Frameworks",status.get("framework_count","—")),("Seeds per dataset/framework",len(status["seeds"]) if status["ready"] else "—")]
    for col,(label,value) in zip(st.columns(4),values):col.metric(label,"{:,}".format(value) if isinstance(value,int) else value)

def render_protocol(status):
    if status["ready"]:st.caption("Framework portfolio: "+" · ".join(framework_label(f) for f in status["manifest"]["frameworks"]))

def render_development_results(status):
    if not status['ready']:return
    with st.expander("Completed development benchmark results",expanded=False):
        frame=pd.read_csv(Path(status["directory"])/"development_aggregates.csv")
        columns=[c for c in ("dataset_id","framework","seed_count") if c in frame]
        for key in ("accuracy","f1_macro","runtime_sec","energy_kwh","co2_kg","peak_process_tree_rss_mib"):
            columns.extend(c for c in (key+"_mean",key+"_std") if c in frame)
        st.caption("Each row contains seed-aggregated outcomes for one dataset and framework. Standard deviations are shown when exported.")
        st.dataframe(display_frame(frame[columns]),use_container_width=True,hide_index=True)
        st.download_button("Download development results",frame.to_csv(index=False).encode("utf-8"),
            file_name="AwareML_Development_Results.csv",mime="text/csv",key="cop_development_download")

def render_validation(status):
    if not status['ready']:return
    with st.expander("Development validation and external evaluation",expanded=False):
        for kind,title in (("development","Nested LODO on development datasets"),("external","External classification evaluation")):
            st.markdown("**"+title+"**")
            try:
                evidence=evaluation_evidence(kind,status["directory"])
                if not evidence:
                    st.caption("This evaluation report is not installed locally.");continue
                meta=evidence["metadata"]
                st.caption("{} datasets · {:,} preference cases per method · Statistical unit: dataset.".format(meta["n_datasets"],meta["n_preference_cases_per_method"]))
                table=pd.read_csv(Path(evidence["directory"])/"baseline_summary.csv")
                if "method" in table:table["method"]=table["method"].replace({"V3":"AwareML"})
                st.dataframe(display_frame(table),use_container_width=True,hide_index=True)
            except Exception as exc:st.warning(str(exc))

def _ranking_chart(frame,score,key,title):
    view=display_frame(frame)
    chart=view.sort_values(score,ascending=True,kind="stable")
    fig=px.bar(chart,x=score,y="framework",orientation="h",text=score,color="framework",
        color_discrete_map=COLORS,title=title)
    fig.update_traces(texttemplate="%{text:.3f}",textposition="inside")
    fig.update_layout(height=330,showlegend=False,yaxis_title=None,xaxis_title="Preference score",margin=dict(l=15,r=20,t=50,b=35))
    st.plotly_chart(fig,use_container_width=True,key=key)

def _historical_summary(ranked,status):
    top=ranked.iloc[0]
    cards=st.columns(4)
    cards[0].metric("Historical starting point",framework_label(top.framework))
    cards[1].metric("Historical rank","#1 of {}".format(len(ranked)))
    cards[2].metric("Cross-dataset preference score","{:.3f}".format(top.historical_utility))
    cards[3].metric("Dataset wins","{} / {}".format(int(top.win_count),int(top.support_datasets)))

def render_historical_preference_prior_tab():
    from .state import ensure_research_state
    state=ensure_research_state();status=historical_status()
    st.markdown("# Historical Preference Prior")
    st.markdown("Use this when **no dataset is available yet**. Compare what worked across the development datasets under your current priorities.")
    st.info("**Historical aggregation · not machine learning.** This is a global starting point, not a prediction for your dataset.")
    render_training_cards(status)
    st.markdown("## 1 · Choose what matters")
    weights=_weight_controls("current_prior_",state)
    if status["ready"]:
        st.success("Stable {}-seed aggregate: each dataset/framework is represented by the mean of seeds {}.".format(len(status["seeds"]),"/".join(map(str,status["seeds"]))))
    st.markdown("## 2 · Compare the historical evidence")
    if not status["ready"]:
        render_pending(status);return
    if weights is None:return
    signature=status["evidence_id"]+json.dumps(weights,sort_keys=True)
    if st.button("Compare frameworks across {:,} historical runs".format(status["underlying_runs"]),key="three_hist_run",type="primary",use_container_width=True):
        ranked,_=historical_prior(weights,status["directory"])
        state["current_historical_result"]={"signature":signature,"ranking":ranked}
    result=state.get("current_historical_result") or {}
    ranked=result.get("ranking")
    if result.get("signature")==signature and isinstance(ranked,pd.DataFrame) and not ranked.empty:
        st.markdown("## Historical Framework Starting Point")
        _historical_summary(ranked,status)
        st.write("**Why this starting point?** {} has the highest mean within-dataset utility across the development datasets under {}.".format(framework_label(str(ranked.iloc[0].framework)),_weights_text(weights)))
        view=ranked[["rank","framework","historical_utility","win_rate","top3_rate","accuracy_median","runtime_median","energy_median","co2_median"]].rename(columns={"rank":"Rank","framework":"Framework","historical_utility":"Cross-dataset preference score","win_rate":"Win rate","top3_rate":"Top-3 rate","accuracy_median":"Median accuracy","runtime_median":"Median runtime (s)","energy_median":"Median energy (kWh)","co2_median":"Median CO₂ (kg)"})
        st.dataframe(display_frame(view),use_container_width=True,hide_index=True)
        _ranking_chart(ranked,"historical_utility","three_hist_chart","Cross-dataset preference ranking")
        with st.expander("Preference sensitivity",expanded=False):
            rows=[]
            for name,values in PRESETS.items():
                alt,_=historical_prior(values,status["directory"])
                rows.append({"Profile":name,"Starting point":framework_label(str(alt.iloc[0].framework)),"Preference score":float(alt.iloc[0].historical_utility)})
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.caption("Scores are mean within-dataset utilities, not probabilities. All tied dataset winners are counted.")
    elif result:st.caption("Your priorities changed. Compare again to update the ranking.")
    render_protocol(status);render_development_results(status);render_validation(status)

def render_dataset_aware_tab():
    from .state import ensure_research_state
    state=ensure_research_state();status=bundle_status()
    history=historical_status(status.get('directory') or None)
    st.markdown("# Dataset-aware ML Recommender")
    st.markdown("Use this when a **dataset and target are available**. The learned objective models use the observed labeled prefix to rank the five frameworks before framework execution.")
    st.success("**Dataset-aware model inference.** The models produce the framework ranking; the LLM may explain it afterwards. You make the final decision.")
    render_training_cards(history,True)
    frame,target=state.get("dataset"),state.get("target")
    if frame is None or not target or target not in frame.columns:
        st.info("Load a labeled classification dataset and choose its target in Run Studio.")
        if not status['ready']:render_pending(status)
        render_validation(history)
        return
    st.markdown("## 1 · Dataset context")
    size=int(status.get("manifest",{}).get("profile_size",1000));prefix=frame.iloc[:size]
    cols=st.columns(4)
    for col,(name,value) in zip(cols,[("Dataset",state.get("dataset_name") or "Loaded dataset"),("Observed prefix",len(prefix)),("Predictor columns",max(0,len(prefix.columns)-1)),("Target",str(target))]):col.metric(name,value)
    st.caption("Profiling uses up to the first {:,} labeled observations. Unobserved stream values are not used.".format(size))
    st.markdown("## 2 · Choose your preferences")
    weights=_weight_controls("current_dataset_",state,DATASET_PRESETS)
    detail=st.radio("Prediction detail",["Point estimates","Empirical intervals"],horizontal=True,key="current_prediction_detail") or "Point estimates"
    st.markdown("## 3 · Predict the five-framework ranking")
    if not status["ready"]:
        st.button("Generate dataset-aware recommendation",key="three_dataset_run",type="primary",use_container_width=True,disabled=True)
        render_pending(status);render_development_results(history);render_validation(history);return
    if weights is None:return
    signature=hashlib.sha256((status["evidence_id"]+str(target)+prefix.to_csv(index=False)+json.dumps(weights,sort_keys=True)).encode()).hexdigest()
    if st.button("Generate dataset-aware recommendation",key="three_dataset_run",type="primary",use_container_width=True):
        try:
            ranked,meta=load_current_recommender(status["directory"]).recommend_dataframe(frame,target,weights)
            state["current_dataset_result"]={"signature":signature,"ranking":ranked,"meta":meta}
        except Exception as exc:st.error("Dataset-aware inference unavailable: "+str(exc))
    result=state.get("current_dataset_result") or {};ranked=result.get("ranking")
    if result.get("signature")==signature and isinstance(ranked,pd.DataFrame) and not ranked.empty:
        meta=result["meta"];top=ranked.iloc[0]
        from .copilot_diagnostics import pareto_flags, render_dataset_diagnostics
        ranked=ranked.copy();ranked['near_pareto']=pareto_flags(ranked,weights)
        top=ranked.iloc[0]
        st.markdown("## Dataset-specific pre-execution recommendation")
        cols=st.columns(4)
        for col,(name,value) in zip(cols,[("Predicted framework",framework_label(str(top.framework))),("Predicted rank","#1 of {}".format(len(ranked))),("Normalized preference utility","{:.4f}".format(float(top.utility))),("Pareto candidate","Yes" if top.near_pareto else "No")]):col.metric(name,value)
        st.info("The recommender predicts **{}** under **{}**. These are estimates for this dataset, not observed framework-run outcomes.".format(framework_label(str(top.framework)),_weights_text(weights)))
        columns=["rank","framework","utility","near_pareto","accuracy","runtime","energy","co2"]
        if detail=="Empirical intervals":columns.extend(c for k in OBJECTIVES for c in (k+"_lower",k+"_upper") if c in ranked)
        view=ranked[columns].copy()
        view["accuracy"]=view["accuracy"]*100
        if "accuracy_lower" in view:
            view["accuracy_lower"]*=100;view["accuracy_upper"]*=100
        view=view.rename(columns={"rank":"Rank","framework":"Framework","utility":"Preference utility","accuracy":"Predicted accuracy (%)","runtime":"Runtime (s)","energy":"Energy (kWh)","co2":"CO₂ (kg)","accuracy_lower":"Accuracy lower (%)","accuracy_upper":"Accuracy upper (%)"})
        st.dataframe(display_frame(view),use_container_width=True,hide_index=True)
        _ranking_chart(ranked,"utility","three_dataset_chart","Dataset-aware preference ranking")
        st.caption("Utility is a relative score, not confidence. Empirical intervals describe development residuals; external coverage is reported separately.")
        cards=st.columns(3)
        proposal=state.get('copilot_proposal')
        item=proposal.model_dump() if hasattr(proposal,'model_dump') else dict(proposal or {})
        cards[0].metric('Goal Copilot',framework_label(item.get('ml_recommender_framework') or 'Not generated'))
        prior,_=historical_prior(weights,status['directory'])
        cards[1].metric('Historical prior',framework_label(str(prior.iloc[0].framework)))
        cards[2].metric('Dataset-aware recommender',framework_label(str(top.framework)))
        render_dataset_diagnostics(state,ranked,weights,meta,signature,status['evidence_id'])
        with st.expander("Observed dataset profile",expanded=False):
            st.dataframe(pd.DataFrame([{"Feature":k.replace("_"," ").title(),"Value":str(v)} for k,v in meta["profile"].items()]),use_container_width=True,hide_index=True)
    elif result:st.caption("The dataset prefix or priorities changed. Generate a recommendation again to update the result.")
    render_protocol(history);render_development_results(history);render_validation(history)

def render_current_goal_guidance(state,interpretation,proposal=None):
    st.markdown("## 2 · Compare the available evidence paths")
    status=historical_status()
    if not status["ready"]:
        st.caption("The goal interpretation can be reviewed now. Add the development results to enable historical comparison.");return
    data=interpretation.model_dump() if hasattr(interpretation,"model_dump") else dict(interpretation or {})
    weights=state.get("copilot_human_corrected_weights") or data.get("primary_weights") or {}
    if hasattr(weights,"normalized_dict"):weights=weights.normalized_dict()
    try:
        ranked,_=historical_prior(weights,status["directory"])
        item=proposal.model_dump() if hasattr(proposal,"model_dump") else dict(proposal or {})
        winner=str(ranked.iloc[0].framework);predicted=item.get('ml_recommender_framework')
        cols=st.columns(3)
        from .components import metric_card
        with cols[0]:metric_card('GLOBAL HISTORICAL PRIOR',framework_label(winner),'{} datasets · {:,} runs · preference score {:.3f}'.format(status['development_datasets'],status['underlying_runs'],float(ranked.iloc[0].historical_utility)))
        with cols[1]:metric_card('DATASET-AWARE ML RECOMMENDER',framework_label(str(predicted)) if predicted else 'Dataset + models required','Ranking utility {:.4f}'.format(float(item['ml_recommender_utility'])) if item.get('ml_recommender_utility') is not None else 'Labeled prefix · learned objective models')
        relation='Agreement' if predicted==winner else 'Different recommendations' if predicted else 'Historical evidence available'
        with cols[2]:metric_card('EVIDENCE RELATIONSHIP',relation,_weights_text(normalize_weights(weights)))
        if predicted==winner:st.success('Historical and dataset-aware evidence both favor **{}**. Their scores use different evidence and should not be compared directly.'.format(framework_label(winner)))
        elif predicted:st.info('The historical prior favors **{}**; the dataset-aware model favors **{}** for this observed prefix.'.format(framework_label(winner),framework_label(str(predicted))))
        with st.expander("Compare the historical alternatives",expanded=False):
            st.dataframe(display_frame(ranked),use_container_width=True,hide_index=True)
    except Exception as exc:st.warning(str(exc))


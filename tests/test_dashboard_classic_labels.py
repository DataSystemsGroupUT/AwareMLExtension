"""Presentation and current-evidence regression tests; all data are synthetic."""
import importlib.util
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from streamlit.testing.v1 import AppTest
from awareml.ui_v2.framework_labels import framework_label,display_frame,display_figure
from awareml.ui_v2 import recommender_assets as assets
from awareml.ui_v2 import recommender_bridge as bridge
from test_copilot_current_protocol import make_bundle,frame

def patcher():
    p=Path(__file__).resolve().parents[1]/'scripts/patch_dashboard_labels.py'
    spec=importlib.util.spec_from_file_location('labels_patch_test',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def test_label_and_table_copy_preserve_identifiers():
    original=pd.DataFrame({'framework':['ChaCha','OAML'],'accuracy':[.7,.8],'seed':[42,43]})
    before=original.copy(deep=True)
    shown=display_frame(original)
    assert shown.framework.tolist()==['ChaCha-OVR','OAML']
    pd.testing.assert_frame_equal(original,before)
    assert shown.accuracy.tolist()==before.accuracy.tolist()
    assert framework_label('ChaCha-OVR')=='ChaCha-OVR'

def test_chart_copy_changes_labels_only():
    fig=go.Figure(go.Bar(name='ChaCha',y=['ChaCha','OAML'],x=[.2,.4],customdata=['ChaCha','OAML']))
    before=fig.to_json();shown=display_figure(fig)
    assert shown.data[0].name=='ChaCha-OVR'
    assert list(shown.data[0].y)==['ChaCha-OVR','OAML']
    assert list(shown.data[0].customdata)==['ChaCha','OAML']
    assert list(shown.data[0].x)==[.2,.4]
    assert fig.to_json()==before

def test_selector_formats_label_but_returns_canonical_name():
    source='import streamlit as st\nst.session_state["selected"] = st.multiselect("Frameworks", ["ChaCha", "OAML"], default=["ChaCha"])\n'
    revised=patcher().patch_source(source)
    app=AppTest.from_string(revised).run(timeout=30)
    assert not app.exception
    assert app.multiselect[0].options==['ChaCha-OVR','OAML']
    assert app.session_state['selected']==['ChaCha']

def test_framework_tab_caption_and_config_preserved():
    app=AppTest.from_string('import streamlit as st\nfrom awareml.ui_v2.framework_control import render_framework_configuration\nst.session_state["configuration"] = render_framework_configuration(["ChaCha"],state={})').run(timeout=30)
    assert not app.exception
    assert app.tabs[0].label=='ChaCha-OVR'
    assert any('logistic learners and a one-versus-rest wrapper' in x.value for x in app.caption)
    assert set(app.session_state['configuration'])=={'ChaCha'}
    assert app.session_state['configuration']['ChaCha']['algorithms']==['AutoVW']

def test_source_patcher_preserves_unicode_comments_and_is_idempotent():
    source='from __future__ import annotations\nimport streamlit as st\n# Local edits stay here\nst.markdown("CO₂ framework: ChaCha")\nst.dataframe(data)\nc1.metric("Winner", winner)\n'
    revised=patcher().patch_source(source)
    assert '# Local edits stay here' in revised
    assert patcher().patch_source(revised)==revised
    assert 'c1.metric(framework_label(' in revised
    assert 'CO₂ framework: ChaCha' in revised

def test_packaged_current_files_use_classic_workflow():
    root=Path(__file__).resolve().parents[1]
    text=(root/'awareml/ui_v2/copilot_recommender.py').read_text(encoding='utf-8')
    header=(root/'awareml/ui_v2/copilot_workspace_v5.py').read_text(encoding='utf-8')
    assert 'Compare frameworks across' in text
    assert 'Generate dataset-aware recommendation' in text
    assert 'Historical Framework Starting Point' in text
    assert 'copv5-hero' in header and 'copv5-current' in header
    assert 'EXPLORE' not in header
    assert 'load_v2_recommender' not in text

def test_setup_is_sidebar_only_and_closed_by_default(tmp_path,monkeypatch):
    monkeypatch.setenv('AWAREML_RECOMMENDER_BUNDLE',str(tmp_path/'absent'))
    monkeypatch.setattr(assets,'POINTER',tmp_path/'pointer.json')
    app=AppTest.from_string('from awareml.ui_v2.copilot_workspace_v5 import render_copilot_workspace_header\nrender_copilot_workspace_header({})').run(timeout=30)
    assert not app.exception
    assert any(x.label=='Recommender setup' for x in app.sidebar.expander)
    assert not app.text_input
    assert len(app.button)==3

def test_exported_evidence_is_discovered_automatically(tmp_path,monkeypatch):
    local=tmp_path/'artifacts/dashboard_evidence';local.mkdir(parents=True)
    model=make_bundle(local/'models')
    monkeypatch.setattr(assets,'ROOT',tmp_path)
    monkeypatch.setattr(assets,'POINTER',tmp_path/'pointer.json')
    monkeypatch.delenv('AWAREML_RECOMMENDER_BUNDLE',raising=False)
    monkeypatch.delenv('AWAREML_RECOMMENDER_V3_BUNDLE',raising=False)
    assert bridge.bundle_directory()==model.resolve()
    assert bridge.bundle_status()['framework_count']==5

def test_historical_controls_do_not_reuse_stale_result_after_weight_change(tmp_path,monkeypatch):
    model=make_bundle(tmp_path/'model');monkeypatch.setenv('AWAREML_RECOMMENDER_BUNDLE',str(model))
    monkeypatch.setattr(assets,'POINTER',tmp_path/'pointer.json')
    app=AppTest.from_string('from awareml.ui_v2.copilot_recommender import render_historical_preference_prior_tab\nrender_historical_preference_prior_tab()').run(timeout=30)
    assert not any(m.label=='Historical starting point' for m in app.metric)
    app.button(key='three_hist_run').click().run()
    assert any(m.label=='Historical starting point' for m in app.metric)
    app.slider(key='current_prior_accuracy').set_value(100).run()
    assert not any(m.label=='Historical starting point' for m in app.metric)

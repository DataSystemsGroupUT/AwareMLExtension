"""Synthetic fixtures test the UI contract, not experimental performance."""
import json
from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from awareml.protocol_v3.common import PRIMARY
from awareml.ui_v2 import recommender_assets as assets
from awareml.ui_v2 import recommender_bridge as bridge
from test_copilot_current_protocol import make_bundle, frame

@pytest.fixture(autouse=True)
def isolated_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(assets, 'POINTER', tmp_path / 'assets.json')
    for name in ('AWAREML_RECOMMENDER_BUNDLE', 'AWAREML_RECOMMENDER_V3_BUNDLE',
                 'AWAREML_V3_DEVELOPMENT_EVALUATION', 'AWAREML_V3_EXTERNAL_EVALUATION'):
        monkeypatch.delenv(name, raising=False)

@pytest.fixture
def five(tmp_path):
    return make_bundle(tmp_path / 'five', tuple(PRIMARY) + ('ChaCha',))

def app(path, page):
    code = ('import os\nos.environ["AWAREML_RECOMMENDER_BUNDLE"] = ' + repr(str(path)) +
        '\nfrom awareml.ui_v2.copilot_recommender import ' + page + '\n' + page + '()')
    return AppTest.from_string(code)

def visible_text(a):
    return ' '.join(str(x.value) for kind in ('markdown', 'caption', 'info', 'warning', 'error', 'title') for x in getattr(a, kind))

def test_activation_uses_real_five_portfolio_and_preserves_files(five):
    before = {p.name: p.read_bytes() for p in five.iterdir()}
    assets.activate_assets(five)
    assert bridge.bundle_directory() == five.resolve()
    assert bridge.bundle_status()['framework_count'] == 5
    assert before == {p.name: p.read_bytes() for p in five.iterdir()}

def test_failed_activation_preserves_current_connection(five, tmp_path):
    assets.activate_assets(five)
    before = assets.POINTER.read_bytes()
    with pytest.raises(ValueError): assets.activate_assets(tmp_path / 'missing')
    assert assets.POINTER.read_bytes() == before

def test_four_framework_bundle_cannot_replace_five(five, tmp_path):
    assets.activate_assets(five)
    before = assets.POINTER.read_bytes()
    with pytest.raises(ValueError, match='five-framework'):
        assets.activate_assets(make_bundle(tmp_path / 'four', PRIMARY))
    assert assets.POINTER.read_bytes() == before

def test_bad_report_cannot_be_connected(five, tmp_path):
    report = tmp_path / 'report'; report.mkdir()
    (report / 'evaluation.json').write_text(json.dumps({'bundle_manifest_sha256': 'wrong', 'portfolio': 'extended'}), encoding='utf-8')
    with pytest.raises(ValueError, match='does not match'):
        assets.activate_assets(five, external=report)
    assert not assets.POINTER.exists()

def test_missing_models_do_not_claim_training_is_pending(tmp_path):
    a = app(tmp_path / 'missing', 'render_dataset_aware_tab').run(timeout=30)
    assert not a.exception
    assert 'not available' in visible_text(a)
    assert 'training pending' not in visible_text(a).lower()
    assert all(x.value=='—' for x in a.metric)

def test_historical_works_without_dataset_and_weights_change_choice(five):
    a = app(five, 'render_historical_preference_prior_tab').run(timeout=30)
    assert not a.exception
    a.button(key='three_hist_run').click().run()
    assert a.dataframe[0].value.shape[0] == 5
    for k in ('runtime','energy','co2'): a.slider(key='current_prior_' + k).set_value(0)
    a.slider(key='current_prior_accuracy').set_value(100).run()
    a.button(key='three_hist_run').click().run()
    assert 'ChaCha-OVR' in visible_text(a)
    assert a.dataframe[0].value.iloc[0]['Framework'] == 'ChaCha-OVR'
    a.slider(key='current_prior_accuracy').set_value(0)
    a.slider(key='current_prior_runtime').set_value(100).run()
    a.button(key='three_hist_run').click().run()
    assert a.dataframe[0].value.iloc[0]['Framework'] == 'AutoStreamML'

def test_dataset_panel_all_five_and_clean_language(five):
    a = app(five, 'render_dataset_aware_tab')
    a.session_state['awareml_state'] = {'dataset': frame(), 'target': 'target', 'dataset_name': 'Fixture only'}
    a.run(timeout=30)
    assert not a.exception
    assert [x.value for x in a.metric][:4] == ['3', '15', '75', '—']
    a.button(key='three_dataset_run').click().run()
    assert a.dataframe[0].value.shape[0] == 5
    text = visible_text(a).lower()
    assert 'frozen' not in text and 'v3' not in text
    assert 'Predicted accuracy (%)' in a.dataframe[0].value.columns

def test_zero_weights_do_not_produce_a_recommendation(five):
    a = app(five, 'render_historical_preference_prior_tab').run(timeout=30)
    for k in ('accuracy','runtime','energy','co2'): a.slider(key='current_prior_' + k).set_value(0)
    a.run()
    assert not a.exception
    assert any('positive' in x.value for x in a.warning)
    assert not a.dataframe

def test_dataset_required_before_inference(five):
    a = app(five, 'render_dataset_aware_tab').run(timeout=30)
    assert not a.exception
    assert any('Run Studio' in x.value for x in a.info)
    assert not a.dataframe

def test_invalid_connection_settings_keep_goal_route_available():
    assets.POINTER.write_text('{bad', encoding='utf-8')
    a = AppTest.from_string('from awareml.ui_v2.copilot_workspace_v5 import render_copilot_workspace_header\nrender_copilot_workspace_header({})').run(timeout=30)
    assert not a.exception
    assert len(a.button) == 3

def test_navigation_preserves_dataset_context(five, monkeypatch):
    monkeypatch.setenv('AWAREML_RECOMMENDER_BUNDLE', str(five))
    code = 'from awareml.ui_v2.state import ensure_research_state\nfrom awareml.ui_v2.copilot_workspace_v5 import render_copilot_workspace_header\ns=ensure_research_state()\nrender_copilot_workspace_header(s)'
    a = AppTest.from_string(code)
    a.session_state['awareml_state'] = {'dataset': frame(), 'target': 'target'}
    a.run(timeout=30)
    a.button(key='copilot_workspace_open_historical').click().run()
    assert not a.exception
    assert a.session_state['awareml_state']['copilot_workspace_path'] == 'historical'
    assert a.session_state['awareml_state']['target'] == 'target'

def test_goal_plan_uses_all_five_prefix_models(five, monkeypatch):
    monkeypatch.setenv('AWAREML_RECOMMENDER_BUNDLE', str(five))
    a=AppTest.from_string('from awareml.ui_v2.pages_copilot import copilot_workspace_page\ncopilot_workspace_page()')
    a.session_state['awareml_state']={'dataset':frame(),'target':'target'}
    a.run(timeout=30)
    a.text_area(key='goal_v3_text').set_value('High prediction accuracy and low energy consumption.')
    a.toggle(key='goal_v3_use_llm').set_value(False)
    a.button(key='goal_v3_generate').click().run(timeout=30)
    assert not a.exception
    state=a.session_state['awareml_state']
    assert state['copilot_proposal'] is not None
    assert len(state['copilot_ranked'])==5
    assert state['copilot_prefix_profile']['profile_sample_size']==1000
    assert 'frozen' not in visible_text(a).lower()

def test_exported_models_and_reports_can_be_connected_without_retraining(five, tmp_path, monkeypatch):
    import importlib.util
    import zipfile
    from awareml.protocol_v3.common import sha256
    source=Path(__file__).resolve().parents[1]/'scripts/export_recommender_dashboard.py'
    spec=importlib.util.spec_from_file_location('dashboard_export_test',source)
    exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
    monkeypatch.setattr(exporter,'ROOT',tmp_path)
    for kind,role in [('development','nested_LODO_development_four_predeclared_profiles'),
                      ('external','revised_external_evaluation_of_previously_evaluated_cohort')]:
        directory=tmp_path/'artifacts'/kind;directory.mkdir(parents=True)
        csv=directory/'baseline_summary.csv';csv.write_text('method,selected_utility\nV3,0.5\n',encoding='utf-8')
        (directory/'evaluation.json').write_text(json.dumps({'bundle_manifest_sha256':sha256(five/'manifest.json'),
            'portfolio':'extended','role':role,'n_datasets':3,'n_preference_cases_per_method':12,
            'file_hashes':{'baseline_summary.csv':sha256(csv)}}),encoding='utf-8')
    archive=tmp_path/'download.zip'
    exporter.export(five,archive)
    local=tmp_path/'downloaded'
    with zipfile.ZipFile(archive) as z:z.extractall(local)
    assets.activate_assets(local/'models',local/'development',local/'external')
    assert bridge.bundle_status()['framework_count']==5
    assert bridge.evaluation_evidence('external')['metadata']['n_datasets']==3

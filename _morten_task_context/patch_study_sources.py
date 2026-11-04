"""Narrow edits to the installed Morten-review study, preserving local UI test fixes."""
import ast

def patch(path,source):
    def replace(old,new):
        nonlocal source
        if new in source:return
        if source.count(old)!=1:raise ValueError('Unrecognized installed source at '+path+': '+old[:90])
        source=source.replace(old,new)
    if path.endswith('studies/trust_morten_v2.py'):
        replace('SCHEMA_VERSION = "phase16_trust_calibration_v3"','SCHEMA_VERSION = "phase16_trust_calibration_v3_task_context_r1"')
        replace('data.get("schema_version") != SCHEMA_VERSION','data.get("schema_version") != "phase16_trust_calibration_v3"')
        replace('DEFAULT_DB_PATH = Path("artifacts/phase16_v3/trust_calibration.sqlite")','DEFAULT_DB_PATH = Path("artifacts/phase16_task_context_r1/trust_calibration.sqlite")')
    elif path.endswith('studies/morten_review_v3.py'):
        replace("REVIEWS = ROOT / 'artifacts/phase16_v3/assessor_reviews.csv'","REVIEWS = ROOT / 'artifacts/phase16_task_context_r1/assessor_reviews.csv'")
        replace("return 'RV-' + digest(row['stimulus_id'])[:12].upper()","from .task_context_revision import presentation_sha\n    return 'RV-' + digest({'stimulus_id':row['stimulus_id'],'presentation':presentation_sha()})[:12].upper()")
        old="hashlib.sha256((Path(root)/'stimuli_researcher.json').read_bytes()).hexdigest()"
        if old in source:
            source=source.replace(old,"__import__('awareml.studies.task_context_revision',fromlist=['review_bank_sha']).review_bank_sha(Path(root))")
    elif path.endswith('ui_v2/phase16_morten_v2.py'):
        replace('PFX = "p16v3"','PFX = "p16_task_context_r1"')
        replace('    render_stimulus_card(trial)','    from awareml.studies.task_context_revision import resolve_trial\n    try:trial=resolve_trial(trial)\n    except ValueError as exc:\n        st.error(str(exc));return\n    render_stimulus_card(trial)')
        old='Rate the AI assistant on this trial after reading its explanation. The factual correctness, fluency and confident-language questions refer to the explanation only. No response is preselected.'
        replace('"'+old+'"','__import__("awareml.studies.task_context_revision",fromlist=["TRUST_INSTRUCTION"]).TRUST_INSTRUCTION')
        old='EXPLANATION_ACTIONS, index=None,'
        new='EXPLANATION_ACTIONS, index=None, format_func=lambda value: __import__("awareml.studies.task_context_revision",fromlist=["EXPLANATION_LABELS"]).EXPLANATION_LABELS[value],'
        replace(old,new)
        replace('"Write the explanation correction and its reference evidence."','"Which claim should be checked or revised, and what reference evidence supports your concern?"')
        replace('    if explanation_action == "Correct before use":','    from awareml.studies.task_context_revision import CORRECTION_INSTRUCTION\n    st.caption(CORRECTION_INSTRUCTION)\n    if explanation_action == "Correct before use":')
        replace('"What does your recommendation decision take into account?", SCOPE_CHOICES, index=None,','__import__("awareml.studies.task_context_revision",fromlist=["SCOPE_QUESTION"]).SCOPE_QUESTION, SCOPE_CHOICES, index=None, format_func=lambda value: __import__("awareml.studies.task_context_revision",fromlist=["SCOPE_LABELS"]).SCOPE_LABELS[value],')
    elif path.endswith('ui_v2/phase17_morten_v2.py'):
        replace('PFX = "p17v3"','PFX = "p17_task_context_r1"')
        replace('return "information_seeking_v3_{}".format(mode)','return "information_seeking_task_context_r1_{}".format(mode)')
        replace('    if not _registration(mode, ctx):','    from awareml.studies.task_context_revision import require_information_context\n    try:require_information_context(ctx)\n    except ValueError as exc:\n        st.error(str(exc));return\n    if not _registration(mode, ctx):')
        replace('    _scenario_card(scenario)','    from .study_task_context import render_information_task\n    render_information_task(ctx)')
        replace('"What does your recommendation decision take into account?", SCOPE_CHOICES, index=None,','__import__("awareml.studies.task_context_revision",fromlist=["SCOPE_QUESTION"]).SCOPE_QUESTION, SCOPE_CHOICES, index=None, format_func=lambda value: __import__("awareml.studies.task_context_revision",fromlist=["SCOPE_LABELS"]).SCOPE_LABELS[value],')
    ast.parse(source)
    return source

TARGETS=['awareml/studies/trust_morten_v2.py','awareml/studies/morten_review_v3.py',
         'awareml/ui_v2/phase16_morten_v2.py','awareml/ui_v2/phase17_morten_v2.py']

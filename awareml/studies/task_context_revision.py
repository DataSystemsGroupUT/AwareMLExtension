"""Participant task context and presentation identity for the revised studies."""
from __future__ import annotations
import hashlib
import json

PRESENTATION_VERSION='task_context_r1'
TASK_INSTRUCTION=('Imagine that you are advising the decision-maker in the scenario below. '
    'Decide whether you would rely on the displayed framework recommendation for the stated study task, '
    'using the included objectives and reference evidence. You may question the objectives or identify '
    'requirements that the evidence does not address. Separately assess the supporting explanation.')
TRUST_INSTRUCTION=('For the next three statements, rate the AI assistant as presented in this trial: '
    'its recommendation and supporting explanation, considered with the scenario, study task and reference table. '
    'These are judgments of the assistant, not explanation-only ratings. The following factual-correctness, '
    'fluency and confident-language questions concern only the explanation text.')
EXPLANATION_LABELS={
    'Use as shown':'Use the explanation as written to support my decision',
    'Correct before use':'Flag an inaccurate or unsupported claim and request a revised explanation before relying on it',
    'Do not use':'Do not rely on this explanation to support my decision',
    'Unsure':'I am unsure how I would use this explanation'}
CORRECTION_INSTRUCTION=('Identify the claim and the reference evidence that should be checked or revised. '
    'This records feedback you would give to the system or study team. You are not asked to mentally rewrite '
    'the explanation or invent replacement values. The AI will not regenerate its explanation during this trial.')
SCOPE_QUESTION='Which parts of the stated scenario informed your recommendation decision?'
SCOPE_LABELS={'Included study objectives':'The included objectives and supplied framework evidence',
    'Requirements beyond the study objectives':'Other scenario requirements or missing evidence',
    'Both':'Both the included objectives and other scenario requirements',
    'Unsure':'Unsure which requirements should determine the decision'}
PAPER_SCOPE=('Following Miller (2019), explanation evaluation is situated in the recipient’s task and decision context. '
    'Track 2 examines how a controlled factual error in an explanation affects trial-level trust in the AI assistant '
    'and separate explanation-use judgments when the scenario, recommendation and reference evidence are held fixed '
    'within each matched family. It does not establish that factual correctness alone makes an explanation good, '
    'nor validate real deployment suitability, causal understanding or the completeness of the selected objectives. '
    'Track 3 describes how participants seek and use evidence in a stated scenario with a saved measured benchmark context; '
    'it is not a second confirmatory explanation-quality experiment.')


def presentation_sha():
    return hashlib.sha256(json.dumps({'version':PRESENTATION_VERSION,'task':TASK_INSTRUCTION,
        'trust':TRUST_INSTRUCTION,'actions':EXPLANATION_LABELS,'correction':CORRECTION_INSTRUCTION,
        'scope_question':SCOPE_QUESTION,'scope_labels':SCOPE_LABELS},sort_keys=True).encode()).hexdigest()


def review_bank_sha(root):
    raw=(root/'stimuli_researcher.json').read_bytes()
    return hashlib.sha256(raw+b'\n'+presentation_sha().encode()).hexdigest()


def resolve_trial(trial):
    result=dict(trial)
    if not str(result.get('scenario_text') or '').strip():
        from .morten_review_v3 import bank_rows
        matches=[r for r in bank_rows() if
            (result.get('scenario_id') and r.get('scenario_id')==result['scenario_id']) or
            (result.get('pair_id') and r.get('pair_id')==result['pair_id'])]
        texts={str(r.get('scenario_text') or '').strip() for r in matches}
        if len(texts)!=1 or not next(iter(texts),''):
            raise ValueError('Scenario context is missing or ambiguous. Ask the researcher to repair this trial before collection.')
        source=matches[0]
        if result.get('scenario_id') and result['scenario_id']!=source.get('scenario_id'):
            raise ValueError('Scenario and trial identifiers disagree.')
        result.update(scenario_text=next(iter(texts)),scenario_id=source.get('scenario_id'),domain=source.get('domain'))
    if not str(result.get('prompt') or '').strip():raise ValueError('The study task is missing.')
    return result


def require_information_context(ctx):
    scenario=ctx.get('scenario') or {}
    if not str(scenario.get('scenario') or '').strip():
        raise ValueError('The saved Information-Seeking scenario is missing. The researcher must select and confirm the task context.')
    if not ctx.get('scenario_alignment_attested'):
        raise ValueError('The researcher must confirm scenario and benchmark-objective alignment before participation.')
    return scenario

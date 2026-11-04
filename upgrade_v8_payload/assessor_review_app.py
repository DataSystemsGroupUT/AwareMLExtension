"""Independent review of exact participant cards. No answer key is displayed."""
import pandas as pd
import streamlit as st
from awareml.studies.morten_review_v3 import bank_rows, review_identity, review_template
from awareml.ui_v2.study_card_v3 import render_stimulus_card

st.set_page_config(page_title='AwareML exact stimulus review',layout='wide')
st.title('AwareML exact stimulus assessment')
st.write('Review independently before discussing items with another assessor. Use only the stated study task and supplied table. Assess the framework recommendation and the explanation separately. The explanation is supported only if all factual claims agree with the reference. Choose Insufficient evidence if a claim cannot be checked. Identify the claim and reference location even when all claims are supported. Privacy/security and other unscored requirements cannot be inferred from the ranking.')
assessor=st.text_input('Assessor code',value='',help='Use a pseudonymous assessor code, not a participant code.')
rows=sorted(bank_rows(),key=review_identity)
if not assessor.strip():st.stop()
st.session_state.setdefault('reviews',{})
ids=[review_identity(r) for r in rows]
rid=st.selectbox('Review item',ids,index=0)
row=next(r for r in rows if review_identity(r)==rid)
trial=dict(row['participant_version'])
render_stimulus_card(trial)
with st.form('review_'+rid):
    rec=st.radio('Is the framework recommendation supported by this task and reference ranking?', ['Supported','Incorrect','Insufficient evidence'],index=None)
    ex=st.radio('Are all factual claims in the explanation supported by the supplied reference?', ['Supported','Incorrect','Insufficient evidence'],index=None)
    reason=st.text_area('Identify the incorrect or unsupported claim, or explain why all claims are supported.')
    location=st.text_input('Identify the reference row and column supporting your judgment.')
    scope=st.radio('Are the included objectives and limits of the claim clear?', ['Yes','No'],index=None)
    save=st.form_submit_button('Save human assessment')
if save:
    if not all([rec,ex,reason.strip(),location.strip(),scope]):st.error('Complete each assessment field.')
    else:
        template=review_template(assessor.strip())
        record=template[template.review_id.eq(rid)].iloc[0].to_dict()
        record.update(recommendation_verdict=rec,explanation_verdict=ex,claim_or_reason=reason.strip(),reference_location=location.strip(),scope_clear=scope)
        st.session_state['reviews'][(assessor.strip(),rid)]=record
        st.success('Human assessment recorded. Select the next item.')
completed=[v for (a,r),v in st.session_state['reviews'].items() if a==assessor.strip()]
st.write('Completed {} of {} exact stimuli'.format(len(completed),len(rows)))
if completed:
    st.download_button('Export this assessor’s judgments CSV',pd.DataFrame(completed).to_csv(index=False).encode('utf-8'),file_name='assessor_review.csv',mime='text/csv')
st.caption('Export regularly. Reloading the browser may reset unsaved browser session state. Import the completed CSV in the Trust Calibration researcher workspace. Disagreements or uncertainty remain unresolved until human re-review; they are never replaced by generated labels.')

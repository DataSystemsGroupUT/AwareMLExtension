"""Presentation labels only. Framework identifiers and recorded results stay canonical."""
from __future__ import annotations
import copy
import re

_NAME = re.compile(r'\bChaCha\b(?![- ]OVR\b)')

def framework_label(value):
    return _NAME.sub('ChaCha-OVR', value) if isinstance(value, str) else value

def framework_description(name, fallback=''):
    if name=='ChaCha':
        return 'AwareML classification adaptation using FLAML AutoVW with logistic learners and a one-versus-rest wrapper.'
    return fallback

def display_labels(values):
    return [framework_label(value) for value in values]

def display_frame(frame):
    """Copy presentation tables; never rename a backend dataframe in place."""
    import pandas as pd
    if not isinstance(frame, pd.DataFrame):
        return frame
    result=frame.copy(deep=True)
    for column in result.columns:
        key=str(column).lower().replace('_',' ')
        if any(word in key for word in ('framework','winner','method','candidate','alternative','recommendation')):
            result[column]=result[column].map(framework_label)
    if isinstance(result.index,pd.Index) and result.index.dtype == object:
        result.index=result.index.map(framework_label)
    result.columns=[framework_label(c) for c in result.columns]
    return result

def display_figure(figure):
    """Copy chart labels while preserving numeric values and custom-data identifiers."""
    if not hasattr(figure,'data') or not hasattr(figure,'layout'):
        return figure
    result=copy.deepcopy(figure)
    for trace in result.data:
        for key in ('name','text','hovertext','hovertemplate'):
            value=getattr(trace,key,None)
            if isinstance(value,str):setattr(trace,key,framework_label(value))
            elif value is not None and key in ('text','hovertext'):
                setattr(trace,key,[framework_label(x) for x in value])
        for key in ('x','y','z'):
            value=getattr(trace,key,None)
            if value is not None and not isinstance(value,str):
                values=list(value)
                if any(isinstance(x,str) and _NAME.search(x) for x in values):
                    setattr(trace,key,[framework_label(x) for x in values])
    for item in result.layout.annotations or ():
        item.text=framework_label(item.text)
    for axis in ('xaxis','yaxis','zaxis'):
        obj=getattr(result.layout,axis,None)
        if obj is not None and obj.ticktext is not None:
            obj.ticktext=display_labels(obj.ticktext)
    return result

"""Make narrow presentation edits without rewriting local application files."""
from __future__ import annotations
import ast

IMPORT='from awareml.ui_v2.framework_labels import framework_label, framework_description, display_labels, display_frame, display_figure\n'
HELPERS={'framework_label','display_labels','display_frame','display_figure'}

def patch_source(source):
    # Ensure the active page always passes through the workspace header.
    tree=ast.parse(source)
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='copilot_workspace_page']
    if functions:
        node=functions[-1]
        lines=source.splitlines(keepends=True)
        replacement='''def copilot_workspace_page():
    from .state import ensure_research_state
    from .copilot_workspace_v5 import render_copilot_workspace_header
    from .copilot_recommender import render_historical_preference_prior_tab, render_dataset_aware_tab
    from .copilot_unified import render_goal_copilot_unified_page
    active_path = render_copilot_workspace_header(ensure_research_state())
    if active_path == "historical":
        render_historical_preference_prior_tab()
    elif active_path == "dataset":
        render_dataset_aware_tab()
    else:
        render_goal_copilot_unified_page()
'''
        source=''.join(lines[:node.lineno-1])+replacement+''.join(lines[node.end_lineno:])
    source=source.replace('st.caption(spec.get("description") or "")',
                          'st.caption(framework_description(framework, spec.get("description") or ""))')
    tree=ast.parse(source)
    lines=source.splitlines(keepends=True)
    offsets=[];total=0
    for line in lines:offsets.append(total);total+=len(line)
    def pos(line,column):
        # Python AST columns count UTF-8 bytes, rather than Unicode characters.
        return offsets[line-1]+len(lines[line-1].encode('utf-8')[:column].decode('utf-8'))
    edits=[]
    def wrap(node,helper):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in HELPERS:return
        edits.append((pos(node.lineno,node.col_offset),helper+'('))
        edits.append((pos(node.end_lineno,node.end_col_offset),')'))
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute):continue
        name=node.func.attr
        is_streamlit=isinstance(node.func.value,ast.Name) and node.func.value.id=='st'
        if not is_streamlit and name!='metric':continue
        first=node.args[0] if node.args else next((k.value for k in node.keywords if k.arg in ('data','figure','label')),None)
        if name in ('dataframe','table') and first is not None:wrap(first,'display_frame')
        elif name=='plotly_chart' and first is not None:wrap(first,'display_figure')
        elif name=='tabs' and first is not None:wrap(first,'display_labels')
        elif name=='metric':
            for item in node.args[:2]:wrap(item,'framework_label')
            for kw in node.keywords:
                if kw.arg in ('label','value'):wrap(kw.value,'framework_label')
        elif name in ('caption','markdown','write','info','success','title','header','subheader') and first is not None:
            text=source[pos(first.lineno,first.col_offset):pos(first.end_lineno,first.end_col_offset)]
            if any(x in text.lower() for x in ('chacha','framework','winner')):wrap(first,'framework_label')
        elif name in ('selectbox','multiselect','radio','segmented_control') and first is not None:
            label=first.value if isinstance(first,ast.Constant) else ''
            if isinstance(label,str) and 'framework' in label.lower() and not any(k.arg=='format_func' for k in node.keywords):
                point=pos(node.end_lineno,node.end_col_offset)-1
                before=source[:point].rstrip()
                separator='' if before.endswith(',') else ','
                edits.append((point,separator+' format_func=framework_label'))
    if (edits or 'framework_description(framework,' in source) and IMPORT.strip() not in source:
        index=0
        for node in tree.body:
            is_doc=isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str)
            if is_doc or isinstance(node,ast.ImportFrom) and node.module=='__future__':index=node.end_lineno
            else:break
        point=sum(len(line) for line in lines[:index])
        edits.append((point,IMPORT))
    for point,value in sorted(edits,key=lambda item:item[0],reverse=True):source=source[:point]+value+source[point:]
    ast.parse(source)
    return source

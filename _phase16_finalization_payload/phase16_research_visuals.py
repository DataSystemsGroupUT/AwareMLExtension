from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

try:
    import altair as alt
except Exception:  # pragma: no cover
    alt = None


PALETTE = {
    "blue": "#2563EB",
    "blue_dark": "#1D4ED8",
    "teal": "#0F766E",
    "green": "#059669",
    "amber": "#D97706",
    "red": "#DC2626",
    "purple": "#7C3AED",
    "indigo": "#4F46E5",
    "slate": "#475569",
    "grid": "#E5E7EB",
}

CORRECT_COLOR = PALETTE["teal"]
INCORRECT_COLOR = PALETTE["red"]
MIDLINE_COLOR = "#64748B"

SOURCE_STAGE_LABELS = {
    "B": "Framework recommendation",
    "E": "Fairness explanation",
    "F_CHAT": "Conversational explanation",
    "F_XAI": "Feature-attribution explanation",
}

QUESTION_BANK_RECOMMENDATIONS = [
    {
        "Construct": "Usability",
        "Candidate item": "The overall AutoML workflow presented in AwareML was easy to understand.",
        "Source": "Previous AwareML Dashboard user study",
        "Status": "Optional secondary item",
    },
    {
        "Construct": "Decision support",
        "Candidate item": "The framework recommendations provided useful support for comparing AutoML alternatives.",
        "Source": "Previous AwareML Dashboard user study",
        "Status": "Optional secondary item",
    },
    {
        "Construct": "Recommendation transparency",
        "Candidate item": "I understood why AwareML recommended one framework or configuration over another.",
        "Source": "Previous AwareML Dashboard user study",
        "Status": "Optional secondary item",
    },
    {
        "Construct": "Performance / drift understanding",
        "Candidate item": "AwareML helped me understand how model performance changed over time and how concept drift was handled.",
        "Source": "Previous AwareML Dashboard user study",
        "Status": "Optional secondary item",
    },
    {
        "Construct": "Fairness support",
        "Candidate item": "The fairness analysis was useful when comparing models or frameworks.",
        "Source": "Previous AwareML Dashboard user study",
        "Status": "Optional secondary item",
    },
    {
        "Construct": "Sustainability support",
        "Candidate item": "The sustainability information, including energy use and CO₂ emissions, was useful when comparing AutoML alternatives.",
        "Source": "Previous AwareML Dashboard user study",
        "Status": "Optional secondary item",
    },
]


def _num(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct(value: Any) -> Optional[float]:
    value = _num(value)
    return None if value is None else 100.0 * value


def _source_label(value: Any) -> str:
    key = str(value or "")
    return SOURCE_STAGE_LABELS.get(key, key.replace("_", " ").title())


def _short_group_label(value: Any) -> str:
    mapping = {
        "Novice / student": "Novice",
        "Practitioner": "Practitioner",
        "AutoML User / Practitioner": "Practitioner",
        "ML / AutoML expert": "Expert",
        "ML Researcher with strong AutoML background": "Researcher",
    }
    return mapping.get(str(value), str(value))


def _theme():
    return {
        "config": {
            "background": "white",
            "font": "Inter, Segoe UI, Arial, sans-serif",
            "view": {"stroke": None},
            "title": {
                "fontSize": 15,
                "fontWeight": 700,
                "color": "#0F172A",
                "anchor": "start",
                "offset": 12,
            },
            "axis": {
                "labelColor": "#334155",
                "titleColor": "#334155",
                "gridColor": PALETTE["grid"],
                "domainColor": "#CBD5E1",
                "tickColor": "#CBD5E1",
                "labelFontSize": 12,
                "titleFontSize": 12,
                "labelPadding": 10,
                "titlePadding": 12,
            },
            "legend": {
                "labelColor": "#334155",
                "titleColor": "#334155",
                "labelFontSize": 12,
                "titleFontSize": 12,
                "orient": "bottom",
            },
        }
    }


def _apply_theme():
    if alt is None:
        return
    try:
        alt.themes.register("awareml_phase16_final_v2", _theme)
    except Exception:
        pass
    try:
        alt.themes.enable("awareml_phase16_final_v2")
    except Exception:
        pass


def _base(df: pd.DataFrame, title: str, height: int = 300):
    _apply_theme()
    return (
        alt.Chart(df)
        .properties(
            title=title,
            height=height,
            padding={"left": 26, "right": 26, "top": 18, "bottom": 22},
        )
    )


def _show(chart, fallback: Optional[pd.DataFrame] = None):
    if alt is None:
        if fallback is not None:
            st.dataframe(fallback, use_container_width=True, hide_index=True)
        return
    st.altair_chart(chart, use_container_width=True)


def _midline(value: float, axis: str = "x"):
    df = pd.DataFrame({axis: [value]})
    if axis == "x":
        return alt.Chart(df).mark_rule(strokeDash=[5, 5], color=MIDLINE_COLOR).encode(x="x:Q")
    return alt.Chart(df).mark_rule(strokeDash=[5, 5], color=MIDLINE_COLOR).encode(y="y:Q")


def _note(text: str):
    st.markdown(
        "<div style='margin:.4rem 0 .9rem;padding:.75rem .95rem;border:1px solid #dbe2ea;"
        "border-radius:12px;background:#f8fafc;color:#334155;line-height:1.45'>"
        + text
        + "</div>",
        unsafe_allow_html=True,
    )


def _small_n(n: int, label: str = "participants"):
    if int(n or 0) < 10:
        st.caption(
            "Pilot visualization only · {} {}. Interpret descriptively; small samples can move these estimates substantially.".format(
                int(n or 0), label
            )
        )


def render_trust_calibration_visuals(
    result: Dict[str, Any],
    responses: Optional[pd.DataFrame] = None,
) -> None:
    if str(result.get("status") or "") != "ok":
        return

    n = int(result.get("participants_completed_valid") or 0)
    st.markdown("#### Visual calibration dashboard")
    st.caption(
        "Redesigned researcher-only view for quick calibration reading. The primary estimand and underlying calculations remain unchanged."
    )
    _small_n(n)

    condition = result.get("condition_summary") or {}
    correct = condition.get("correct") or {}
    incorrect = condition.get("incorrect") or {}

    overview_tab, reliance_tab, expertise_tab, style_tab = st.tabs(
        ["Calibration overview", "Reliance behavior", "Expertise & sources", "Style & timing"]
    )

    with overview_tab:
        _note(
            "<b>Core question.</b> Do participants assign more trust to correct explanations and reduce reliance on incorrect explanations?"
        )
        overview = pd.DataFrame(
            [
                {
                    "Condition": "Correct",
                    "Mean trust": _num(correct.get("mean_trust")),
                    "Acceptance rate (%)": _pct(correct.get("acceptance_rate")),
                },
                {
                    "Condition": "Incorrect",
                    "Mean trust": _num(incorrect.get("mean_trust")),
                    "Acceptance rate (%)": _pct(incorrect.get("acceptance_rate")),
                },
            ]
        ).dropna(how="all")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            if not overview.empty and alt is not None:
                chart = (
                    _base(overview, "Mean trust by explanation correctness", 300)
                    .mark_bar(cornerRadiusTopLeft=7, cornerRadiusTopRight=7)
                    .encode(
                        x=alt.X("Condition:N", sort=["Correct", "Incorrect"], title=None),
                        y=alt.Y("Mean trust:Q", scale=alt.Scale(domain=[0, 7]), title="Mean trust (1–7)"),
                        color=alt.Color(
                            "Condition:N",
                            scale=alt.Scale(
                                domain=["Correct", "Incorrect"],
                                range=[CORRECT_COLOR, INCORRECT_COLOR],
                            ),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("Condition:N"),
                            alt.Tooltip("Mean trust:Q", format=".2f"),
                        ],
                    )
                )
                _show(chart + _midline(4, "y"), overview)
        with c2:
            if not overview.empty and alt is not None:
                chart = (
                    _base(overview, "Acceptance by explanation correctness", 300)
                    .mark_bar(cornerRadiusTopLeft=7, cornerRadiusTopRight=7)
                    .encode(
                        x=alt.X("Condition:N", sort=["Correct", "Incorrect"], title=None),
                        y=alt.Y(
                            "Acceptance rate (%):Q",
                            scale=alt.Scale(domain=[0, 100]),
                            title="Acceptance rate (%)",
                        ),
                        color=alt.Color(
                            "Condition:N",
                            scale=alt.Scale(
                                domain=["Correct", "Incorrect"],
                                range=[PALETTE["blue"], PALETTE["amber"]],
                            ),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("Condition:N"),
                            alt.Tooltip("Acceptance rate (%):Q", format=".1f"),
                        ],
                    )
                )
                _show(chart, overview)

        paired = ((result.get("primary_calibration") or {}).get("paired_gap") or {})
        ci = paired.get("ci95") or [None, None]
        gap = _num(paired.get("mean_gap"))
        lo = _num(ci[0]) if len(ci) > 0 else None
        hi = _num(ci[1]) if len(ci) > 1 else None
        if gap is not None:
            message = "Mean within-participant trust gap: **{:.2f}**".format(gap)
            if lo is not None and hi is not None:
                message += " · bootstrap 95% CI **[{:.2f}, {:.2f}]**".format(lo, hi)
            st.info(message)

    with reliance_tab:
        _note(
            "<b>Behavioral calibration.</b> Appropriate reliance combines acceptance of correct explanations with non-acceptance of incorrect explanations."
        )
        frame = pd.DataFrame() if responses is None else responses.copy()

        if not frame.empty and {"correctness_condition", "decision_action"}.issubset(frame.columns):
            action = (
                frame.assign(
                    Condition=frame["correctness_condition"].astype(str).str.title(),
                    Action=frame["decision_action"].astype(str),
                )
                .groupby(["Condition", "Action"])
                .size()
                .reset_index(name="Trials")
            )
            action["Percent"] = (
                action["Trials"] / action.groupby("Condition")["Trials"].transform("sum") * 100.0
            )
            if alt is not None:
                chart = (
                    _base(action, "Accept / Override / Reject behavior", 240)
                    .mark_bar()
                    .encode(
                        y=alt.Y("Condition:N", sort=["Correct", "Incorrect"], title=None),
                        x=alt.X("Percent:Q", stack="normalize", title="Share of decisions"),
                        color=alt.Color(
                            "Action:N",
                            scale=alt.Scale(
                                domain=["Accept", "Override", "Reject"],
                                range=[PALETTE["green"], PALETTE["amber"], PALETTE["red"]],
                            ),
                        ),
                        tooltip=[
                            alt.Tooltip("Condition:N"),
                            alt.Tooltip("Action:N"),
                            alt.Tooltip("Trials:Q"),
                            alt.Tooltip("Percent:Q", format=".1f"),
                        ],
                    )
                )
                _show(chart, action)

        reliance = result.get("reliance") or {}
        over = result.get("overtrust") or {}
        under = result.get("undertrust") or {}
        profile = pd.DataFrame(
            [
                {"Measure": "Appropriate reliance", "Rate": _pct(reliance.get("appropriate_reliance_rate"))},
                {"Measure": "Over-trust", "Rate": _pct(over.get("overtrust_rate"))},
                {"Measure": "Under-trust", "Rate": _pct(under.get("undertrust_rate"))},
            ]
        ).dropna()
        if not profile.empty and alt is not None:
            chart = (
                _base(profile, "Reliance profile", 230)
                .mark_bar(cornerRadiusEnd=7)
                .encode(
                    y=alt.Y(
                        "Measure:N",
                        sort=["Appropriate reliance", "Over-trust", "Under-trust"],
                        title=None,
                        axis=alt.Axis(labelLimit=220),
                    ),
                    x=alt.X("Rate:Q", scale=alt.Scale(domain=[0, 100]), title="Rate (%)"),
                    color=alt.Color(
                        "Measure:N",
                        scale=alt.Scale(
                            domain=["Appropriate reliance", "Over-trust", "Under-trust"],
                            range=[PALETTE["green"], PALETTE["amber"], PALETTE["red"]],
                        ),
                        legend=None,
                    ),
                    tooltip=[alt.Tooltip("Measure:N"), alt.Tooltip("Rate:Q", format=".1f")],
                )
            )
            _show(chart, profile)

    with expertise_tab:
        _note(
            "<b>Subgroup view.</b> Expertise comparisons remain secondary/descriptive unless the study is separately powered for an expertise interaction."
        )

        expertise_rows = []
        for group, values in (result.get("expertise_groups") or {}).items():
            values = values or {}
            expertise_rows.append(
                {
                    "Expertise": _short_group_label(group),
                    "Participants": int(values.get("participants") or 0),
                    "Trust gap": _num(values.get("mean_trust_gap")),
                    "Over-trust (%)": _pct(values.get("overtrust_rate")),
                }
            )
        ef = pd.DataFrame(expertise_rows)
        if not ef.empty:
            c1, c2 = st.columns(2, gap="large")
            with c1:
                df = ef.dropna(subset=["Trust gap"])
                if not df.empty and alt is not None:
                    chart = (
                        _base(df, "Trust gap by expertise group", 260)
                        .mark_bar(cornerRadiusEnd=7, color=PALETTE["blue"])
                        .encode(
                            y=alt.Y(
                                "Expertise:N",
                                sort="-x",
                                title=None,
                                axis=alt.Axis(labelLimit=180),
                            ),
                            x=alt.X("Trust gap:Q", title="Correct − incorrect trust"),
                            tooltip=[
                                alt.Tooltip("Expertise:N"),
                                alt.Tooltip("Participants:Q"),
                                alt.Tooltip("Trust gap:Q", format=".2f"),
                            ],
                        )
                    )
                    _show(chart, df)
            with c2:
                df = ef.dropna(subset=["Over-trust (%)"])
                if not df.empty and alt is not None:
                    chart = (
                        _base(df, "Over-trust by expertise group", 260)
                        .mark_bar(cornerRadiusEnd=7, color=PALETTE["amber"])
                        .encode(
                            y=alt.Y(
                                "Expertise:N",
                                sort="x",
                                title=None,
                                axis=alt.Axis(labelLimit=180),
                            ),
                            x=alt.X(
                                "Over-trust (%):Q",
                                scale=alt.Scale(domain=[0, 100]),
                                title="Accepted incorrect explanations (%)",
                            ),
                            tooltip=[
                                alt.Tooltip("Expertise:N"),
                                alt.Tooltip("Participants:Q"),
                                alt.Tooltip("Over-trust (%):Q", format=".1f"),
                            ],
                        )
                    )
                    _show(chart, df)

        source_rows = []
        for stage, values in (result.get("source_stages") or {}).items():
            values = values or {}
            c = _num(values.get("mean_trust_correct"))
            i = _num(values.get("mean_trust_incorrect"))
            if c is not None and i is not None:
                source_rows.append(
                    {
                        "Explanation source": _source_label(stage),
                        "Correct": c,
                        "Incorrect": i,
                        "Gap": c - i,
                    }
                )
        sf = pd.DataFrame(source_rows)
        if not sf.empty and alt is not None:
            order = sf.sort_values("Gap", ascending=False)["Explanation source"].tolist()
            long = sf.melt(
                id_vars=["Explanation source", "Gap"],
                value_vars=["Correct", "Incorrect"],
                var_name="Condition",
                value_name="Mean trust",
            )
            line = (
                _base(long, "Trust by explanation source", max(300, 68 * len(sf)))
                .mark_line(strokeWidth=3, color="#94A3B8")
                .encode(
                    y=alt.Y(
                        "Explanation source:N",
                        sort=order,
                        title=None,
                        axis=alt.Axis(labelLimit=260),
                    ),
                    x=alt.X("Mean trust:Q", scale=alt.Scale(domain=[1, 7]), title="Mean trust (1–7)"),
                    detail="Explanation source:N",
                )
            )
            points = (
                _base(long, "", max(300, 68 * len(sf)))
                .mark_circle(size=170)
                .encode(
                    y=alt.Y("Explanation source:N", sort=order, title=None),
                    x=alt.X("Mean trust:Q", scale=alt.Scale(domain=[1, 7]), title="Mean trust (1–7)"),
                    color=alt.Color(
                        "Condition:N",
                        scale=alt.Scale(
                            domain=["Correct", "Incorrect"],
                            range=[CORRECT_COLOR, INCORRECT_COLOR],
                        ),
                        legend=alt.Legend(title="Condition"),
                    ),
                    tooltip=[
                        alt.Tooltip("Explanation source:N"),
                        alt.Tooltip("Condition:N"),
                        alt.Tooltip("Mean trust:Q", format=".2f"),
                        alt.Tooltip("Gap:Q", format=".2f", title="Correct−incorrect gap"),
                    ],
                )
            )
            _show(line + points, sf)

    with style_tab:
        _note(
            "<b>Style diagnostics.</b> These analyses test whether trust aligns with actual correctness or with fluent/confident presentation."
        )
        style = result.get("style_vs_correctness") or {}
        regression = style.get("participant_centered_regression") or {}
        betas = regression.get("betas") or {}
        names = {
            "correctness_binary": "Actual correctness",
            "fluency_rating": "Perceived fluency",
            "perceived_confidence": "Confident-sounding language",
            "order_index": "Trial order",
        }
        beta = pd.DataFrame(
            [{"Predictor": names.get(k, k), "Coefficient": _num(v)} for k, v in betas.items()]
        ).dropna()
        if not beta.empty and alt is not None:
            chart = (
                _base(beta, "What is associated with trust?", 270)
                .mark_bar(cornerRadiusEnd=7)
                .encode(
                    y=alt.Y("Predictor:N", sort="-x", title=None, axis=alt.Axis(labelLimit=240)),
                    x=alt.X("Coefficient:Q", title="Participant-centered standardized coefficient"),
                    color=alt.Color(
                        "Predictor:N",
                        scale=alt.Scale(
                            domain=[
                                "Actual correctness",
                                "Perceived fluency",
                                "Confident-sounding language",
                                "Trial order",
                            ],
                            range=[
                                PALETTE["teal"],
                                PALETTE["blue"],
                                PALETTE["purple"],
                                PALETTE["slate"],
                            ],
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Predictor:N"),
                        alt.Tooltip("Coefficient:Q", format=".3f"),
                    ],
                )
            )
            _show(chart + _midline(0, "x"), beta)

        if responses is not None and not responses.empty and {
            "correctness_condition",
            "response_time_sec",
        }.issubset(responses.columns):
            rt = responses[["correctness_condition", "response_time_sec"]].copy()
            rt["Condition"] = rt["correctness_condition"].astype(str).str.title()
            rt["Response time (s)"] = pd.to_numeric(rt["response_time_sec"], errors="coerce")
            rt = rt.dropna(subset=["Response time (s)"])
            if not rt.empty and alt is not None:
                chart = (
                    _base(rt, "Response-time distribution", 290)
                    .mark_boxplot(size=75)
                    .encode(
                        x=alt.X("Condition:N", sort=["Correct", "Incorrect"], title=None),
                        y=alt.Y("Response time (s):Q", title="Response time (seconds)"),
                        color=alt.Color(
                            "Condition:N",
                            scale=alt.Scale(
                                domain=["Correct", "Incorrect"],
                                range=[CORRECT_COLOR, INCORRECT_COLOR],
                            ),
                            legend=None,
                        ),
                    )
                )
                _show(chart, rt)


def render_secondary_visuals(summary: Dict[str, Any], rows: Any) -> None:
    rows = list(rows or [])
    n = int(summary.get("responses") or 0)

    st.markdown("#### Visual study-experience profile")
    st.caption(
        "Redesigned researcher-only summary of the secondary human-agency and study-experience measures. Tables remain available below."
    )
    _small_n(n, "completed questionnaires")

    construct_labels = {
        "human_agency": "Human agency",
        "calibrated_reliance_support": "Calibration support",
        "explainability": "Explainability",
        "usability": "Usability",
        "global_reliance": "Global reliance",
    }
    item_labels = {
        "critical_evaluation": "Critical evaluation",
        "freedom_to_override": "Freedom to override/reject",
        "final_control": "Final decision control",
        "rely_or_question": "Know when to rely/question",
        "evidence_checking": "Evidence checking",
        "explanation_usefulness": "Explanation usefulness",
        "interface_usability": "Interface usability",
        "real_world_support_trust": "Real-world support trust",
    }

    construct_df = pd.DataFrame(
        [
            {
                "Construct": construct_labels.get(k, k.replace("_", " ").title()),
                "Mean": _num(v),
            }
            for k, v in (summary.get("construct_means") or {}).items()
            if _num(v) is not None
        ]
    )

    _note(
        "<b>Construct profile.</b> Scores use the 1–7 response scale; the dashed line marks the neutral midpoint of 4."
    )
    if not construct_df.empty and alt is not None:
        chart = (
            _base(construct_df, "Construct profile (1–7)", max(290, 60 * len(construct_df)))
            .mark_bar(cornerRadiusEnd=7, color=PALETTE["blue"])
            .encode(
                y=alt.Y(
                    "Construct:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(labelLimit=260),
                ),
                x=alt.X("Mean:Q", scale=alt.Scale(domain=[1, 7]), title="Mean response (1–7)"),
                tooltip=[alt.Tooltip("Construct:N"), alt.Tooltip("Mean:Q", format=".2f")],
            )
        )
        _show(chart + _midline(4, "x"), construct_df)

    if rows:
        frame = pd.DataFrame(rows)
        ids = [key for key in item_labels if key in frame.columns]
        dist_rows = []
        for item_id in ids:
            values = pd.to_numeric(frame[item_id], errors="coerce").dropna().astype(int)
            counts = values.value_counts().reindex(range(1, 8), fill_value=0)
            for rating, count in counts.items():
                dist_rows.append(
                    {
                        "Item": item_labels[item_id],
                        "Rating": int(rating),
                        "Responses": int(count),
                    }
                )
        heat = pd.DataFrame(dist_rows)
        if not heat.empty and alt is not None:
            _note(
                "<b>Response distribution.</b> This heatmap shows where responses concentrate without forcing long item labels into narrow chart columns."
            )
            base = _base(heat, "Response distribution heatmap", max(340, 44 * len(ids)))
            rect = base.mark_rect(cornerRadius=3).encode(
                x=alt.X("Rating:O", title="Likert rating (1–7)"),
                y=alt.Y("Item:N", sort=None, title=None, axis=alt.Axis(labelLimit=280)),
                color=alt.Color(
                    "Responses:Q",
                    scale=alt.Scale(range=["#EFF6FF", PALETTE["blue_dark"]]),
                    title="Responses",
                ),
                tooltip=[
                    alt.Tooltip("Item:N"),
                    alt.Tooltip("Rating:O"),
                    alt.Tooltip("Responses:Q"),
                ],
            )
            text = base.mark_text(fontSize=11).encode(
                x="Rating:O",
                y=alt.Y("Item:N", sort=None),
                text=alt.Text("Responses:Q"),
                color=alt.condition("datum.Responses > 0", alt.value("white"), alt.value("#94A3B8")),
            )
            _show(rect + text, heat)

    item_df = pd.DataFrame(
        [
            {
                "Item": item_labels.get(k, k.replace("_", " ").title()),
                "Mean": _num(v),
            }
            for k, v in (summary.get("item_means") or {}).items()
            if _num(v) is not None
        ]
    )
    if not item_df.empty and alt is not None:
        _note(
            "<b>Item-level profile.</b> Horizontal bars and larger label margins prevent item text from touching or being hidden by the plotting area."
        )
        chart = (
            _base(item_df, "Item-level profile (1–7)", max(360, 52 * len(item_df)))
            .mark_bar(cornerRadiusEnd=7, color=PALETTE["indigo"])
            .encode(
                y=alt.Y(
                    "Item:N",
                    sort="-x",
                    title=None,
                    axis=alt.Axis(labelLimit=300),
                ),
                x=alt.X("Mean:Q", scale=alt.Scale(domain=[1, 7]), title="Mean response (1–7)"),
                tooltip=[alt.Tooltip("Item:N"), alt.Tooltip("Mean:Q", format=".2f")],
            )
        )
        _show(chart + _midline(4, "x"), item_df)

    by_expertise = pd.DataFrame(summary.get("by_expertise") or [])
    available = [key for key in construct_labels if key in by_expertise.columns]
    if not by_expertise.empty and available:
        long = by_expertise.melt(
            id_vars=["expertise_group", "participants"],
            value_vars=available,
            var_name="Construct key",
            value_name="Mean",
        )
        long["Construct"] = long["Construct key"].map(construct_labels)
        long["Expertise"] = long["expertise_group"].apply(_short_group_label)
        long["Mean"] = pd.to_numeric(long["Mean"], errors="coerce")
        long = long.dropna(subset=["Mean"])

        if not long.empty and alt is not None:
            _note(
                "<b>Novice / practitioner / expert comparison.</b> The matrix layout avoids overlapping grouped bars and makes small subgroup counts easier to inspect."
            )
            base = _base(
                long,
                "Novice / practitioner / expert comparison",
                max(300, 54 * long["Construct"].nunique()),
            )
            rect = base.mark_rect(cornerRadius=5).encode(
                x=alt.X("Expertise:N", title="Expertise group", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Construct:N", sort=None, title=None, axis=alt.Axis(labelLimit=240)),
                color=alt.Color(
                    "Mean:Q",
                    scale=alt.Scale(domain=[1, 7], range=["#EFF6FF", PALETTE["blue_dark"]]),
                    title="Mean",
                ),
                tooltip=[
                    alt.Tooltip("Expertise:N"),
                    alt.Tooltip("Construct:N"),
                    alt.Tooltip("Mean:Q", format=".2f"),
                    alt.Tooltip("participants:Q", title="Participants"),
                ],
            )
            text = base.mark_text(fontWeight=700).encode(
                x="Expertise:N",
                y=alt.Y("Construct:N", sort=None),
                text=alt.Text("Mean:Q", format=".2f"),
                color=alt.condition("datum.Mean >= 4.5", alt.value("white"), alt.value("#0F172A")),
            )
            _show(rect + text, long)
            st.caption(
                "Expertise comparisons are secondary/descriptive unless the Main Study is separately powered for subgroup interactions."
            )

    with st.expander(
        "Optional future questionnaire additions from the previous AwareML user study",
        expanded=False,
    ):
        st.caption(
            "These optional system-level items are not part of the primary Trust Calibration estimand."
        )
        st.dataframe(
            pd.DataFrame(QUESTION_BANK_RECOMMENDATIONS),
            use_container_width=True,
            hide_index=True,
        )

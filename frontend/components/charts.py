import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def plot_decision_donut(allow_count: int, deny_count: int, appr_count: int):
    labels = ["ALLOW", "DENY", "REQUIRE_APPROVAL"]
    values = [allow_count, deny_count, appr_count]
    colors = ["#10B981", "#EF4444", "#F59E0B"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        showlegend=False
    )])

    total = sum(values)
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        annotations=[dict(
            text=f"<b>{total}</b><br><span style='font-size:11px;color:#64748B;'>Decisions</span>",
            x=0.5, y=0.5,
            font_size=20,
            showarrow=False
        )],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def plot_agent_activity(df_logs: pd.DataFrame):
    if df_logs.empty or "agent_name" not in df_logs.columns:
        return None

    # Group by agent and decision
    grouped = df_logs.groupby(["agent_name", "decision"]).size().reset_index(name="count")
    color_map = {
        "ALLOW": "#10B981",
        "DENY": "#EF4444",
        "REQUIRE_APPROVAL": "#F59E0B"
    }

    fig = px.bar(
        grouped,
        x="agent_name",
        y="count",
        color="decision",
        color_discrete_map=color_map,
        barmode="stack",
        labels={"agent_name": "AI Agent", "count": "Evaluations", "decision": "Decision"},
        height=260
    )

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
    )
    return fig

def plot_risk_distribution(df_logs: pd.DataFrame):
    if df_logs.empty or "risk_level" not in df_logs.columns:
        return None

    risk_counts = df_logs["risk_level"].value_counts().reset_index()
    risk_counts.columns = ["risk_level", "count"]
    
    # Order standard risks
    order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    risk_counts["order"] = risk_counts["risk_level"].map(lambda x: order.index(x) if x in order else 99)
    risk_counts = risk_counts.sort_values("order")

    color_map = {
        "LOW": "#10B981",
        "MEDIUM": "#F59E0B",
        "HIGH": "#F97316",
        "CRITICAL": "#EF4444"
    }

    fig = px.bar(
        risk_counts,
        x="risk_level",
        y="count",
        color="risk_level",
        color_discrete_map=color_map,
        labels={"risk_level": "Risk Tier", "count": "Events"},
        height=260
    )

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
    )
    return fig

"""
Enterprise SaaS Styling Module for AgentGuard Platform.
Designed with modern cybersecurity visual standards:
Dark Navy Sidebar (#0F172A), Slate Accents, Crisp Light Dashboard (#F8FAFC).
"""

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Top Padding & App Background */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        max-width: 100% !important;
    }

    /* Dark Navy Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0B1120 !important;
        border-right: 1px solid #1E293B !important;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #94A3B8 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #1E293B !important;
        color: #60A5FA !important;
        border-left: 3px solid #3B82F6 !important;
    }

    /* Header Titles */
    .page-header {
        margin-bottom: 1.5rem;
    }
    .page-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .page-subtitle {
        color: #64748B;
        font-size: 0.95rem;
        margin-top: 0;
        margin-bottom: 1.25rem;
    }

    /* Enterprise KPI Metric Cards */
    .metric-card-pro {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card-pro:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
    }
    .metric-card-pro::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
    }
    .metric-card-pro.alert-card::before {
        background: linear-gradient(90deg, #EF4444, #F97316);
    }
    .metric-card-pro.warn-card::before {
        background: linear-gradient(90deg, #F59E0B, #EAB308);
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.82rem;
        margin-top: 0.4rem;
        color: #64748B;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    /* Decision Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .badge-allow {
        background-color: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    .badge-deny {
        background-color: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
    .badge-approval {
        background-color: #FFFBEB;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .badge-active {
        background-color: #F0FDF4;
        color: #166534;
        border: 1px solid #BBF7D0;
    }
    .badge-inactive {
        background-color: #F8FAFC;
        color: #64748B;
        border: 1px solid #E2E8F0;
    }

    /* Risk Badges */
    .risk-low {
        background-color: #F0FDF4;
        color: #15803D;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .risk-medium {
        background-color: #FEFCE8;
        color: #A16207;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .risk-high {
        background-color: #FFF7ED;
        color: #C2410C;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .risk-critical {
        background-color: #FEF2F2;
        color: #B91C1C;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #FCA5A5;
    }

    /* Modern Card Container */
    .pro-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }

    /* Policy Evaluation Hero Verdict Banners */
    .verdict-hero {
        border-radius: 12px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .verdict-hero-allow {
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 2px solid #10B981;
    }
    .verdict-hero-deny {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 2px solid #EF4444;
    }
    .verdict-hero-approval {
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border: 2px solid #F59E0B;
    }
    .verdict-title {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .verdict-subtitle {
        font-size: 0.95rem;
        font-weight: 500;
    }

    /* Trace Pipeline Steps */
    .trace-step-item {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }
    .trace-step-item.step-pass {
        border-left: 4px solid #10B981;
    }
    .trace-step-item.step-fail {
        border-left: 4px solid #EF4444;
        background: #FEF2F2;
    }
    .trace-step-item.step-paused {
        border-left: 4px solid #F59E0B;
        background: #FFFBEB;
    }

    /* Subtle Dividers */
    hr {
        margin: 1.5rem 0 !important;
        border: none !important;
        border-top: 1px solid #E2E8F0 !important;
    }
</style>
"""

def inject_custom_styles():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

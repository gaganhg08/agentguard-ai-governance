"""
Generates enterprise-grade, high-resolution UI screenshots for AgentGuard documentation.
Renders pixel-perfect visual previews of all 7 key platform views into docs/screenshots/.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMI = "C:/Windows/Fonts/segoeui.ttf"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"

def get_fonts():
    try:
        f_title = ImageFont.truetype(FONT_BOLD, 22)
        f_sub = ImageFont.truetype(FONT_REGULAR, 13)
        f_h2 = ImageFont.truetype(FONT_BOLD, 15)
        f_body = ImageFont.truetype(FONT_REGULAR, 12)
        f_body_b = ImageFont.truetype(FONT_BOLD, 12)
        f_small = ImageFont.truetype(FONT_REGULAR, 10)
        f_small_b = ImageFont.truetype(FONT_BOLD, 10)
        f_kpi_val = ImageFont.truetype(FONT_BOLD, 26)
        f_mono = ImageFont.truetype(FONT_MONO, 11)
        f_mono_s = ImageFont.truetype(FONT_MONO, 9)
    except Exception:
        f_title = f_sub = f_h2 = f_body = f_body_b = f_small = f_small_b = f_kpi_val = f_mono = f_mono_s = ImageFont.load_default()
    return {
        "title": f_title, "sub": f_sub, "h2": f_h2, "body": f_body,
        "body_b": f_body_b, "small": f_small, "small_b": f_small_b,
        "kpi_val": f_kpi_val, "mono": f_mono, "mono_s": f_mono_s
    }

def create_base_canvas(active_nav="1. Overview"):
    w, h = 1380, 880
    im = Image.new("RGB", (w, h), "#F8FAFC")
    d = ImageDraw.Draw(im)
    fonts = get_fonts()

    # Browser Top Bar
    d.rectangle([0, 0, w, 36], fill="#1E293B")
    d.ellipse([14, 12, 24, 22], fill="#EF4444")
    d.ellipse([30, 12, 40, 22], fill="#F59E0B")
    d.ellipse([46, 12, 56, 22], fill="#10B981")

    # Address bar
    d.rounded_rectangle([180, 7, w - 180, 29], radius=5, fill="#0F172A")
    d.text((195, 10), "🔒 https://agentguard.local:8501 — AgentGuard Enterprise AI Security & Governance Platform", fill="#94A3B8", font=fonts["mono_s"])

    # Sidebar (Dark Navy)
    sb_w = 240
    d.rectangle([0, 36, sb_w, h], fill="#0B1120")
    d.line([sb_w, 36, sb_w, h], fill="#1E293B", width=1)

    # Logo
    d.rounded_rectangle([18, 52, 52, 86], radius=7, fill="#2563EB")
    d.text((25, 57), "AG", fill="#FFFFFF", font=fonts["title"])
    d.text((62, 54), "AgentGuard", fill="#FFFFFF", font=fonts["h2"])
    d.text((62, 72), "AI SECURITY GATEWAY", fill="#60A5FA", font=fonts["small_b"])

    d.line([16, 98, sb_w - 16, 98], fill="#1E293B", width=1)

    # Nav items
    nav_items = [
        "1. Overview", "2. AI Agents", "3. Security Policies",
        "4. Permissions & Roles", "5. Guardrails", "6. Policy Evaluation",
        "7. Human Approvals", "8. Audit Logs", "9. AI Playground", "10. Settings"
    ]
    cur_y = 110
    for nav in nav_items:
        is_active = (nav == active_nav)
        if is_active:
            d.rounded_rectangle([12, cur_y - 3, sb_w - 12, cur_y + 25], radius=6, fill="#1E293B")
            d.rectangle([12, cur_y - 1, 15, cur_y + 23], fill="#3B82F6")
            d.text((24, cur_y + 2), nav, fill="#60A5FA", font=fonts["body_b"])
        else:
            d.text((24, cur_y + 2), nav, fill="#94A3B8", font=fonts["body"])
        cur_y += 34

    # Sidebar bottom status box
    d.rounded_rectangle([14, h - 90, sb_w - 14, h - 20], radius=8, fill="#111827", outline="#1F2937")
    d.text((24, h - 82), "SYSTEM STATUS", fill="#9CA3AF", font=fonts["small_b"])
    d.ellipse([24, h - 64, 32, h - 56], fill="#10B981")
    d.text((38, h - 68), "ACTIVE ENFORCEMENT", fill="#F3F4F6", font=fonts["small_b"])
    d.text((24, h - 48), "Default-Deny • SHA-256 Chain", fill="#6B7280", font=fonts["small"])

    return im, d, fonts, sb_w + 28, 54

def draw_kpi(d, fonts, x, y, w, h, label, val, sub, top_color="#3B82F6", sub_color="#64748B"):
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill="#FFFFFF", outline="#E2E8F0")
    d.rounded_rectangle([x, y, x + w, y + 4], radius=2, fill=top_color)
    d.text((x + 14, y + 12), label.upper(), fill="#64748B", font=fonts["small_b"])
    d.text((x + 14, y + 28), str(val), fill="#0F172A", font=fonts["kpi_val"])
    d.text((x + 14, y + 66), sub, fill=sub_color, font=fonts["small"])

# 1. OVERVIEW SCREENSHOT
def make_overview():
    im, d, fonts, cx, cy = create_base_canvas("1. Overview")
    d.text((cx, cy), "🛡️ Security & Governance Overview", fill="#0F172A", font=fonts["title"])
    d.text((cx, cy + 28), "Real-time telemetry, agent fleet status, and policy interception metrics.", fill="#64748B", font=fonts["sub"])

    # 4 KPI Cards
    kw = 250
    kh = 88
    ky = cy + 56
    draw_kpi(d, fonts, cx, ky, kw, kh, "Total Registered Agents", "4", "● 3 Active Fleet Members", "#3B82F6", "#059669")
    draw_kpi(d, fonts, cx + kw + 16, ky, kw, kh, "Blocked Actions (DENY)", "14", "Security violations caught", "#EF4444", "#DC2626")
    draw_kpi(d, fonts, cx + (kw + 16) * 2, ky, kw, kh, "Pending Approvals", "2", "Requires human review", "#F59E0B", "#D97706")
    draw_kpi(d, fonts, cx + (kw + 16) * 3, ky, kw, kh, "Total Interceptions", "38", "Append-only SHA-256 audit trail", "#2563EB", "#2563EB")

    # Donut Chart Mock
    ch_y = ky + 104
    cw1 = 440
    d.rounded_rectangle([cx, ch_y, cx + cw1, ch_y + 240], radius=8, fill="#FFFFFF", outline="#E2E8F0")
    d.text((cx + 16, ch_y + 12), "Policy Decisions Breakdown", fill="#0F172A", font=fonts["h2"])
    # circle mock
    d.ellipse([cx + 60, ch_y + 50, cx + 220, ch_y + 210], fill="#059669")
    d.pieslice([cx + 60, ch_y + 50, cx + 220, ch_y + 210], 0, 120, fill="#DC2626")
    d.pieslice([cx + 60, ch_y + 50, cx + 220, ch_y + 210], 120, 160, fill="#D97706")
    d.ellipse([cx + 100, ch_y + 90, cx + 180, ch_y + 170], fill="#FFFFFF")
    d.text((cx + 125, ch_y + 122), "38", fill="#0F172A", font=fonts["h2"])
    # legend
    d.rectangle([cx + 250, ch_y + 80, cx + 262, ch_y + 92], fill="#059669")
    d.text((cx + 270, ch_y + 79), "ALLOW: 22 (58%)", fill="#0F172A", font=fonts["body"])
    d.rectangle([cx + 250, ch_y + 115, cx + 262, ch_y + 127], fill="#DC2626")
    d.text((cx + 270, ch_y + 114), "DENY: 14 (37%)", fill="#0F172A", font=fonts["body"])
    d.rectangle([cx + 250, ch_y + 150, cx + 262, ch_y + 162], fill="#D97706")
    d.text((cx + 270, ch_y + 149), "REQUIRE_APP: 2 (5%)", fill="#0F172A", font=fonts["body"])

    # Agent Activity Bars Mock
    cw2 = 600
    cx2 = cx + cw1 + 16
    d.rounded_rectangle([cx2, ch_y, cx2 + cw2, ch_y + 240], radius=8, fill="#FFFFFF", outline="#E2E8F0")
    d.text((cx2 + 16, ch_y + 12), "Agent Activity & Decision Distribution", fill="#0F172A", font=fonts["h2"])
    agents_bar = [
        ("Customer Support", 18, 12, 5, 1),
        ("Finance Agent", 12, 7, 3, 2),
        ("IT Admin Agent", 6, 3, 3, 0),
        ("Legacy Decommissioned", 2, 0, 2, 0)
    ]
    by = ch_y + 45
    for a_name, tot, al, dn, ap in agents_bar:
        d.text((cx2 + 16, by), a_name, fill="#334155", font=fonts["body_b"])
        # stacked bar
        bx = cx2 + 200
        bw = 360
        w_al = int(bw * (al / 20))
        w_dn = int(bw * (dn / 20))
        w_ap = int(bw * (ap / 20))
        d.rounded_rectangle([bx, by + 2, bx + w_al, by + 16], radius=3, fill="#059669")
        d.rounded_rectangle([bx + w_al, by + 2, bx + w_al + w_dn, by + 16], radius=3, fill="#DC2626")
        if w_ap > 0:
            d.rounded_rectangle([bx + w_al + w_dn, by + 2, bx + w_al + w_dn + w_ap, by + 16], radius=3, fill="#D97706")
        d.text((bx + bw + 10, by), f"{tot} req", fill="#64748B", font=fonts["small"])
        by += 44

    # Table of recent events
    ty = ch_y + 256
    d.text((cx, ty), "Recent Security Events & Telemetry Stream", fill="#0F172A", font=fonts["h2"])
    d.rounded_rectangle([cx, ty + 24, cx + cw1 + cw2 + 16, ty + 210], radius=8, fill="#FFFFFF", outline="#E2E8F0")
    # table headers
    d.rectangle([cx, ty + 24, cx + cw1 + cw2 + 16, ty + 56], fill="#F1F5F9")
    headers = [("TIMESTAMP (UTC)", 130), ("AI AGENT", 160), ("TARGET TOOL", 140), ("DECISION", 110), ("RISK", 80), ("ENFORCEMENT REASON", 400)]
    hx = cx + 14
    for h_txt, hw in headers:
        d.text((hx, ty + 34), h_txt, fill="#475569", font=fonts["small_b"])
        hx += hw

    rows = [
        ("2026-11-02 02:11:05", "Customer Support", "search_faq", "ALLOW", "LOW", "Action compliant with RBAC permissions and security guardrails."),
        ("2026-11-02 02:10:48", "Customer Support", "request_refund", "ALLOW", "MEDIUM", "Auto-approved within refund threshold cap ($45.00 <= $100.00)."),
        ("2026-11-02 02:09:30", "Finance Agent", "approve_refund", "REQUIRE_APPROVAL", "HIGH", "High-consequence action requires dual-control human authorization."),
        ("2026-11-02 02:08:12", "Legacy Decommissioned", "read_customer_data", "DENY", "HIGH", "Access Denied: Agent is DEACTIVATED (Default-Deny)."),
        ("2026-11-02 02:07:05", "Customer Support", "cat /etc/passwd", "DENY", "CRITICAL", "Security Alert: Tool 'cat /etc/passwd' is not registered in system catalog.")
    ]
    ry = ty + 62
    for ts, ag, tl, dc, rk, rsn in rows:
        rx = cx + 14
        d.text((rx, ry), ts, fill="#64748B", font=fonts["small"])
        d.text((rx + 130, ry), ag, fill="#0F172A", font=fonts["small_b"])
        d.text((rx + 290, ry), tl, fill="#2563EB", font=fonts["mono_s"])
        # Badge
        badge_bg = "#ECFDF5" if dc == "ALLOW" else ("#FFFBEB" if dc == "REQUIRE_APPROVAL" else "#FEF2F2")
        badge_fg = "#065F46" if dc == "ALLOW" else ("#92400E" if dc == "REQUIRE_APPROVAL" else "#991B1B")
        d.rounded_rectangle([rx + 430, ry - 2, rx + 430 + 75, ry + 14], radius=4, fill=badge_bg)
        d.text((rx + 436, ry), dc, fill=badge_fg, font=fonts["small_b"])
        d.text((rx + 540, ry), rk, fill="#64748B", font=fonts["small"])
        d.text((rx + 620, ry), rsn[:65] + "...", fill="#334155", font=fonts["small"])
        d.line([cx, ry + 20, cx + cw1 + cw2 + 16, ry + 20], fill="#F1F5F9", width=1)
        ry += 27

    im.save(os.path.join(OUTPUT_DIR, "overview.png"))

# 2. AGENT MANAGEMENT SCREENSHOT
def make_agent_management():
    im, d, fonts, cx, cy = create_base_canvas("2. AI Agents")
    d.text((cx, cy), "🤖 AI Agent Management & Directory", fill="#0F172A", font=fonts["title"])
    d.text((cx, cy + 28), "Register, inspect, edit, monitor, activate, and deactivate enterprise AI agent identities.", fill="#64748B", font=fonts["sub"])

    # Tabs row
    ty = cy + 56
    tabs = ["📋 Registered Agents", "🔍 Agent Details & Activity", "✏️ Edit Agent", "➕ Register New Agent"]
    tx = cx
    for i, t in enumerate(tabs):
        if i == 0:
            d.rounded_rectangle([tx, ty, tx + 160, ty + 28], radius=5, fill="#2563EB")
            d.text((tx + 12, ty + 6), t, fill="#FFFFFF", font=fonts["small_b"])
        else:
            d.rounded_rectangle([tx, ty, tx + 160, ty + 28], radius=5, fill="#E2E8F0")
            d.text((tx + 12, ty + 6), t, fill="#475569", font=fonts["small"])
        tx += 170

    # Search and filter card
    fy = ty + 38
    d.rounded_rectangle([cx, fy, cx + 1056, fy + 58], radius=8, fill="#FFFFFF", outline="#E2E8F0")
    d.text((cx + 14, fy + 8), "Search by Agent Name or ID", fill="#64748B", font=fonts["small_b"])
    d.rounded_rectangle([cx + 14, fy + 24, cx + 380, fy + 48], radius=5, fill="#F8FAFC", outline="#CBD5E1")
    d.text((cx + 24, fy + 30), "🔍 Search agents...", fill="#94A3B8", font=fonts["small"])

    d.text((cx + 400, fy + 8), "Role Filter", fill="#64748B", font=fonts["small_b"])
    d.rounded_rectangle([cx + 400, fy + 24, cx + 600, fy + 48], radius=5, fill="#F8FAFC", outline="#CBD5E1")
    d.text((cx + 410, fy + 30), "All Roles ▾", fill="#0F172A", font=fonts["small"])

    d.text((cx + 620, fy + 8), "Status Filter", fill="#64748B", font=fonts["small_b"])
    d.rounded_rectangle([cx + 620, fy + 24, cx + 800, fy + 48], radius=5, fill="#F8FAFC", outline="#CBD5E1")
    d.text((cx + 630, fy + 30), "All Statuses ▾", fill="#0F172A", font=fonts["small"])

    # Agent Fleet Cards
    ay = fy + 72
    agents = [
        ("agent-support-01", "Customer Support Agent", "Customer Support", True, "Autonomous customer inquiry triage, FAQ lookups, and standard refunds.", "18 evals", "12 ALLOW"),
        ("agent-finance-01", "Finance & Disbursement Agent", "Finance", True, "Processes payment batches, invoice reconciliations, and high-value approvals.", "12 evals", "7 ALLOW"),
        ("agent-it-01", "IT Administration Agent", "IT Administrator", True, "Manages infrastructure provisioning, diagnostic telemetry, and daemon restarts.", "6 evals", "3 ALLOW"),
        ("agent-inactive-demo", "Decommissioned Legacy Bot", "Analytics", False, "Decommissioned legacy agent retained for security regression testing.", "2 evals", "0 ALLOW (Default-Deny)")
    ]

    for aid, aname, arole, is_act, desc, evs, alw in agents:
        d.rounded_rectangle([cx, ay, cx + 1056, ay + 110], radius=8, fill="#FFFFFF", outline="#E2E8F0")
        # badge
        if is_act:
            d.rounded_rectangle([cx + 14, ay + 12, cx + 85, ay + 28], radius=10, fill="#F0FDF4", outline="#BBF7D0")
            d.text((cx + 22, ay + 15), "● ACTIVE", fill="#166534", font=fonts["small_b"])
        else:
            d.rounded_rectangle([cx + 14, ay + 12, cx + 105, ay + 28], radius=10, fill="#FEF2F2", outline="#FECACA")
            d.text((cx + 22, ay + 15), "○ DEACTIVATED", fill="#991B1B", font=fonts["small_b"])

        d.text((cx + 120, ay + 12), aname, fill="#0F172A", font=fonts["h2"])
        d.text((cx + 14, ay + 38), f"Agent ID: {aid}  |  Role: {arole}  |  Telemetry: {evs} ({alw})", fill="#475569", font=fonts["small_b"])
        d.text((cx + 14, ay + 58), desc, fill="#64748B", font=fonts["body"])

        # buttons
        btn_txt = "Deactivate" if is_act else "Activate"
        btn_bg = "#EF4444" if is_act else "#10B981"
        d.rounded_rectangle([cx + 890, ay + 20, cx + 970, ay + 50], radius=5, fill=btn_bg)
        d.text((cx + 900, ay + 28), btn_txt, fill="#FFFFFF", font=fonts["small_b"])

        d.rounded_rectangle([cx + 980, ay + 20, cx + 1040, ay + 50], radius=5, fill="#F1F5F9", outline="#CBD5E1")
        d.text((cx + 995, ay + 28), "Edit", fill="#334155", font=fonts["small_b"])

        ay += 122

    im.save(os.path.join(OUTPUT_DIR, "agent_management.png"))

# 3. PERMISSION MATRIX SCREENSHOT
def make_permission_matrix():
    im, d, fonts, cx, cy = create_base_canvas("4. Permissions & Roles")
    d.text((cx, cy), "🛡️ Role-Based Access Control (RBAC) & Governance Matrix", fill="#0F172A", font=fonts["title"])
    d.text((cx, cy + 28), "Enforce least-privilege policies, assign roles to agents, and configure permission matrices.", fill="#64748B", font=fonts["sub"])

    # Legend banner
    my = cy + 56
    d.rounded_rectangle([cx, my, cx + 1056, my + 40], radius=6, fill="#F8FAFC", outline="#E2E8F0")
    d.text((cx + 14, my + 12), "Legend:  ✅ Granted  |  ✋ Approval Required  |  ❌ Denied (Default-Deny)", fill="#1E293B", font=fonts["body_b"])

    # Matrix Table Card
    ty = my + 50
    d.rounded_rectangle([cx, ty, cx + 1056, ty + 460], radius=8, fill="#FFFFFF", outline="#E2E8F0")
    # Table header
    d.rectangle([cx, ty, cx + 1056, ty + 45], fill="#0F172A")
    d.text((cx + 20, ty + 14), "PERMISSION / TOOL CAPABILITY", fill="#FFFFFF", font=fonts["small_b"])
    d.text((cx + 340, ty + 14), "CUSTOMER SUPPORT", fill="#FFFFFF", font=fonts["small_b"])
    d.text((cx + 580, ty + 14), "FINANCE", fill="#FFFFFF", font=fonts["small_b"])
    d.text((cx + 820, ty + 14), "IT ADMINISTRATOR", fill="#FFFFFF", font=fonts["small_b"])

    matrix_rows = [
        ("customer:read (read_customer_data)", "✅ Granted (Auto)", "❌ Denied", "❌ Denied"),
        ("ticket:create (search_faq, update_ticket)", "✅ Granted (Auto)", "❌ Denied", "❌ Denied"),
        ("refund:request (request_refund)", "✅ Granted (<= $100)", "❌ Denied", "❌ Denied"),
        ("refund:approve (approve_refund)", "❌ Denied", "✋ Approval Required", "❌ Denied"),
        ("payment:process (process_payment)", "❌ Denied", "✋ Approval Required", "❌ Denied"),
        ("system:manage (restart_service)", "❌ Denied", "❌ Denied", "✋ Approval Required"),
        ("network:configure (modify_firewall)", "❌ Denied", "❌ Denied", "✋ Approval Required"),
        ("analytics:export (generate_report)", "❌ Denied", "✅ Granted", "✅ Granted"),
        ("arbitrary:shell (exec_bash)", "❌ Denied (Default-Deny)", "❌ Denied (Default-Deny)", "❌ Denied (Default-Deny)")
    ]

    ry = ty + 50
    for perm, cs, fn, it in matrix_rows:
        d.text((cx + 20, ry + 8), perm, fill="#0F172A", font=fonts["mono_s"])
        # Customer support status
        c_color = "#059669" if "✅" in cs else ("#D97706" if "✋" in cs else "#94A3B8")
        d.text((cx + 340, ry + 8), cs, fill=c_color, font=fonts["small_b"])
        # Finance
        f_color = "#059669" if "✅" in fn else ("#D97706" if "✋" in fn else "#94A3B8")
        d.text((cx + 580, ry + 8), fn, fill=f_color, font=fonts["small_b"])
        # IT Admin
        i_color = "#059669" if "✅" in it else ("#D97706" if "✋" in it else "#94A3B8")
        d.text((cx + 820, ry + 8), it, fill=i_color, font=fonts["small_b"])

        d.line([cx, ry + 36, cx + 1056, ry + 36], fill="#F1F5F9", width=1)
        ry += 42

    im.save(os.path.join(OUTPUT_DIR, "permission_matrix.png"))

# 4. POLICY EVALUATION SCREENSHOT
def make_policy_evaluation():
    im, d, fonts, cx, cy = create_base_canvas("6. Policy Evaluation")
    d.text((cx, cy), "⚖️ Policy Evaluation & Central Authorization Gateway", fill="#0F172A", font=fonts["title"])
    d.text((cx, cy + 28), "Zero-trust policy enforcement test bench. Evaluate identity, guardrails, RBAC, and approval gates.", fill="#64748B", font=fonts["sub"])

    # Presets Row
    py = cy + 56
    d.text((cx, py), "QUICK SECURITY PRESETS", fill="#64748B", font=fonts["small_b"])
    presets = ["🟢 Authorized Action", "🔴 Inactive Agent", "🔴 RBAC Violation", "🔴 Prompt Injection", "🟡 High-Value Payment"]
    px = cx
    for p in presets:
        d.rounded_rectangle([px, py + 14, px + 195, py + 42], radius=5, fill="#FFFFFF", outline="#CBD5E1")
        d.text((px + 10, py + 22), p, fill="#0F172A", font=fonts["small_b"])
        px += 205

    # 2 columns layout
    cy2 = py + 60
    col_w1 = 440
    d.rounded_rectangle([cx, cy2, cx + col_w1, cy2 + 480], radius=8, fill="#FFFFFF", outline="#E2E8F0")
    d.text((cx + 16, cy2 + 16), "🛠️ Configure Action Request", fill="#0F172A", font=fonts["h2"])

    fields = [
        ("1. Agent Identity", "Customer Support Agent (agent-support-01)"),
        ("2. Requested Tool / Capability", "process_payment (Financial Gateway)"),
        ("3. Target Resource", "disbursement:vendor-vault"),
        ("4. JSON Parameters", '{"amount": 1500.0, "vendor_id": "VEND-992"}')
    ]
    fy = cy2 + 48
    for f_lbl, f_val in fields:
        d.text((cx + 16, fy), f_lbl, fill="#475569", font=fonts["small_b"])
        d.rounded_rectangle([cx + 16, fy + 16, cx + col_w1 - 16, fy + 44], radius=5, fill="#F8FAFC", outline="#CBD5E1")
        d.text((cx + 26, fy + 24), f_val[:48], fill="#0F172A", font=fonts["small"])
        fy += 64

    d.rounded_rectangle([cx + 16, fy + 10, cx + col_w1 - 16, fy + 52], radius=6, fill="#2563EB")
    d.text((cx + 120, fy + 22), "Run Policy Evaluation ⚖️", fill="#FFFFFF", font=fonts["body_b"])

    # Right column: Verdict Hero Banner
    rx = cx + col_w1 + 20
    rw = 596
    d.rounded_rectangle([rx, cy2, rx + rw, cy2 + 480], radius=8, fill="#FFFFFF", outline="#E2E8F0")

    # Verdict Hero Banner (DENY)
    d.rounded_rectangle([rx + 16, cy2 + 16, rx + rw - 16, cy2 + 100], radius=8, fill="#FEF2F2", outline="#EF4444")
    d.text((rx + 30, cy2 + 28), "STATUS: BLOCKED / DENIED ❌", fill="#991B1B", font=fonts["title"])
    d.text((rx + 30, cy2 + 62), "Cross-role RBAC violation: Role 'Customer Support' is forbidden from executing financial payments.", fill="#B91C1C", font=fonts["small"])

    # Evaluation Details
    ey = cy2 + 115
    d.text((rx + 16, ey), "🔬 Step-by-Step Security Governance Trace", fill="#0F172A", font=fonts["h2"])

    trace_steps = [
        ("✅ 1. Agent Identity Verification", "Agent 'agent-support-01' found in registry and status is ACTIVE.", "#059669", "#ECFDF5"),
        ("✅ 2. Guardrails Threat Analysis", "Zero prompt injection keywords or shell metacharacters detected.", "#059669", "#ECFDF5"),
        ("❌ 3. Role-Based Access Control", "Action 'process_payment' is NOT granted to role 'Customer Support'. (Default-Deny)", "#DC2626", "#FEF2F2"),
        ("⏭️ 4. Human Approval Gateway", "Skipped: Preceding RBAC check failed. Enforcement decision is final.", "#64748B", "#F1F5F9"),
        ("🔒 5. Cryptographic Audit Commitment", "Policy verdict permanently sealed in append-only SHA-256 ledger.", "#2563EB", "#EFF6FF")
    ]
    ty2 = ey + 30
    for s_title, s_desc, s_color, s_bg in trace_steps:
        d.rounded_rectangle([rx + 16, ty2, rx + rw - 16, ty2 + 48], radius=6, fill=s_bg, outline=s_color)
        d.text((rx + 28, ty2 + 8), s_title, fill=s_color, font=fonts["small_b"])
        d.text((rx + 28, ty2 + 26), s_desc, fill="#334155", font=fonts["small"])
        ty2 += 56

    im.save(os.path.join(OUTPUT_DIR, "policy_evaluation.png"))

# 5. APPROVAL CENTER SCREENSHOT
def make_approval_center():
    im, d, fonts, cx, cy = create_base_canvas("7. Human Approvals")
    d.text((cx, cy), "✋ Human-in-the-Loop Approval Center", fill="#0F172A", font=fonts["title"])
    d.text((cx, cy + 28), "Dual-control governance for high-risk operations. Review, authorize, or reject paused actions.", fill="#64748B", font=fonts["sub"])

    # KPI row
    kw = 250
    kh = 88
    ky = cy + 56
    draw_kpi(d, fonts, cx, ky, kw, kh, "Pending Reviews", "2", "Awaiting human sign-off", "#F59E0B", "#D97706")
    draw_kpi(d, fonts, cx + kw + 16, ky, kw, kh, "Approved Actions", "8", "Authorized by reviewers", "#10B981", "#059669")
    draw_kpi(d, fonts, cx + (kw + 16) * 2, ky, kw, kh, "Rejected Actions", "3", "Blocked by reviewers", "#EF4444", "#DC2626")
    draw_kpi(d, fonts, cx + (kw + 16) * 3, ky, kw, kh, "Dual-Control Policy", "ENFORCED", "Self-approval strictly barred", "#2563EB", "#2563EB")

    # Pending Card
    cy2 = ky + 104
    d.rounded_rectangle([cx, cy2, cx + 1056, cy2 + 380], radius=8, fill="#FFFFFF", outline="#F59E0B")
    d.rounded_rectangle([cx, cy2, cx + 6, cy2 + 380], radius=2, fill="#F59E0B")

    # Left: Ticket details
    d.text((cx + 20, cy2 + 16), "🎫 Request ID: req_9021a8f", fill="#0F172A", font=fonts["h2"])
    d.text((cx + 20, cy2 + 36), "Created: 2026-11-02 02:09:30 UTC  |  Priority: High-Consequence Action", fill="#64748B", font=fonts["small"])

    d.rounded_rectangle([cx + 20, cy2 + 58, cx + 540, cy2 + 140], radius=6, fill="#F8FAFC", outline="#E2E8F0")
    d.text((cx + 30, cy2 + 68), "Requesting Agent: Finance & Disbursement Agent (agent-finance-01)", fill="#0F172A", font=fonts["small_b"])
    d.text((cx + 30, cy2 + 88), "Requested Action: approve_refund  |  Target: refund:REF-8821", fill="#2563EB", font=fonts["mono_s"])
    d.text((cx + 30, cy2 + 108), "Assigned Role: Finance  |  Risk Level: HIGH", fill="#D97706", font=fonts["small_b"])

    d.rounded_rectangle([cx + 20, cy2 + 150, cx + 540, cy2 + 220], radius=6, fill="#FFFBEB", outline="#FDE68A")
    d.text((cx + 30, cy2 + 160), "PAUSE JUSTIFICATION / TRIGGER POLICY", fill="#92400E", font=fonts["small_b"])
    d.text((cx + 30, cy2 + 180), "Financial action exceeds auto-threshold ($750.00 > $500.00).", fill="#78350F", font=fonts["body"])
    d.text((cx + 30, cy2 + 198), "Mandatory dual-control human authorization required before fund release.", fill="#78350F", font=fonts["small"])

    d.text((cx + 20, cy2 + 230), "Action Parameters Payload (JSON):", fill="#475569", font=fonts["small_b"])
    d.rounded_rectangle([cx + 20, cy2 + 248, cx + 540, cy2 + 350], radius=6, fill="#0F172A")
    d.text((cx + 30, cy2 + 260), '{\n  "refund_id": "REF-8821",\n  "amount": 750.0,\n  "customer_id": "CUST-9912",\n  "reason": "Damaged goods return"\n}', fill="#38BDF8", font=fonts["mono"])

    # Right: Review Console
    rx = cx + 570
    d.text((rx, cy2 + 16), "✍️ Dual-Control Authorization Console", fill="#0F172A", font=fonts["h2"])
    d.text((rx, cy2 + 36), "Authorized human reviewers must sign off before execution.", fill="#64748B", font=fonts["small"])

    d.text((rx, cy2 + 68), "Human Reviewer Identity", fill="#475569", font=fonts["small_b"])
    d.rounded_rectangle([rx, cy2 + 86, rx + 460, cy2 + 116], radius=5, fill="#F8FAFC", outline="#CBD5E1")
    d.text((rx + 12, cy2 + 94), "security_lead_alice@enterprise.corp", fill="#0F172A", font=fonts["small"])

    d.text((rx, cy2 + 130), "Review Justification / Decision Notes", fill="#475569", font=fonts["small_b"])
    d.rounded_rectangle([rx, cy2 + 148, rx + 460, cy2 + 230], radius=5, fill="#F8FAFC", outline="#CBD5E1")
    d.text((rx + 12, cy2 + 158), "Verified physical return manifest with warehouse.\nAuthorizing standard merchant reimbursement.", fill="#0F172A", font=fonts["small"])

    # Anti self-approval alert
    d.rounded_rectangle([rx, cy2 + 242, rx + 460, cy2 + 286], radius=6, fill="#FEF2F2", outline="#FECACA")
    d.text((rx + 12, cy2 + 252), "⚠️ Anti-Self-Approval Enforcement: Submissions by agent identity are automatically blocked.", fill="#991B1B", font=fonts["small_b"])

    # Buttons
    d.rounded_rectangle([rx, cy2 + 304, rx + 220, cy2 + 348], radius=6, fill="#059669")
    d.text((rx + 45, cy2 + 318), "Approve Action ✅", fill="#FFFFFF", font=fonts["body_b"])

    d.rounded_rectangle([rx + 240, cy2 + 304, rx + 460, cy2 + 348], radius=6, fill="#DC2626")
    d.text((rx + 290, cy2 + 318), "Reject Action ❌", fill="#FFFFFF", font=fonts["body_b"])

    im.save(os.path.join(OUTPUT_DIR, "approval_center.png"))

# 6. AUDIT LOGS SCREENSHOT
def make_audit_logs():
    im, d, fonts, cx, cy = create_base_canvas("8. Audit Logs")
    d.text((cx, cy), "📜 Tamper-Evident Cryptographic Audit Trail", fill="#0F172A", font=fonts["title"])
    d.text((cx, cy + 28), "Immutable append-only ledger of every policy interception. Protected by SHA-256 cryptographic hash chaining.", fill="#64748B", font=fonts["sub"])

    # Compliance banner
    by = cy + 56
    d.rounded_rectangle([cx, by, cx + 1056, by + 50], radius=8, fill="#F0FDF4", outline="#BBF7D0")
    d.text((cx + 14, by + 10), "🔒 Append-Only Immutable Security Ledger", fill="#166534", font=fonts["body_b"])
    d.text((cx + 14, by + 28), "All security decisions are permanently committed to an immutable ledger chained via SHA-256 hashes.", fill="#15803D", font=fonts["small"])

    # Toolbar
    ty = by + 60
    d.rounded_rectangle([cx, ty, cx + 320, ty + 36], radius=5, fill="#2563EB")
    d.text((cx + 14, ty + 10), "🔒 Run Cryptographic Hash-Chain Audit", fill="#FFFFFF", font=fonts["small_b"])

    d.rounded_rectangle([cx + 340, ty, cx + 580, ty + 36], radius=5, fill="#FFFFFF", outline="#CBD5E1")
    d.text((cx + 354, ty + 10), "📥 Export Audit Trail (CSV / JSON)", fill="#0F172A", font=fonts["small_b"])

    # Filter row
    fy = ty + 46
    d.rounded_rectangle([cx, fy, cx + 1056, fy + 48], radius=6, fill="#FFFFFF", outline="#E2E8F0")
    d.text((cx + 14, fy + 16), "🔍 Filter:", fill="#64748B", font=fonts["small_b"])
    d.text((cx + 70, fy + 16), "Agent: All Agents ▾", fill="#0F172A", font=fonts["small"])
    d.text((cx + 250, fy + 16), "Decision: All Decisions ▾", fill="#0F172A", font=fonts["small"])
    d.text((cx + 460, fy + 16), "Sort: Newest First ▾", fill="#0F172A", font=fonts["small"])

    # Table of chained records
    tbl_y = fy + 58
    d.rounded_rectangle([cx, tbl_y, cx + 1056, tbl_y + 360], radius=8, fill="#FFFFFF", outline="#E2E8F0")
    d.rectangle([cx, tbl_y, cx + 1056, tbl_y + 36], fill="#F1F5F9")
    headers = [("ID", 40), ("TIMESTAMP (UTC)", 130), ("AGENT", 160), ("ACTION", 130), ("DECISION", 100), ("RISK", 70), ("SHA-256 HASH", 200), ("STATUS", 100)]
    hx = cx + 14
    for h_txt, hw in headers:
        d.text((hx, tbl_y + 12), h_txt, fill="#475569", font=fonts["small_b"])
        hx += hw

    records = [
        ("38", "2026-11-02 02:11:05", "Customer Support", "search_faq", "ALLOW", "LOW", "e4a291f09c2a8b3...", "EXECUTED"),
        ("37", "2026-11-02 02:10:48", "Customer Support", "request_refund", "ALLOW", "MED", "8f30b910e52aa1c...", "EXECUTED"),
        ("36", "2026-11-02 02:09:30", "Finance Agent", "approve_refund", "REQ_APPR", "HIGH", "7c11a049fbb1389...", "PAUSED"),
        ("35", "2026-11-02 02:08:12", "Legacy Bot", "read_customer", "DENY", "HIGH", "5a89ee120fa2417...", "BLOCKED"),
        ("34", "2026-11-02 02:07:05", "Customer Support", "cat /etc/passwd", "DENY", "CRIT", "29b8f041ea55018...", "BLOCKED"),
        ("33", "2026-11-02 02:06:40", "IT Admin Agent", "restart_service", "ALLOW", "HIGH", "11d4e908cc3144a...", "EXECUTED"),
        ("32", "2026-11-02 02:05:15", "Finance Agent", "process_payment", "ALLOW", "HIGH", "05fa3910bb42881...", "EXECUTED")
    ]
    ry = tbl_y + 44
    for rid, ts, ag, ac, dc, rk, hsh, st_txt in records:
        rx = cx + 14
        d.text((rx, ry), f"#{rid}", fill="#64748B", font=fonts["small"])
        d.text((rx + 40, ry), ts, fill="#64748B", font=fonts["small"])
        d.text((rx + 170, ry), ag, fill="#0F172A", font=fonts["small_b"])
        d.text((rx + 330, ry), ac, fill="#2563EB", font=fonts["mono_s"])

        badge_bg = "#ECFDF5" if "ALLOW" in dc else ("#FFFBEB" if "APPR" in dc else "#FEF2F2")
        badge_fg = "#065F46" if "ALLOW" in dc else ("#92400E" if "APPR" in dc else "#991B1B")
        d.rounded_rectangle([rx + 460, ry - 2, rx + 460 + 65, ry + 14], radius=4, fill=badge_bg)
        d.text((rx + 466, ry), dc, fill=badge_fg, font=fonts["small_b"])

        d.text((rx + 560, ry), rk, fill="#64748B", font=fonts["small"])
        d.text((rx + 630, ry), hsh, fill="#059669", font=fonts["mono_s"])
        d.text((rx + 830, ry), st_txt, fill="#334155", font=fonts["small_b"])

        d.line([cx, ry + 22, cx + 1056, ry + 22], fill="#F1F5F9", width=1)
        ry += 29

    im.save(os.path.join(OUTPUT_DIR, "audit_logs.png"))

# 7. AI PLAYGROUND SCREENSHOT
def make_playground():
    im, d, fonts, cx, cy = create_base_canvas("9. AI Playground")
    d.text((cx, cy), "🧪 Autonomous AI Agent Playground & Tool Sandbox", fill="#0F172A", font=fonts["title"])
    d.text((cx, cy + 28), "Controlled tool execution sandbox. Runs 100% offline without requiring paid API keys.", fill="#64748B", font=fonts["sub"])

    # Zero-Trust Alert
    by = cy + 56
    d.rounded_rectangle([cx, by, cx + 1056, by + 46], radius=6, fill="#F0FDF4", outline="#BBF7D0")
    d.text((cx + 14, by + 8), "🛡️ Zero-Trust Tool Execution Architecture", fill="#166534", font=fonts["body_b"])
    d.text((cx + 14, by + 26), "The LLM never directly executes tools. Every action proposal is intercepted and governed by the backend policy engine.", fill="#15803D", font=fonts["small"])

    # Presets
    py = by + 56
    d.text((cx, py), "INTERACTIVE TEST SCENARIOS", fill="#64748B", font=fonts["small_b"])
    scenarios = [
        ("🟢 1. Support Reads Customer Info", "read_customer_data"),
        ("🟢 2. Support Requests Refund", "$45 refund"),
        ("🟡 3. Finance Approves Refund", "$750 approval"),
        ("🔴 4. Inactive Agent Action", "Deactivated bot"),
        ("🔴 5. Unknown Rogue Tool", "exec_shell"),
        ("🔴 6. Prompt Injection Attack", "SQL jailbreak")
    ]
    sx = cx
    sy = py + 16
    for i, (s_title, s_sub) in enumerate(scenarios):
        d.rounded_rectangle([sx, sy, sx + 168, sy + 44], radius=6, fill="#FFFFFF", outline="#CBD5E1")
        d.text((sx + 8, sy + 8), s_title[:22], fill="#0F172A", font=fonts["small_b"])
        d.text((sx + 8, sy + 24), s_sub, fill="#64748B", font=fonts["small"])
        sx += 177

    # Chat execution stream
    cy2 = sy + 58
    d.text((cx, cy2), "💬 Agent Execution & Interception Stream", fill="#0F172A", font=fonts["h2"])

    # User Directive Box
    dy = cy2 + 24
    d.rounded_rectangle([cx, dy, cx + 1056, dy + 42], radius=6, fill="#F1F5F9", outline="#3B82F6")
    d.rounded_rectangle([cx, dy, cx + 4, dy + 42], radius=2, fill="#3B82F6")
    d.text((cx + 16, dy + 6), "USER DIRECTIVE", fill="#475569", font=fonts["small_b"])
    d.text((cx + 16, dy + 22), "Customer order ORD-9821 was returned damaged, please issue a $45 refund.", fill="#0F172A", font=fonts["body_b"])

    # Interception Card
    iy = dy + 52
    d.rounded_rectangle([cx, iy, cx + 1056, iy + 250], radius=8, fill="#FFFFFF", outline="#E2E8F0")

    # Left: Agent Proposal
    d.text((cx + 20, iy + 16), "1. Autonomous AI Agent Proposal", fill="#0F172A", font=fonts["h2"])
    d.text((cx + 20, iy + 40), "Agent: Customer Support Agent (agent-support-01)", fill="#334155", font=fonts["small_b"])
    d.text((cx + 20, iy + 60), "Planned Action: tool: request_refund", fill="#2563EB", font=fonts["mono_s"])
    d.text((cx + 20, iy + 80), "Target Resource: order:ORD-9821", fill="#475569", font=fonts["mono_s"])
    d.text((cx + 20, iy + 104), "Proposed Parameters (JSON):", fill="#64748B", font=fonts["small_b"])
    d.rounded_rectangle([cx + 20, iy + 120, cx + 460, iy + 190], radius=6, fill="#0F172A")
    d.text((cx + 30, iy + 130), '{\n  "order_id": "ORD-9821",\n  "amount": 45.0,\n  "reason": "Damaged goods return"\n}', fill="#38BDF8", font=fonts["mono"])

    # Right: Policy Enforcement Verdict
    rx = cx + 490
    d.text((rx, iy + 16), "2. AgentGuard Policy Enforcement", fill="#0F172A", font=fonts["h2"])
    d.rounded_rectangle([rx, iy + 40, rx + 540, iy + 90], radius=6, fill="#ECFDF5", outline="#10B981")
    d.text((rx + 14, iy + 48), "STATUS: ALLOWED ✅", fill="#065F46", font=fonts["h2"])
    d.text((rx + 14, iy + 70), "Action compliant with RBAC permissions and security guardrails.", fill="#047857", font=fonts["small"])

    d.text((rx, iy + 104), "Applicable Policy: Support Agent Refund Ceiling Rule", fill="#0F172A", font=fonts["small_b"])
    d.text((rx, iy + 124), "Policy Rationale: Auto-approved within refund threshold cap ($45.00 <= $100.00).", fill="#334155", font=fonts["small"])
    d.text((rx, iy + 144), "Assessed Risk: LOW  |  Guardrails: Clean (0 flags)", fill="#059669", font=fonts["small_b"])

    # Bottom Execution Outcome
    d.line([cx + 20, iy + 202, cx + 1036, iy + 202], fill="#F1F5F9", width=1)
    d.text((cx + 20, iy + 212), "3. Controlled Execution Result:", fill="#0F172A", font=fonts["small_b"])
    d.text((cx + 220, iy + 212), "✅ Refund REF-7109 for $45.00 successfully processed for Order ORD-9821.", fill="#059669", font=fonts["small_b"])

    im.save(os.path.join(OUTPUT_DIR, "playground.png"))

if __name__ == "__main__":
    print("Generating screenshots...")
    make_overview()
    make_agent_management()
    make_permission_matrix()
    make_policy_evaluation()
    make_approval_center()
    make_audit_logs()
    make_playground()
    print("All 7 screenshots generated successfully in docs/screenshots/")

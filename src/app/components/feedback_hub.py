"""Voice of the Industry & Live Telemetry Hub Component.

Renders verified practitioner reviews, interactive feedback submission,
aggregate community metrics, and real-time mobile push webhook controls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from src.app.theme import (
    COLOR_BORDER,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_CANOPY_GREEN,
    COLOR_CARD_BG,
    COLOR_INK_GREEN,
    COLOR_MOSS_GREY,
    COLOR_PALE_SAGE,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from src.utils.telemetry import (
    dispatch_webhook_alert,
    get_all_feedback,
    get_feedback_summary,
    record_feedback,
    verify_feedback_chain,
)


def render_feedback_hub_section(project_root: Any = None) -> None:
    """Render the complete Voice of the Industry and Telemetry panel."""
    summary = get_feedback_summary()
    chain = get_all_feedback()
    is_valid_chain, chain_msg = verify_feedback_chain()

    st.markdown(
        f"""
        <div style="background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h3 style="margin: 0; color: {COLOR_BRAND_PRIMARY}; font-size: 1.25rem;">
                        🌿 Voice of the Industry & Community Pulse
                    </h3>
                    <p style="margin: 4px 0 0 0; color: {COLOR_TEXT_SECONDARY}; font-size: 0.85rem;">
                        Verified reviews from automotive materials planners, plant directors, and supply chain evaluators.
                    </p>
                </div>
                <div style="display: flex; gap: 16px; align-items: center;">
                    <div style="text-align: right;">
                        <span style="font-size: 1.4rem; font-weight: 700; color: {COLOR_BRAND_PRIMARY};">⭐ {summary.get('avg_rating', 5.0)}</span>
                        <span style="font-size: 0.8rem; color: {COLOR_TEXT_SECONDARY};"> / 5.0</span>
                        <div style="font-size: 0.75rem; color: {COLOR_CANOPY_GREEN}; font-weight: 600;">
                            {summary.get('total_reviews', 0)} Verified Reviews ({summary.get('stars_5_pct', 100)}% 5-Star)
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### ✍️ Submit Practitioner Verdict / Peer Review")
        st.caption("Leave your critique or operational feedback. Submissions are cryptographically signed.")

        with st.form("industry_feedback_form", clear_on_submit=True):
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                rating_choice = st.selectbox(
                    "Rating",
                    options=[5, 4, 3, 2, 1],
                    format_func=lambda x: f"{'⭐' * x} ({x}/5 Stars)",
                    index=0,
                )
            with r_col2:
                persona_choice = st.selectbox(
                    "Professional Role",
                    options=[
                        "Automotive Materials Planner",
                        "Plant Operations Director",
                        "Supply Chain Analyst",
                        "Data Engineer / Judge",
                        "Logistics Lead (Pune/Chakan)",
                        "Open-Source Contributor",
                        "Other",
                    ],
                    index=0,
                )

            org_input = st.text_input(
                "Organization / Facility (Optional)",
                placeholder="e.g. Chakan Tier-1 Ancillary / OEM Centre / Devfolio Judge",
            )

            scenario_choice = st.selectbox(
                "Scenario or Module Tested",
                options=[
                    "Entire Materials Cockpit",
                    "BYOD Ingestion Studio (Tab 8)",
                    "Inbound Triage & Overrides (Tab 1)",
                    "What-If Crisis Simulator (Tab 3)",
                    "10k Scale Benchmark (Tab 4)",
                    "Financial ROI Engine (Tab 5)",
                ],
                index=0,
            )

            feedback_text = st.text_area(
                "Your Feedback / Operational Critique",
                placeholder="What did you think of the True ATP formula, false alarm clearance, or Exasol query latency? How does this match real factory floor challenges?",
                height=110,
            )

            submit_btn = st.form_submit_button("🚀 Cryptographically Sign & Post Review", use_container_width=True)

            if submit_btn:
                if not feedback_text.strip():
                    st.warning("Please provide a short sentence of feedback.")
                else:
                    new_block = record_feedback(
                        rating=rating_choice,
                        persona=persona_choice,
                        organization=org_input if org_input.strip() else "Verified Community Evaluator",
                        feedback_text=feedback_text.strip(),
                        scenario_tested=scenario_choice,
                    )
                    st.success(f"Review cryptographically recorded in Block #{new_block['index']}! SHA: {new_block['hash'][:16]}...")
                    st.rerun()

    with col2:
        st.markdown("#### 📜 Verified Practitioner Review Wall")
        st.caption(f"Cryptographic Integrity: {'✅ ' + chain_msg if is_valid_chain else '❌ ' + chain_msg}")

        # Display reviews in reverse chronological order
        reversed_chain = list(reversed(chain))
        for block in reversed_chain[:4]:
            rating_stars = "⭐" * int(block.get("rating", 5))
            st.markdown(
                f"""
                <div style="background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-left: 4px solid {COLOR_BRAND_PRIMARY}; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div>
                            <span style="font-weight: 700; color: {COLOR_INK_GREEN}; font-size: 0.9rem;">{block.get('persona')}</span>
                            <span style="color: {COLOR_MOSS_GREY}; font-size: 0.8rem;"> — {block.get('organization')}</span>
                        </div>
                        <span style="font-size: 0.85rem;">{rating_stars}</span>
                    </div>
                    <p style="margin: 0 0 8px 0; color: {COLOR_TEXT_PRIMARY}; font-size: 0.85rem; font-style: italic; line-height: 1.4;">
                        "{block.get('feedback_text')}"
                    </p>
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.72rem; color: {COLOR_TEXT_SECONDARY};">
                        <span>Module: <b>{block.get('scenario_tested', 'Cockpit')}</b></span>
                        <code style="font-size: 0.7rem; color: {COLOR_CANOPY_GREEN};">Block #{block.get('index')} • {block.get('hash', '')[:10]}</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Collapsible Telemetry Webhook Integration Info
    with st.expander("📱 Live Push Notifications: See Real-Time Visits & Reviews on Your Phone"):
        st.markdown(
            """
            To receive **instant mobile push notifications** whenever an evaluator, judge, or materials planner
            submits a review or tests a scenario:
            
            1. Create an incoming webhook in **Discord** (Channel Settings $\\to$ Integrations $\\to$ Webhooks) or **Slack**.
            2. Add it to your `.env` file:
               ```bash
               MANGROVE_WEBHOOK_URL="https://discord.com/api/webhooks/your/webhook/url"
               ```
               *(On Streamlit Community Cloud, add it under **Settings $\\to$ Secrets** as `MANGROVE_WEBHOOK_URL = "..."`)*.
            3. Your phone will immediately receive a rich embed alert whenever activity occurs!
            """
        )
        test_ping_col1, test_ping_col2 = st.columns([1, 2])
        with test_ping_col1:
            if st.button("🔔 Send Test Notification", use_container_width=True):
                sent = dispatch_webhook_alert(
                    "TEST_PING",
                    {
                        "rating": 5,
                        "persona": "System Diagnostic Ping",
                        "organization": "Mangrove Health Check",
                        "feedback_text": "Live telemetry channel operational. Real-time push active.",
                        "scenario_tested": "Webhook Diagnostic",
                        "index": 0,
                        "hash": "test000000000000",
                    },
                )
                if sent:
                    st.success("Test push dispatched successfully to your configured webhook!")
                else:
                    st.info("No webhook URL configured or network unreachable. Set `MANGROVE_WEBHOOK_URL` in `.env` to enable.")

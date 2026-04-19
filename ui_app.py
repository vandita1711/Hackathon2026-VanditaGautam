import sys
from pathlib import Path

import gradio as gr
import json
import asyncio
import pandas as pd
import os
from pipelines.process_tickets import process_tickets_batch
from app.services.data_loader import DataLoader
from app.schemas.ticket import Ticket
from app.schemas.customer import Customer
from config import settings

class ShopWaveUI:
    def __init__(self):
        self.results = []
        self.customers_map = {}
        self.tickets = []

    def load_files(self, ticket_file, customer_file, order_file, product_file):
        """Loads uploaded JSON files into the app state."""
        if not all([ticket_file, customer_file, order_file, product_file]):
            return "ERROR: Please upload all required files (Tickets, Customers, Orders, Products)."
        
        try:
            # Move uploaded files to data directory for processing
            os.makedirs("data", exist_ok=True)
            for f, target in zip([ticket_file, customer_file, order_file, product_file], 
                                [settings.TICKET_DATA, settings.CUSTOMER_DATA, settings.ORDER_DATA, settings.PRODUCT_DATA]):
                with open(f.name, "r") as src, open(target, "w") as dst:
                    dst.write(src.read())

            self.tickets = DataLoader.load_collection(str(settings.TICKET_DATA), Ticket)
            all_customers = DataLoader.load_collection(str(settings.CUSTOMER_DATA), Customer)
            self.customers_map = {}
            
            # Build customer lookup map - support both ID and email
            for customer in all_customers:
                customer_data = customer.model_dump()
                # Map by customer_id
                if hasattr(customer, 'customer_id'):
                    self.customers_map[customer.customer_id] = customer_data
                # Map by email if it exists
                if hasattr(customer, 'email') and customer.email:
                    self.customers_map[customer.email] = customer_data
                # Also try 'name' field for legacy data
                if hasattr(customer, 'name'):
                    self.customers_map[customer.name] = customer_data
            
            return f"SUCCESS: Successfully loaded {len(self.tickets)} tickets, {len(all_customers)} customers, and product data."
        except Exception as e:
            return f"ERROR: Error loading files: {str(e)}"

    def run_analysis(self, num_tickets):
        """Runs the AutoGen orchestration pipeline with API analysis."""
        if not self.tickets:
            return (
                pd.DataFrame(columns=["Ticket ID", "Status", "Confidence", "Reasoning"]),
                "ERROR: No tickets loaded. Please upload data files first.",
                "Idle",
                self._empty_kpi_html(),
                self._empty_chart_html(),
                self._empty_intelligence_html()
            )

        try:
            # Convert to int and validate
            num_tickets = int(num_tickets) if num_tickets else 5
            num_tickets = max(1, min(num_tickets, len(self.tickets)))  # Ensure valid range
            
            # Limit to requested number of tickets
            tickets_to_process = self.tickets[:num_tickets]
            raw_tickets = [t.model_dump(by_alias=True) for t in tickets_to_process]
            
            status_text = f"RUNNING: Running AutoGen AI analysis on {len(raw_tickets)} tickets..."
            
            # Clear audit log before new run to show only fresh entries
            try:
                import os
                if os.path.exists(settings.AUDIT_LOG_PATH):
                    os.remove(settings.AUDIT_LOG_PATH)
            except Exception as e:
                print(f"Warning: Could not clear audit log: {e}")
            
            self.results = asyncio.run(
    process_tickets_batch(raw_tickets, self.customers_map)
)
            
            df_data = []
            metrics = {"total": len(self.results), "resolved": 0, "escalated": 0, "failed": 0, "confidence": []}
            
            for idx, res in enumerate(self.results):
                status = res.get("status", "error")
                confidence = res.get("confidence_score", 0.0)
                try:
                    confidence = float(confidence or 0.0)
                except Exception:
                    confidence = 0.0

                if status in {"resolved", "approved"}:
                    metrics["resolved"] += 1
                elif status in {"escalate", "escalated"}:
                    metrics["escalated"] += 1
                else:
                    metrics["failed"] += 1
                
                if confidence:
                    metrics["confidence"].append(confidence)
                
                reasoning = res.get("reasoning") or res.get("final_message") or "No reasoning available."
                reasoning = str(reasoning)[:80]

                # Color-code status with emoji badges
                status_upper = status.upper()
                if status in {"resolved", "approved"}:
                    status_display = f"🟢 {status_upper}"
                elif status in {"escalate", "escalated"}:
                    status_display = f"🔴 {status_upper}"
                else:
                    status_display = f"🟡 {status_upper}"

                # AI vs Rules badge
                is_autogen = res.get("reasoning") != "No reasoning available."
                source_display = "🤖 AutoGen" if is_autogen else "⚙️ Rules"

                df_data.append({
                   "Index": idx,
                   "Ticket ID": res.get("ticket_id"),
                   "Status": status_display,
                   "Confidence": f"{confidence:.0%}",
                   "Source": source_display,
                   "Reasoning": reasoning + "..."
                })
            
            df = pd.DataFrame(df_data)
            
            avg_confidence = sum(metrics["confidence"]) / len(metrics["confidence"]) if metrics["confidence"] else 0
            summary_md = (
                f"## ✅ Analysis Complete\n\n"
                f"**Tickets Processed:** {metrics['total']}\n\n"
                f"**Results Distribution:**\n"
                f"- 🟢 RESOLVED: {metrics['resolved']} ({metrics['resolved']/metrics['total']*100:.0f}%)\n"
                f"- 🔴 ESCALATED: {metrics['escalated']} ({metrics['escalated']/metrics['total']*100:.0f}%)\n"
                f"- 🟡 FAILED: {metrics['failed']} ({metrics['failed']/metrics['total']*100:.0f}%)\n\n"
                f"**Average Confidence:** {avg_confidence:.0%}"
            )
            status_text = "✅ Analysis complete! Review results above."

            kpi_html = self._build_kpi_html(metrics, avg_confidence)
            chart_html = self._build_chart_html(metrics)
            intelligence_html = self._build_intelligence_html(metrics, avg_confidence)
            
            return df, summary_md, status_text, kpi_html, chart_html, intelligence_html
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n\n{traceback.format_exc()}"
            print(f"ERROR in run_analysis: {error_detail}")
            error_msg = f"ERROR: {str(e)[:200]}"
            return (
                pd.DataFrame(columns=["Ticket ID", "Status", "Confidence", "Reasoning"]),
                f"ERROR: {error_detail[:500]}",
                error_msg,
                self._empty_kpi_html(),
                self._empty_chart_html(),
                self._empty_intelligence_html()
            )

    # ── KPI Cards ──────────────────────────────────────────────────────────────
    def _build_kpi_html(self, metrics, avg_confidence):
        total = metrics["total"]
        resolved_pct = metrics["resolved"] / total * 100 if total else 0
        escalated_pct = metrics["escalated"] / total * 100 if total else 0
        conf_pct = avg_confidence * 100
        return f"""
        <div style="display:flex;gap:16px;flex-wrap:wrap;margin:16px 0;">
          <div style="flex:1;min-width:140px;background:linear-gradient(135deg,#667eea,#764ba2);
                      border-radius:12px;padding:20px;color:white;box-shadow:0 4px 15px rgba(102,126,234,0.3);text-align:center;">
            <div style="font-size:2rem;font-weight:700;">{total}</div>
            <div style="font-size:0.85rem;opacity:0.9;margin-top:4px;">🎫 Total Tickets</div>
          </div>
          <div style="flex:1;min-width:140px;background:linear-gradient(135deg,#22c55e,#16a34a);
                      border-radius:12px;padding:20px;color:white;box-shadow:0 4px 15px rgba(34,197,94,0.3);text-align:center;">
            <div style="font-size:2rem;font-weight:700;">{resolved_pct:.0f}%</div>
            <div style="font-size:0.85rem;opacity:0.9;margin-top:4px;">✅ Resolved</div>
          </div>
          <div style="flex:1;min-width:140px;background:linear-gradient(135deg,#ef4444,#dc2626);
                      border-radius:12px;padding:20px;color:white;box-shadow:0 4px 15px rgba(239,68,68,0.3);text-align:center;">
            <div style="font-size:2rem;font-weight:700;">{escalated_pct:.0f}%</div>
            <div style="font-size:0.85rem;opacity:0.9;margin-top:4px;">🚨 Escalated</div>
          </div>
          <div style="flex:1;min-width:140px;background:linear-gradient(135deg,#f59e0b,#d97706);
                      border-radius:12px;padding:20px;color:white;box-shadow:0 4px 15px rgba(245,158,11,0.3);text-align:center;">
            <div style="font-size:2rem;font-weight:700;">{conf_pct:.0f}%</div>
            <div style="font-size:0.85rem;opacity:0.9;margin-top:4px;">🧠 Avg Confidence</div>
          </div>
        </div>
        """

    def _empty_kpi_html(self):
        return "<div style='color:#94a3b8;padding:16px;text-align:center;'>Run analysis to see KPI cards.</div>"

    # ── Pie Chart ──────────────────────────────────────────────────────────────
    def _build_chart_html(self, metrics):
        total = metrics["total"]
        if total == 0:
            return self._empty_chart_html()
        resolved = metrics["resolved"]
        escalated = metrics["escalated"]
        failed = metrics["failed"]
        # SVG donut chart
        def _slice(value, total, start_angle, color, label, emoji):
            if value == 0:
                return "", start_angle
            pct = value / total
            angle = pct * 360
            end_angle = start_angle + angle
            # Convert to radians
            import math
            r, cx, cy, ri = 80, 110, 110, 48
            s_rad = math.radians(start_angle - 90)
            e_rad = math.radians(end_angle - 90)
            x1, y1 = cx + r * math.cos(s_rad), cy + r * math.sin(s_rad)
            x2, y2 = cx + r * math.cos(e_rad), cy + r * math.sin(e_rad)
            xi1, yi1 = cx + ri * math.cos(s_rad), cy + ri * math.sin(s_rad)
            xi2, yi2 = cx + ri * math.cos(e_rad), cy + ri * math.sin(e_rad)
            large = 1 if angle > 180 else 0
            path = (f'<path d="M {x1:.2f} {y1:.2f} A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f} '
                    f'L {xi2:.2f} {yi2:.2f} A {ri} {ri} 0 {large} 0 {xi1:.2f} {yi1:.2f} Z" '
                    f'fill="{color}" />')
            return path, end_angle

        slices_data = [
            (resolved, "#22c55e", "Resolved", "✅"),
            (escalated, "#ef4444", "Escalated", "🚨"),
            (failed, "#f59e0b", "Failed", "🟡"),
        ]
        svg_paths = ""
        angle = 0
        for val, color, label, emoji in slices_data:
            path, angle = _slice(val, total, angle, color, label, emoji)
            svg_paths += path

        legend_items = "".join([
            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
            f'<span style="width:12px;height:12px;border-radius:3px;background:{color};display:inline-block;"></span>'
            f'<span style="font-size:0.85rem;color:#475569;">{emoji} {label}: <b>{val}</b> ({val/total*100:.0f}%)</span></div>'
            for val, color, label, emoji in slices_data if val > 0
        ])

        return f"""
        <div style="display:flex;align-items:center;gap:32px;background:#fff;border-radius:12px;
                    padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.07);margin:16px 0;flex-wrap:wrap;">
          <div>
            <div style="font-weight:600;color:#1e293b;margin-bottom:8px;">📊 Ticket Distribution</div>
            <svg width="220" height="220" viewBox="0 0 220 220">
              {svg_paths}
              <circle cx="110" cy="110" r="38" fill="white"/>
              <text x="110" y="106" text-anchor="middle" font-size="18" font-weight="700" fill="#1e293b">{total}</text>
              <text x="110" y="124" text-anchor="middle" font-size="10" fill="#64748b">tickets</text>
            </svg>
          </div>
          <div>{legend_items}</div>
        </div>
        """

    def _empty_chart_html(self):
        return "<div style='color:#94a3b8;padding:16px;text-align:center;'>Run analysis to see distribution chart.</div>"

    # ── System Intelligence ────────────────────────────────────────────────────
    def _build_intelligence_html(self, metrics, avg_confidence):
        total = metrics["total"]
        ai_count = metrics["resolved"] + metrics["escalated"]  # approximation: non-failed are AI-handled
        rules_count = metrics["failed"]
        ai_pct = ai_count / total * 100 if total else 0
        rules_pct = rules_count / total * 100 if total else 0
        conf_pct = avg_confidence * 100

        def bar(pct, color):
            return (f'<div style="background:#e2e8f0;border-radius:99px;height:10px;width:100%;margin-top:6px;">'
                    f'<div style="width:{pct:.0f}%;background:{color};border-radius:99px;height:10px;'
                    f'transition:width 0.6s ease;"></div></div>')

        return f"""
        <div style="background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.07);margin:16px 0;">
          <div style="font-weight:700;font-size:1rem;color:#1e293b;margin-bottom:16px;">🏆 System Intelligence</div>
          <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;">
              <span style="color:#475569;font-size:0.88rem;">🤖 AI Handled</span>
              <b style="color:#22c55e;">{ai_pct:.0f}%</b>
            </div>{bar(ai_pct, "#22c55e")}
          </div>
          <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;">
              <span style="color:#475569;font-size:0.88rem;">⚙️ Fallback / Rules Used</span>
              <b style="color:#f59e0b;">{rules_pct:.0f}%</b>
            </div>{bar(rules_pct, "#f59e0b")}
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;">
              <span style="color:#475569;font-size:0.88rem;">🧠 Avg Decision Confidence</span>
              <b style="color:#667eea;">{conf_pct:.0f}%</b>
            </div>{bar(conf_pct, "#667eea")}
          </div>
        </div>
        """

    def _empty_intelligence_html(self):
        return "<div style='color:#94a3b8;padding:16px;text-align:center;'>Run analysis to see system intelligence.</div>"

    # ── Existing helpers (unchanged) ───────────────────────────────────────────
    def _format_data(self, data):
        if data is None:
            return "None"
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            try:
                return json.dumps(data, indent=2, default=str)
            except Exception:
                return str(data)
        if isinstance(data, list):
            return json.dumps(data, indent=2, default=str)
        return str(data)

    def _format_plan(self, plan):
        if not isinstance(plan, list):
            return self._format_data(plan)
        lines = []
        for idx, step in enumerate(plan, start=1):
            tool_name = step.get("tool_name")
            params = step.get("parameters")
            lines.append(f"    {idx}. {tool_name}({self._format_data(params)})")
        return "\n".join(lines)

    def _format_tool_results(self, results):
        if not isinstance(results, list):
            return self._format_data(results)
        lines = []
        for result in results:
            tool = result.get("tool")
            status = result.get("status")
            output = result.get("output")
            lines.append(f"    - {tool}: {status}\n      output: {self._format_data(output)}")
        return "\n".join(lines)

    def _format_audit_trace(self, ticket_logs):
        formatted_lines = []
        for entry in ticket_logs:
            event_type = entry.get("event_type", "unknown")
            timestamp = entry.get("timestamp", "")
            data = entry.get("data", {})

            # ── Storytelling headings per event type ──────────────────────────
            section_icons = {
                "ticket_received":       "📥 Ticket Received",
                "autogen_started":       "🚀 AutoGen Started",
                "autogen_completed":     "✅ AutoGen Completed",
                "autogen_failed":        "❌ AutoGen Failed",
                "autogen_skipped":       "⏭️ AutoGen Skipped",
                "fallback_used":         "⚙️ Fallback / Rules Engine",
                "autogen_response":      "💬 AutoGen Raw Response",
                "plan_created":          "🔍 Planner Decision",
                "tools_executed":        "⚙️ Tool Execution",
                "resolution_completed":  "🧠 Final Reasoning & Resolution",
                "llm_review_completed":  "🔎 LLM Review Completed",
                "llm_review_failed":     "⚠️ LLM Review Failed",
                "policy_check":          "📋 Policy Check",
                "intermediate_reasoning":"💡 Intermediate Reasoning",
                "planner_decision":      "🔍 Planner Decision",
            }
            heading = section_icons.get(event_type, f"🔹 {event_type.replace('_', ' ').title()}")
            formatted_lines.append(f"\n{'='*60}")
            formatted_lines.append(f"  {heading}")
            formatted_lines.append(f"  🕒 {timestamp}")
            formatted_lines.append(f"{'='*60}")

            if event_type == "ticket_received":
                customer = data.get("customer") or {}
                customer_id = customer.get("customer_id") or customer.get("email") or "unknown"
                formatted_lines.append(f"  - Ticket accepted for customer: {customer_id}")
            elif event_type == "autogen_started":
                formatted_lines.append("  - AutoGen orchestration started.")
            elif event_type == "autogen_completed":
                formatted_lines.append(f"  - AutoGen completed. Final message: {data.get('final_message')}")
            elif event_type == "autogen_failed":
                formatted_lines.append(f"  - AutoGen failed: {data.get('error')}")
            elif event_type == "autogen_skipped":
                formatted_lines.append(f"  - AutoGen skipped: {data.get('reason')}")
            elif event_type == "fallback_used":
                formatted_lines.append(f"  - Deterministic fallback used (reason: {data.get('reason')})")
            elif event_type == "autogen_response":
                formatted_lines.append("  - AutoGen raw messages recorded.")
                formatted_lines.append(f"  - Messages: {self._format_data(data.get('raw_messages'))}")
            elif event_type == "plan_created":
                formatted_lines.append(f"  - Planner decision: {data.get('intent')}")
                formatted_lines.append("  - Tool plan:")
                formatted_lines.append(self._format_plan(data.get("plan")))
            elif event_type == "tools_executed":
                formatted_lines.append("  - Tool execution results:")
                formatted_lines.append(self._format_tool_results(data.get("results")))
            elif event_type == "resolution_completed":
                formatted_lines.append(f"  - Decision: {data.get('status')} with confidence {data.get('confidence_score')}")
                if data.get("escalation_team"):
                    formatted_lines.append(f"  - Escalation team: {data.get('escalation_team')}")
                if data.get("reasoning"):
                    formatted_lines.append(f"  - Reasoning: {data.get('reasoning')}")
                if data.get("final_message"):
                    formatted_lines.append(f"  - Final message: {data.get('final_message')}")
            elif event_type == "llm_review_completed":
                formatted_lines.append("  - LLM review completed.")
                formatted_lines.append(f"  - Response: {self._format_data(data.get('response'))}")
            elif event_type == "llm_review_failed":
                formatted_lines.append(f"  - LLM review failed: {data.get('error')}")
            elif event_type == "policy_check":
                check_name = data.get("check", "unknown")
                result = data.get("result", "unknown")
                details = data.get("details", "")
                formatted_lines.append(f"  - Policy check '{check_name}': {result}")
                if details:
                    formatted_lines.append(f"    Details: {details}")
            elif event_type == "intermediate_reasoning":
                reasoning = data.get("reasoning", "")
                step = data.get("step", "")
                formatted_lines.append(f"  - Intermediate reasoning ({step}): {reasoning}")
            elif event_type == "planner_decision":
                decision = data.get("decision", "")
                confidence = data.get("confidence", "")
                reasoning = data.get("reasoning", "")
                formatted_lines.append(f"  - Planner agent decision: {decision}")
                if confidence:
                    formatted_lines.append(f"    Confidence: {confidence}")
                if reasoning:
                    formatted_lines.append(f"    Reasoning: {reasoning}")

            formatted_lines.append("")

        return "\n".join(formatted_lines)

    def get_ticket_details(self, evt: gr.SelectData):
        """Fetches detailed trace for a selected ticket (row/cell click in results table)."""
        ticket_id = None

        # Gradio Dataframe .select() provides SelectData with index (row, col) and row_value
        if evt is not None and getattr(evt, "selected", True):
            if evt.row_value is not None and len(evt.row_value) >= 2:
                try:
                    index = int(evt.row_value[0])
                    if 0 <= index < len(self.results):
                        ticket_id = self.results[index].get("ticket_id")
                except (ValueError, TypeError):
                    pass
            if not ticket_id and evt.index is not None:
                try:
                    row_idx = evt.index[0] if isinstance(evt.index, (list, tuple)) else int(evt.index)
                    if 0 <= row_idx < len(self.results):
                        ticket_id = self.results[row_idx].get("ticket_id")
                except (ValueError, TypeError, IndexError):
                    pass

        if not ticket_id:
            return "No ticket selected. Click a row from the results table to view the audit trace."

        try:
            audit_path = settings.AUDIT_LOG_PATH
            if not os.path.exists(audit_path):
                return f"Audit log not found at {audit_path}. Run analysis first to generate logs."

            with open(audit_path, "r") as f:
                logs = json.load(f)

            ticket_logs = [log for log in logs if log.get("ticket_id") == ticket_id]
            ticket_logs.sort(key=lambda entry: entry.get("timestamp", ""))

            if not ticket_logs:
                # Show available tickets in the log for debugging
                available_tickets = set(log.get("ticket_id") for log in logs)
                return f"No audit trace found for ticket {ticket_id}. Available tickets in log: {sorted(available_tickets)}"

            return self._format_audit_trace(ticket_logs)
        except Exception as e:
            return f"Could not load audit trace: {str(e)}"

    def filter_results(self, filter_choice, full_df_state):
        """Filter the results table by status."""
        if full_df_state is None or full_df_state.empty:
            return full_df_state
        if filter_choice == "All":
            return full_df_state
        mask = full_df_state["Status"].str.contains(filter_choice.upper(), case=False, na=False)
        return full_df_state[mask].reset_index(drop=True)

def launch_ui():
    ui_logic = ShopWaveUI()

    # Custom theme with modern colors
    custom_theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="indigo",
        neutral_hue="slate"
    ).set(
        body_background_fill="#87ceeb",
        body_background_fill_dark="#0f172a",
        button_primary_background_fill="#bff47f",
        button_primary_background_fill_hover="#e0bede",
        button_primary_text_color="white",
        block_background_fill="#ffffff",
        block_border_color="#e2e8f0",
        block_border_width="1px",
        input_background_fill="#f8fafc"
    )

    css_styles = """
        .gradio-container {
            background: #87ceeb !important;
            min-height: 100vh;
        }
        body, .main {
            background: #87ceeb !important;
        }
        .gr-button-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        }
        .gr-button-primary:hover {
            background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
        }
        .gr-markdown h1 {
            color: #1e293b !important;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        .gr-tab {
            background: rgba(255,255,255,0.9) !important;
            backdrop-filter: blur(10px) !important;
        }
        /* Highlight selected dataframe row */
        .svelte-df tr.selected td {
            background: #ede9fe !important;
            border-left: 3px solid #7c3aed !important;
        }
        /* Compact file upload boxes */
        .compact-upload .wrap {
            min-height: 80px !important;
            padding: 8px !important;
        }
        .compact-upload .upload-container {
            min-height: 80px !important;
        }
        .compact-upload svg {
            width: 24px !important;
            height: 24px !important;
        }
        .compact-upload .text-center {
            font-size: 0.78rem !important;
        }
    """

    with gr.Blocks() as demo:
        gr.Markdown("#  ShopWave: Autonomous Support Dashboard")
        gr.Markdown("### Multi-Agent Orchestration via AutoGen & Groq")

        with gr.Tab("1. Data Setup"):
            with gr.Row():
                t_file = gr.File(label="📋 tickets.json", file_types=[".json"], elem_classes=["compact-upload"])
                c_file = gr.File(label="👤 customers.json", file_types=[".json"], elem_classes=["compact-upload"])
                o_file = gr.File(label="📦 orders.json", file_types=[".json"], elem_classes=["compact-upload"])
                p_file = gr.File(label="🛍️ products.json", file_types=[".json"], elem_classes=["compact-upload"])

            load_btn = gr.Button("Initialize Database", variant="primary", size="lg")
            status_msg = gr.Textbox(label="System Status", interactive=False)

            with gr.Accordion("View Policy Knowledge Base", open=False):
                policy_text = gr.TextArea(
                    value=open("data/knowledge_base/policies.txt").read() if os.path.exists("data/knowledge_base/policies.txt") else "",
                    interactive=False,
                    lines=10
                )

        with gr.Tab("2. Agent Analysis"):
            with gr.Row():
                num_tickets_input = gr.Number(
                    label="Number of Tickets to Process",
                    value=5,
                    minimum=1,
                    maximum=50,
                    step=1,
                    info="Select how many tickets to analyze (1-50)"
                )
                run_btn = gr.Button("🤖 Run Multi-Agent Ticket Analysis", variant="primary", size="lg")

            # Loading animation label
            loading_indicator = gr.Markdown("", visible=True)

            # ── KPI Cards ──────────────────────────────────────────────────────
            kpi_display = gr.HTML(value="<div style='color:#94a3b8;padding:8px;'>Run analysis to see KPI cards.</div>")

            # ── Inner Tabs: Results / Trace / Analytics ────────────────────────
            with gr.Tabs():
                with gr.Tab("📊 Results"):
                    # Filter dropdown
                    filter_dropdown = gr.Dropdown(
                        choices=["All", "Resolved", "Approved", "Escalated", "Error"],
                        value="All",
                        label="🔍 Filter by Status",
                        interactive=True
                    )
                    results_table = gr.Dataframe(
                        headers=["Index", "Ticket ID", "Status", "Confidence", "Source", "Reasoning"],
                        datatype=["number", "str", "str", "str", "str", "str"],
                        interactive=False,
                        wrap=True
                    )
                    # Hidden state to keep full unfiltered df
                    full_df_state = gr.State(pd.DataFrame())

                    summary_view = gr.Markdown("Click run to start analysis.")
                    status_view = gr.Textbox(label="Analysis Status", interactive=False)

                with gr.Tab("📜 Trace"):
                    gr.Markdown("### 🔍 Deep Dive: Resolution Trace\nClick any row in the Results tab to load the audit trace below.")
                    trace_view = gr.Code(label="Audit Log & Agent Conversation Trace", language="json", lines=20)

                with gr.Tab("📈 Analytics"):
                    chart_display = gr.HTML(value="<div style='color:#94a3b8;padding:8px;'>Run analysis to see distribution chart.</div>")
                    intelligence_display = gr.HTML(value="<div style='color:#94a3b8;padding:8px;'>Run analysis to see system intelligence.</div>")

        # ── Loading animation helper ───────────────────────────────────────────
        def show_loading():
            return gr.update(value="### 🤖 Agents Thinking… ⏳ Please wait while the multi-agent pipeline processes your tickets.", visible=True)

        def hide_loading():
            return gr.update(value="", visible=False)

        def run_and_store(num_tickets):
            df, summary, status, kpi, chart, intel = ui_logic.run_analysis(num_tickets)
            return df, summary, status, kpi, chart, intel, df   # last item = full_df_state

        # ── Event Listeners ────────────────────────────────────────────────────
        load_btn.click(ui_logic.load_files, inputs=[t_file, c_file, o_file, p_file], outputs=status_msg)

        run_btn.click(
            fn=show_loading,
            inputs=[],
            outputs=[loading_indicator]
        ).then(
            fn=run_and_store,
            inputs=[num_tickets_input],
            outputs=[results_table, summary_view, status_view, kpi_display, chart_display, intelligence_display, full_df_state]
        ).then(
            fn=hide_loading,
            inputs=[],
            outputs=[loading_indicator]
        )

        results_table.select(ui_logic.get_ticket_details, outputs=trace_view)

        filter_dropdown.change(
            fn=ui_logic.filter_results,
            inputs=[filter_dropdown, full_df_state],
            outputs=[results_table]
        )

    # Try different ports if 7860 is busy
    ports_to_try = [7860, 7861, 7862, 7863, 7864]
    for port in ports_to_try:
        try:
            demo.launch(
                server_name="127.0.0.1",
                server_port=port,
                theme=custom_theme,
                css=css_styles,
                show_error=True
            )
            break
        except OSError as e:
            if "Cannot find empty port" in str(e):
                print(f"Port {port} is busy, trying next port...")
                continue
            else:
                raise e
    else:
        print("Could not find an available port in range 7860-7864")
        print("Please close other Gradio applications or specify a different port")


if __name__ == "__main__":
    launch_ui()
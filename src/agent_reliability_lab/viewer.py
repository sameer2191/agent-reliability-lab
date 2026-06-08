"""Static HTML trace viewer generator."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .tracing import load_trace


def generate_trace_viewer(
    summary: dict[str, Any],
    trace_dir: Path,
    output_path: Path,
) -> Path:
    traces: dict[str, list[dict[str, Any]]] = {}
    for trace_path in sorted(trace_dir.glob("*.jsonl")):
        traces[trace_path.stem] = load_trace(trace_path)

    payload = json.dumps({"summary": summary, "traces": traces}, sort_keys=True)
    metrics = summary["metrics"]
    metric_cards = "\n".join(
        f"<div class='metric'><span>{html.escape(key)}</span><strong>{value}</strong></div>"
        for key, value in metrics.items()
    )
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(result['name'])}</td>"
        f"<td>{html.escape(result['status'])}</td>"
        f"<td>{'pass' if result['passed'] else 'fail'}</td>"
        f"<td>{result['steps']}</td>"
        f"<td>{html.escape(Path(result['trace_path']).name)}</td>"
        "</tr>"
        for result in summary["results"]
    )

    output_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Reliability Lab Trace Viewer</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #f8fafc;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #64748b;
      --line: #d8dee9;
      --accent: #0f766e;
      --risk: #b42318;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0e1117;
        --panel: #151b23;
        --ink: #e6edf3;
        --muted: #9aa4b2;
        --line: #2f3a4a;
        --accent: #2dd4bf;
        --risk: #fb7185;
      }}
    }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      letter-spacing: 0;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
      line-height: 1.1;
    }}
    p {{
      color: var(--muted);
      margin: 0 0 24px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 12px;
      margin-bottom: 28px;
    }}
    .metric, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metric {{
      padding: 14px 16px;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    .metric strong {{
      display: block;
      margin-top: 8px;
      font-size: 24px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 28px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      text-align: left;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    .trace-list {{
      display: grid;
      gap: 14px;
    }}
    .panel {{
      padding: 16px;
    }}
    .event {{
      border-left: 3px solid var(--accent);
      padding: 8px 10px;
      margin: 8px 0;
      background: color-mix(in srgb, var(--panel) 92%, var(--accent));
    }}
    .event.safety_guard, .event.budget_guard {{
      border-left-color: var(--risk);
    }}
    code {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      color: var(--muted);
    }}
  </style>
</head>
<body>
<main>
  <h1>Agent Reliability Lab Trace Viewer</h1>
  <p>Static artifact generated from JSONL traces. No network, API keys, or external assets required.</p>
  <section class="metrics">{metric_cards}</section>
  <h2>Scenario Results</h2>
  <table>
    <thead><tr><th>Scenario</th><th>Status</th><th>Result</th><th>Steps</th><th>Trace</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <h2>Structured Trace Events</h2>
  <section id="trace-list" class="trace-list"></section>
</main>
<script>
const DATA = {payload};
const traceList = document.getElementById('trace-list');
for (const [name, events] of Object.entries(DATA.traces)) {{
  const panel = document.createElement('section');
  panel.className = 'panel';
  const title = document.createElement('h3');
  title.textContent = name;
  panel.appendChild(title);
  for (const event of events) {{
    const row = document.createElement('div');
    row.className = `event ${{event.actor}}`;
    row.innerHTML = `<strong>#${{event.event_id}} ${{event.actor}} / ${{event.event_type}}</strong><br>${{event.message}}<br><code>${{JSON.stringify(event.data, null, 2)}}</code>`;
    panel.appendChild(row);
  }}
  traceList.appendChild(panel);
}}
</script>
</body>
</html>
""",
        encoding="utf-8",
    )
    return output_path

"""
Exporter - Exports session data in multiple formats
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any


class Exporter:

    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.export_dir = session_dir / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self, events: List[Dict[str, Any]],
                   metrics: Dict[str, Any], session_info: Dict[str, Any]):
        self._raw_events_json(events)
        self._raw_events_csv(events)
        self._session_summary_csv(metrics, session_info)
        self._task_summary_csv(metrics.get('task_summaries', []))
        self._ux_metrics_csv(metrics, session_info)
        self._metrics_json(metrics, session_info)

        print(f"✓ raw_events.json  ({len(events)} events)")
        print(f"✓ raw_events.csv")
        print(f"✓ session_summary.csv")
        print(f"✓ task_summary.csv")
        print(f"✓ ux_metrics.csv")
        print(f"✓ metrics.json")

    # ── 1. Raw event log ──────────────────────────────────────────────────────

    def _raw_events_json(self, events):
        with open(self.export_dir / "raw_events.json", 'w') as f:
            json.dump(events, f, indent=2)

    def _raw_events_csv(self, events):
        """Flat CSV matching the spec example table."""
        if not events:
            return
        all_keys = set()
        for e in events:
            all_keys.update(e.keys())
        fields = ['timestamp', 'event'] + sorted(all_keys - {'timestamp', 'event'})
        with open(self.export_dir / "raw_events.csv", 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            w.writeheader()
            w.writerows(events)

    # ── 2. User session summary ───────────────────────────────────────────────

    def _session_summary_csv(self, metrics: Dict[str, Any], session_info: Dict[str, Any]):
        filepath = self.export_dir / "session_summary.csv"
        dur = session_info.get('duration_seconds', 0) or 0
        mins = int(dur // 60)
        secs = int(dur % 60)

        rows = [
            ['Metric', 'Value'],
            [],
            ['── SESSION INFO ──', ''],
            ['Session ID',          session_info.get('session_id', '')],
            ['Participant ID',      session_info.get('participant_id', '')],
            ['Task',                session_info.get('task_name', '')],
            ['Website',             session_info.get('target_url', '')],
            ['Start Time',          str(session_info.get('start_time', ''))],
            ['End Time',            str(session_info.get('end_time', ''))],
            ['Total Duration',      f"{mins}m {secs}s ({dur:.1f}s)"],
            [],
            ['── ACTIVITY ──', ''],
            ['Total Clicks',        metrics.get('click_count', 0)],
            ['Pages Visited',       metrics.get('pages_visited', 0)],
            ['Backtracks',          metrics.get('backtrack_count', 0)],
            ['Errors',              metrics.get('error_count', 0)],
            ['Hesitations',         metrics.get('hesitation_count', 0)],
            ['Total Events',        metrics.get('total_events', 0)],
            [],
            ['── EVENT BREAKDOWN ──', ''],
        ]
        for etype, count in sorted(metrics.get('event_breakdown', {}).items()):
            rows.append([etype, count])

        with open(filepath, 'w', newline='') as f:
            csv.writer(f).writerows(rows)

    # ── 3. Task-wise summary ──────────────────────────────────────────────────

    def _task_summary_csv(self, task_summaries: List[Dict[str, Any]]):
        filepath = self.export_dir / "task_summary.csv"
        with open(filepath, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['Task', 'Time (s)', 'Success', 'Errors', 'Hesitations'])
            for t in task_summaries:
                dur = t.get('duration_seconds')
                w.writerow([
                    t.get('task_name', ''),
                    f"{dur:.2f}" if dur is not None else 'N/A',
                    'Yes' if t.get('success') else 'No',
                    t.get('errors', 0),
                    t.get('hesitations', 0)
                ])

    # ── 4. UX metrics ─────────────────────────────────────────────────────────

    def _ux_metrics_csv(self, metrics: Dict[str, Any], session_info: Dict[str, Any]):
        filepath = self.export_dir / "ux_metrics.csv"
        rows = [
            ['Category', 'Metric', 'Value'],
            [],
            ['Performance', 'Task Completion Time (s)',  f"{metrics.get('task_completion_time', 0):.2f}"],
            ['Performance', 'Success Rate',              f"{metrics.get('success_rate', 0)*100:.0f}%"],
            ['Performance', 'Error Count',               metrics.get('error_count', 0)],
            ['Performance', 'Backtracking Count',        metrics.get('backtrack_count', 0)],
            ['Performance', 'Click Count',               metrics.get('click_count', 0)],
            ['Performance', 'Click Frequency (per min)', f"{metrics.get('click_frequency', 0):.2f}"],
            [],
            ['Behavioral',  'Hesitation Count',          metrics.get('hesitation_count', 0)],
            ['Behavioral',  'Hesitation Total (s)',       f"{metrics.get('hesitation_total_seconds', 0):.2f}"],
            ['Behavioral',  'Hesitation Avg (s)',         f"{metrics.get('hesitation_avg_seconds', 0):.2f}"],
            ['Behavioral',  'Misclick Rate',              f"{metrics.get('misclick_rate', 0):.3f}"],
            ['Behavioral',  'Navigation Depth',           metrics.get('navigation_depth', 0)],
            ['Behavioral',  'Max Scroll Depth (%)',       f"{metrics.get('scroll_depth_max', 0):.1f}"],
            ['Behavioral',  'Rage Click Incidents',       len(metrics.get('rage_clicks', []))],
            ['Behavioral',  'Pages Visited',              metrics.get('pages_visited', 0)],
        ]
        with open(filepath, 'w', newline='') as f:
            csv.writer(f).writerows(rows)

    # ── Full metrics JSON ─────────────────────────────────────────────────────

    def _metrics_json(self, metrics: Dict[str, Any], session_info: Dict[str, Any]):
        with open(self.export_dir / "metrics.json", 'w') as f:
            json.dump({'session_info': session_info, 'metrics': metrics},
                      f, indent=2, default=str)

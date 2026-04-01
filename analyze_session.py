#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from datetime import datetime


def generate_analysis_report(session_dir, metrics, session_info, session_manager):
    """Print the complete UX analysis report."""

    dur = session_manager.duration_seconds
    mins = int(dur // 60)
    secs = int(dur % 60)

    print("\n" + "="*70)
    print("📊  DETAILED UX ANALYSIS REPORT")
    print("="*70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "─"*70)
    print("1.  SESSION OVERVIEW")
    print("─"*70)
    print(f"  Participant ID : {session_info['participant_id']}")
    print(f"  Task           : {session_info['task_name']}")
    print(f"  Session ID     : {session_manager.session_id}")
    print(f"  Start Time     : {session_info.get('start_time', '')}")
    print(f"  End Time       : {session_info.get('end_time', '')}")
    print(f"  Total Duration : {mins}m {secs}s  ({dur:.1f}s)")

    print("\n" + "─"*70)
    print("2.  RAW EVENT LOG  (last 10 events)")
    print("─"*70)
    print(f"  {'Timestamp':<26} {'Event':<14} {'Element / Detail':<30} {'Page'}")
    print(f"  {'─'*26} {'─'*14} {'─'*30} {'─'*20}")
    events = metrics.get('_events', [])   # injected by main if available
    sample = events[-10:] if events else []
    for e in sample:
        ts      = e.get('timestamp', '')[-12:-4] if e.get('timestamp') else ''
        etype   = e.get('event', '')[:14]
        detail  = (e.get('element') or e.get('field_name') or
                   e.get('key_type') or e.get('focus_state') or
                   f"x={e.get('x','')} y={e.get('y','')}")[:30]
        page    = (e.get('url') or e.get('to_url') or '')[-25:]
        print(f"  {ts:<26} {etype:<14} {detail:<30} {page}")
    if not sample:
        print("  (no events — see exports/raw_events.csv for full log)")

    print("\n" + "─"*70)
    print("3.  USER SESSION SUMMARY")
    print("─"*70)
    rows = [
        ("Total Time",       f"{mins}m {secs}s"),
        ("Total Clicks",     metrics.get('click_count', 0)),
        ("Pages Visited",    metrics.get('pages_visited', 0)),
        ("Backtracks",       metrics.get('backtrack_count', 0)),
        ("Errors",           metrics.get('error_count', 0)),
        ("Hesitations",      metrics.get('hesitation_count', 0)),
        ("Rage Clicks",      len(metrics.get('rage_clicks', []))),
        ("Total Events",     metrics.get('total_events', 0)),
    ]
    for label, val in rows:
        print(f"  {label:<22} {val}")

    print("\n" + "─"*70)
    print("4.  TASK-WISE SUMMARY")
    print("─"*70)
    print(f"  {'Step':<35} {'Time (s)':<12} {'Success':<10} {'Errors':<8} {'Hesitations'}")
    print(f"  {'─'*35} {'─'*12} {'─'*10} {'─'*8} {'─'*11}")
    for t in metrics.get('task_summaries', []):
        dur_s = f"{t['duration_seconds']:.1f}" if t.get('duration_seconds') is not None else 'N/A'
        print(f"  {t['task_name']:<35} {dur_s:<12} "
              f"{'Yes' if t['success'] else 'No':<10} "
              f"{t['errors']:<8} {t['hesitations']}")

    print("\n" + "─"*70)
    print("5.  UX METRICS")
    print("─"*70)
    print("  📊 Performance Metrics")
    perf = [
        ("Task Completion Time",  f"{metrics.get('task_completion_time', 0):.1f}s"),
        ("Success Rate",          f"{metrics.get('success_rate', 0)*100:.0f}%"),
        ("Error Count",           metrics.get('error_count', 0)),
        ("Backtracking Count",    metrics.get('backtrack_count', 0)),
        ("Click Count",           metrics.get('click_count', 0)),
        ("Click Frequency",       f"{metrics.get('click_frequency', 0):.1f}/min"),
    ]
    for label, val in perf:
        print(f"    {label:<28} {val}")

    print("\n  📊 Behavioral Metrics")
    beh = [
        ("Hesitation Count",      metrics.get('hesitation_count', 0)),
        ("Hesitation Total",      f"{metrics.get('hesitation_total_seconds', 0):.1f}s"),
        ("Hesitation Avg",        f"{metrics.get('hesitation_avg_seconds', 0):.1f}s"),
        ("Misclick Rate",         f"{metrics.get('misclick_rate', 0)*100:.1f}%"),
        ("Navigation Depth",      metrics.get('navigation_depth', 0)),
        ("Max Scroll Depth",      f"{metrics.get('scroll_depth_max', 0):.0f}%"),
        ("Repeated Actions",      len(metrics.get('repeated_actions', {}))),
    ]
    for label, val in beh:
        print(f"    {label:<28} {val}")

    idle = metrics.get('idle_periods', [])
    if idle:
        print("\n" + "─"*70)
        print("6.  HESITATION DETAIL  (idle > 3s)")
        print("─"*70)
        print(f"  {'Start':<26} {'Duration (s)':<14} {'Page'}")
        print(f"  {'─'*26} {'─'*14} {'─'*30}")
        for p in sorted(idle, key=lambda x: x['duration_seconds'], reverse=True)[:10]:
            print(f"  {p['start'][-19:]:<26} {p['duration_seconds']:<14.1f} {p['page'][-35:]}")

    rage = metrics.get('rage_clicks', [])
    if rage:
        print("\n" + "─"*70)
        print("7.  RAGE CLICKS  (3+ clicks within 1s at same location)")
        print("─"*70)
        for r in rage:
            print(f"  {r['timestamp'][-19:]}  selector={r['selector']}  at {r['location']}")

    tc = metrics.get('task_completion', {})
    if tc:
        print("\n" + "─"*70)
        print("8.  TASK COMPLETION")
        print("─"*70)
        print(f"  Status     : {tc.get('status', 'Unknown')}")
        print(f"  Completion : {tc.get('percentage', 0)}%")
        for step in tc.get('steps_completed', []):
            print(f"    {step}")

    score = _usability_score(metrics)
    print("\n" + "─"*70)
    print("9.  USABILITY SCORE")
    print("─"*70)
    print(f"  Score: {score}/100")
    if score >= 80:
        print("  Rating: ✅ Excellent — smooth user experience")
    elif score >= 60:
        print("  Rating: ⚠️  Good — minor issues detected")
    elif score >= 40:
        print("  Rating: ⚠️  Fair — several usability concerns")
    else:
        print("  Rating: ❌ Poor — significant usability problems")

    print("\n" + "="*70)
    print("END OF REPORT")
    print("="*70 + "\n")


def _usability_score(metrics: dict) -> int:
    score = 100
    if metrics.get('scroll_depth_max', 0) < 50:
        score -= 15
    if metrics.get('hesitation_count', 0) > 3:
        score -= 10
    if len(metrics.get('rage_clicks', [])) > 0:
        score -= 20
    if len(metrics.get('navigation_loops', [])) > 2:
        score -= 15
    if metrics.get('click_frequency', 0) > 20:
        score -= 10
    if metrics.get('error_count', 0) > 2:
        score -= 10
    return max(0, score)

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_session.py <session_directory>")
        sys.exit(1)

    data = json.loads((Path(sys.argv[1]) / "exports" / "metrics.json").read_text())

    class _SM:
        def __init__(self, d):
            self.session_id       = d['session_info']['session_id']
            self.duration_seconds = d['session_info'].get('duration_seconds', 0)

    generate_analysis_report(Path(sys.argv[1]), data['metrics'],
                              data['session_info'], _SM(data))


if __name__ == "__main__":
    main()

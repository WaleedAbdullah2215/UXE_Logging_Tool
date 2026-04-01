#!/usr/bin/env python3
"""
UX Interaction Logging Tool — CheapOair Study
Run: python main.py

Flow:
  1. Auto-assign next USER ID
  2. Run all 4 tasks sequentially (one browser session per task)
  3. Save each task's data under sessions/USERxxx/Tx_<name>/
  4. Print full analysis after every task
  5. Print combined summary at the end
"""

import asyncio
from pathlib import Path
from datetime import datetime

from session_manager import SessionManager
from browser_controller import BrowserController
from event_logger import EventLogger
from screenshot_manager import ScreenshotManager
from metrics_engine import MetricsEngine
from exporter import Exporter
from analyze_session import generate_analysis_report



TARGET_URL = "https://www.cheapoair.com"

TASKS = [
    ("T1", "Book cheapest round-trip ISB→DXB (21 Apr - 29 Apr, cabin baggage only)"),
    ("T2", "Compare two one-way flights ISB→DXB (15 May, with baggage & seat selection)"),
    ("T3", "Book round-trip ISB→DXB (21 Apr - 25 Apr, cabin only, NO add-ons)"),
    ("T4", "Search round-trip ISB→DXB (21 Apr - 25 Apr), then modify dates to find cheaper option"),
]



TASK_INSTRUCTIONS = {
    "T1": """
  TASK 1 — Book Cheapest Round-Trip Flight
  ─────────────────────────────────────────
  Route   : Islamabad (ISB) → Dubai (DXB), Round-Trip
  Depart  : 21st April
  Return  : 29th April
  Baggage : Cabin baggage only (no checked baggage)
  Goal    : Find the CHEAPEST available option and proceed all the
            way to the payment page (where card details are entered).

  NOTE: We will cross-check the price you find against other travel
  sites to evaluate whether CheapOair is offering a competitive fare.
  Task is considered COMPLETE when you reach the payment/card page.
""",
    "T2": """
  TASK 2 — Compare Two Flight Options
  ─────────────────────────────────────────
  Route   : Islamabad (ISB) → Dubai (DXB), One-Way
  Date    : 15th May
  Extras  : You ARE allowed to add baggage and select a seat
  Goal    : Identify which of two flight options has the LOWER total
            cost after including baggage fees and seat selection.
            Explore at least two flights, view their full cost
            breakdown, and proceed to the payment page for the
            cheaper one.
  Task is considered COMPLETE when you reach the payment/card page.
""",
    "T3": """
  TASK 3 — Book Round-Trip, NO Add-ons
  ─────────────────────────────────────────
  Route   : Islamabad (ISB) → Dubai (DXB), Round-Trip
  Depart  : 21st April
  Return  : 25th April
  Baggage : Cabin baggage only
  Goal    : Complete the booking process reaching the payment page
            WITHOUT selecting any optional add-ons (no seat
            selection, no travel protection, no checked baggage,
            no extras of any kind).
  Task is considered COMPLETE when you reach the payment/card page.
""",
    "T4": """
  TASK 4 — Modify Dates to Find Cheaper Option
  ─────────────────────────────────────────
  Route         : Islamabad (ISB) → Dubai (DXB), Round-Trip
  Initial dates : Depart 21st April, Return 25th April
  Baggage       : Cabin baggage only
  Goal          : After viewing the initial results, MODIFY your
                  travel dates (without restarting the search from
                  scratch) to find a cheaper alternative. Explore
                  different date combinations and proceed to the
                  payment page for the cheapest option you find.
  Task is considered COMPLETE when you reach the payment/card page.
""",
}


def get_next_user_id() -> str:
    sessions_dir = Path("sessions")
    sessions_dir.mkdir(exist_ok=True)
    nums = []
    for d in sessions_dir.iterdir():
        if d.is_dir() and d.name.startswith("USER"):
            try:
                nums.append(int(d.name[4:]))
            except ValueError:
                pass
    return f"USER{(max(nums) + 1 if nums else 1):03d}"


def calculate_task_completion(events: list, task_id: str) -> dict:

    def clicked(keywords):
        return any(
            e.get('event') == 'click' and
            any(k in (e.get('element') or '').lower() for k in keywords)
            for e in events
        )

    def navigated_to(keywords):
        return any(
            e.get('event') == 'navigation' and
            any(k in (e.get('to_url') or '').lower() for k in keywords)
            for e in events
        )

    def field_filled(keywords):
        return any(
            e.get('event') in ('input_end', 'click') and
            any(k in (e.get('field_name') or e.get('element') or '').lower()
                for k in keywords)
            for e in events
        )

    # ── Universal: reached payment page? ─────────────────────────────────────
    PAYMENT_KEYWORDS = ['payment', 'checkout', 'billing', 'card', 'credit',
                        'pay', 'purchase', 'confirm', 'review-order',
                        'review_order', 'revieworder']

    reached_payment = (
        navigated_to(PAYMENT_KEYWORDS) or
        clicked(['enter card', 'pay now', 'complete booking',
                 'confirm booking', 'place order', 'proceed to payment'])
    )

    if task_id == "T1":
        steps_raw = [
            ("Enter origin (Islamabad)",       field_filled(['islamabad', 'isb', 'origin', 'from'])),
            ("Enter destination (Dubai)",      field_filled(['dubai', 'dxb', 'dest', 'to'])),
            ("Select round-trip",              clicked(['round', 'round-trip', 'roundtrip'])),
            ("Set dates (21 Apr – 29 Apr)",    clicked(['april', '21', '29', 'date', 'depart', 'return'])),
            ("Click Search",                   clicked(['search', 'find flight', 'search flights'])),
            ("View results",                   navigated_to(['result', 'flight', 'search'])),
            ("Select cheapest flight",         clicked(['select', 'book', 'choose', 'view deal', 'continue'])),
            ("Reached payment page ✅",        reached_payment),
        ]
        weights = [5, 5, 10, 10, 15, 15, 20, 20]

    elif task_id == "T2":
        steps_raw = [
            ("Enter origin (Islamabad)",       field_filled(['islamabad', 'isb', 'origin', 'from'])),
            ("Enter destination (Dubai)",      field_filled(['dubai', 'dxb', 'dest', 'to'])),
            ("Set date (15 May)",              clicked(['may', '15', 'date', 'depart'])),
            ("Click Search",                   clicked(['search', 'find flight', 'search flights'])),
            ("View results",                   navigated_to(['result', 'flight', 'search'])),
            ("Explore 2+ flight options",      len([e for e in events if e.get('event') == 'click' and
                                                    any(k in (e.get('element') or '').lower()
                                                        for k in ['select', 'view', 'detail', 'choose'])]) >= 2),
            ("Add baggage / seat",             clicked(['baggage', 'bag', 'seat', 'luggage'])),
            ("Reached payment page ✅",        reached_payment),
        ]
        weights = [5, 5, 10, 15, 15, 15, 15, 20]

    elif task_id == "T3":
        addon_clicks = [e for e in events if e.get('event') == 'click' and
                        any(k in (e.get('element') or '').lower()
                            for k in ['insurance', 'protection', 'seat', 'checked bag',
                                      'add bag', 'upgrade', 'add-on', 'addon'])]
        no_addons = len(addon_clicks) == 0
        steps_raw = [
            ("Enter origin (Islamabad)",       field_filled(['islamabad', 'isb', 'origin', 'from'])),
            ("Enter destination (Dubai)",      field_filled(['dubai', 'dxb', 'dest', 'to'])),
            ("Select round-trip",              clicked(['round', 'round-trip', 'roundtrip'])),
            ("Set dates (21 Apr – 25 Apr)",    clicked(['april', '21', '25', 'date', 'depart', 'return'])),
            ("Click Search",                   clicked(['search', 'find flight', 'search flights'])),
            ("Select flight",                  clicked(['select', 'book', 'choose', 'continue'])),
            ("Skipped all add-ons",            no_addons),
            ("Reached payment page ✅",        reached_payment),
        ]
        weights = [5, 5, 10, 10, 15, 15, 20, 20]

    elif task_id == "T4":
        steps_raw = [
            ("Enter origin (Islamabad)",       field_filled(['islamabad', 'isb', 'origin', 'from'])),
            ("Enter destination (Dubai)",      field_filled(['dubai', 'dxb', 'dest', 'to'])),
            ("Set initial dates (21–25 Apr)",  clicked(['april', '21', '25', 'date', 'depart', 'return'])),
            ("Click Search",                   clicked(['search', 'find flight', 'search flights'])),
            ("View initial results",           navigated_to(['result', 'flight', 'search'])),
            ("Modify dates (no full restart)", clicked(['date', 'calendar', 'modify', 'change',
                                                        'edit', 'depart', 'return'])),
            ("Re-search with new dates",       clicked(['search', 'find flight', 'search flights'])),
            ("Reached payment page ✅",        reached_payment),
        ]
        weights = [5, 5, 10, 15, 15, 15, 15, 20]

    else:
        steps_raw, weights = [], []

    percentage = 0
    step_labels = []
    for (label, done), weight in zip(steps_raw, weights):
        if done:
            percentage += weight
            step_labels.append(f"✓ {label}")
        else:
            step_labels.append(f"✗ {label}")

    if percentage == 0:
        status = "Not Started"
    elif reached_payment:
        status = "Fully Completed"
        percentage = 100
    elif percentage < 50:
        status = "Partially Completed (early stage)"
    else:
        status = "Partially Completed (late stage)"

    return {"percentage": percentage, "steps_completed": step_labels,
            "status": status, "reached_payment": reached_payment}


def write_summary_txt(session_dir: Path, events: list, metrics: dict,
                      session_info: dict, session_manager, task_completion: dict):
    """Write plain-English SUMMARY.txt for a single task."""
    summary_dir = session_dir / "summary"
    summary_dir.mkdir(exist_ok=True)
    dur = session_manager.duration_seconds
    score = _score(metrics)

    with open(summary_dir / "SUMMARY.txt", 'w') as f:
        f.write("="*70 + "\n")
        f.write("UX STUDY — TASK SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write(f"Participant : {session_info['participant_id']}\n")
        f.write(f"Task ID     : {session_info['task_id']}\n")
        f.write(f"Task        : {session_info['task_name']}\n")
        f.write(f"Date        : {datetime.now().strftime('%B %d, %Y  %I:%M %p')}\n\n")

        f.write("TASK COMPLETION\n" + "-"*70 + "\n")
        f.write(f"Status     : {task_completion['status']}\n")
        f.write(f"Completion : {task_completion['percentage']}%\n")
        for s in task_completion['steps_completed']:
            f.write(f"  {s}\n")
        f.write("\n")

        f.write("TIMING\n" + "-"*70 + "\n")
        f.write(f"Duration : {int(dur//60)}m {int(dur%60)}s\n\n")

        f.write("ACTIVITY\n" + "-"*70 + "\n")
        bd = metrics.get('event_breakdown', {})
        f.write(f"Total events : {metrics.get('total_events', 0)}\n")
        f.write(f"Clicks       : {bd.get('click', 0)}\n")
        f.write(f"Scrolls      : {bd.get('scroll', 0)}  (max depth {metrics.get('scroll_depth_max', 0):.0f}%)\n")
        f.write(f"Keystrokes   : {bd.get('keypress', 0)}\n\n")

        f.write("ISSUES\n" + "-"*70 + "\n")
        issues = False
        if metrics.get('hesitation_count', 0):
            f.write(f"⚠️  Hesitations : {metrics['hesitation_count']} (paused >3s)\n"); issues = True
        if metrics.get('rage_clicks'):
            f.write(f"⚠️  Rage clicks : {len(metrics['rage_clicks'])}\n"); issues = True
        if metrics.get('navigation_loops'):
            f.write(f"⚠️  Nav loops   : {len(metrics['navigation_loops'])}\n"); issues = True
        if not issues:
            f.write("✅ No major issues\n")
        f.write("\n")

        f.write(f"USABILITY SCORE : {score}/100\n")
        f.write(["⭐⭐ NEEDS IMPROVEMENT", "⭐⭐⭐ FAIR",
                 "⭐⭐⭐⭐ GOOD", "⭐⭐⭐⭐⭐ EXCELLENT"][
                     min(3, score // 25)] + "\n\n")
        f.write("="*70 + "\nEND\n" + "="*70 + "\n")


def _score(metrics: dict) -> int:
    s = 100
    if metrics.get('scroll_depth_max', 0) < 50:   s -= 15
    if metrics.get('hesitation_count', 0) > 3:    s -= 10
    if metrics.get('rage_clicks'):                 s -= 20
    if len(metrics.get('navigation_loops', [])) > 2: s -= 15
    if metrics.get('error_count', 0) > 2:          s -= 10
    return max(0, s)



async def run_task(participant_id: str, task_id: str, task_name: str) -> dict:
    """Run one task, return a result dict for the combined summary."""

    session_info = {
        'participant_id': participant_id,
        'task_id':        task_id,
        'task_name':      task_name,
        'target_url':     TARGET_URL,
    }

    session_manager    = SessionManager(participant_id, task_name, task_id)
    event_logger       = EventLogger(session_manager.session_dir)
    screenshot_manager = ScreenshotManager(session_manager.session_dir)
    browser_controller = BrowserController(event_logger, screenshot_manager,
                                           session_manager.session_id)

    print(f"\n{'='*70}")
    print(f"▶  {task_id}: {task_name}")
    print(f"{'='*70}")
    print(TASK_INSTRUCTIONS[task_id])
    print(f"   Session : {session_manager.session_id}")
    print(f"   Output  : {session_manager.session_dir}")
    input(f"\n   Press ENTER to open the browser and start recording…\n")

    try:
        await browser_controller.start(TARGET_URL)
        await browser_controller.wait_for_close()
    except KeyboardInterrupt:
        print("\n⏹  Recording stopped by researcher.")
    finally:
        await browser_controller.stop()
        session_manager.end_session()

    print(f"\n📊 Processing {task_id}…")
    metrics = MetricsEngine(event_logger.events).compute_metrics()
    metrics['_events'] = event_logger.events

    task_completion = calculate_task_completion(event_logger.events, task_id)
    metrics['task_completion'] = task_completion

    full_session_info = {
        **session_info,
        'session_id':       session_manager.session_id,
        'start_time':       session_manager.start_time,
        'end_time':         session_manager.end_time,
        'duration_seconds': session_manager.duration_seconds,
    }

    Exporter(session_manager.session_dir).export_all(
        events=event_logger.events,
        metrics=metrics,
        session_info=full_session_info
    )

    write_summary_txt(session_manager.session_dir, event_logger.events,
                      metrics, full_session_info, session_manager, task_completion)

    generate_analysis_report(session_manager.session_dir, metrics,
                             full_session_info, session_manager)

    return {
        'task_id':    task_id,
        'task_name':  task_name,
        'duration':   session_manager.duration_seconds,
        'events':     len(event_logger.events),
        'completion': task_completion,
        'score':      _score(metrics),
        'session_dir': session_manager.session_dir,
    }



async def main():
    participant_id = get_next_user_id()

    print("\n" + "="*70)
    print("🚀  UX INTERACTION LOGGING TOOL — CHEAPOAIR STUDY")
    print("="*70)
    print(f"\n  Participant : {participant_id}")
    print(f"  Website     : {TARGET_URL}")
    print(f"  Tasks       : {len(TASKS)} tasks to complete")
    print("\n  ⚠️  Privacy: keyboard text is NOT stored. All data is local.")
    print("\n  Tasks in this session:")
    for tid, tname in TASKS:
        print(f"    {tid}: {tname}")
    print("\n" + "="*70)
    input("\n  Press ENTER to begin the first task…\n")

    results = []
    for i, (task_id, task_name) in enumerate(TASKS, 1):
        print(f"\n  ── Task {i} of {len(TASKS)} ──")
        result = await run_task(participant_id, task_id, task_name)
        results.append(result)

        if i < len(TASKS):
            print(f"\n✅  {task_id} complete.")
            input(f"  Press ENTER when ready to start {TASKS[i][0]}: {TASKS[i][1]}\n")

    print("\n" + "="*70)
    print(f"🏁  ALL TASKS COMPLETE — {participant_id}")
    print("="*70)
    print(f"\n  {'Task':<6} {'Name':<48} {'Time':>8}  {'Done':>6}  {'Score':>6}")
    print(f"  {'─'*6} {'─'*48} {'─'*8}  {'─'*6}  {'─'*6}")
    for r in results:
        mins = int(r['duration'] // 60)
        secs = int(r['duration'] % 60)
        pct  = r['completion']['percentage']
        paid = "✅" if r['completion'].get('reached_payment') else "❌"
        print(f"  {r['task_id']:<6} {r['task_name'][:48]:<48} "
              f"{mins}m{secs:02d}s  {paid} {pct:>3}%  {r['score']:>5}/100")

    combined_dir = Path("sessions") / participant_id
    with open(combined_dir / "COMBINED_SUMMARY.txt", 'w') as f:
        f.write("="*70 + "\n")
        f.write(f"COMBINED STUDY SUMMARY — {participant_id}\n")
        f.write(f"Date: {datetime.now().strftime('%B %d, %Y  %I:%M %p')}\n")
        f.write("="*70 + "\n\n")
        f.write(f"{'Task':<6} {'Name':<48} {'Time':>8}  {'Payment':>8}  {'Done':>6}  {'Score':>6}\n")
        f.write(f"{'─'*6} {'─'*48} {'─'*8}  {'─'*8}  {'─'*6}  {'─'*6}\n")
        for r in results:
            mins = int(r['duration'] // 60)
            secs = int(r['duration'] % 60)
            pct  = r['completion']['percentage']
            paid = "Yes" if r['completion'].get('reached_payment') else "No"
            f.write(f"{r['task_id']:<6} {r['task_name'][:48]:<48} "
                    f"{mins}m{secs:02d}s  {paid:>8}  {pct:>5}%  {r['score']:>5}/100\n")
        f.write("\n" + "="*70 + "\n")

    print(f"\n  📁 All data saved under: sessions/{participant_id}/")
    print(f"  📄 Combined summary   : sessions/{participant_id}/COMBINED_SUMMARY.txt")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Smoke test script that simulates sessions without launching a browser.
Creates two sessions for the same user with two different tasks, writes synthetic events,
runs the MetricsEngine, exports files and generates summaries/reports. This demonstrates
that session folders are created per user and per-task and exports are produced.
"""
from datetime import datetime, timedelta
from pathlib import Path
import json

from session_manager import SessionManager
from event_logger import EventLogger
from metrics_engine import MetricsEngine
from exporter import Exporter
from analyze_session import generate_analysis_report

# Local TASKS map (don't import main to avoid Playwright dependency during smoke test)
TASKS = {
    'T1': "Search & Select Cheapest Flight",
    'T2': "Compare Two Flights (Cost Comparison)",
    'T3': "Booking WITHOUT Add-ons",
    'T4': "Modify Dates"
}


def write_raw_events_file(session_dir, events):
    logs_dir = session_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    filepath = logs_dir / "raw_events.jsonl"
    with open(filepath, 'w') as f:
        for e in events:
            f.write(json.dumps(e) + '\n')


def run_simulated_session(participant_id, task_id, events):
    task_name = TASKS.get(task_id, f"Task {task_id}")
    session_manager = SessionManager(participant_id=participant_id, task_name=task_name, task_id=task_id)

    # Use EventLogger but populate events directly
    event_logger = EventLogger(session_manager.session_dir)
    event_logger.events = events

    # Make sure logs/export dirs exist and write raw events
    write_raw_events_file(session_manager.session_dir, events)

    # Compute metrics
    metrics_engine = MetricsEngine(events)
    metrics = metrics_engine.compute_metrics()

    # Build session_info
    session_info = {
        'participant_id': participant_id,
        'task_id': task_id,
        'task_name': task_name,
        'session_id': session_manager.session_id,
        'start_time': session_manager.start_time,
        'end_time': session_manager.end_time,
        'duration_seconds': session_manager.duration_seconds,
        'target_url': 'https://www.cheapoair.com'
    }

    # Export
    exporter = Exporter(session_manager.session_dir)
    exporter.export_all(events=events, metrics=metrics, session_info=session_info)

    # Create human readable summary
    # Minimal human-readable summary (lightweight for smoke test)
    summary_dir = session_manager.session_dir / 'summary'
    summary_dir.mkdir(exist_ok=True)
    summary_file = summary_dir / 'SUMMARY.txt'
    with open(summary_file, 'w') as f:
        f.write('SMOKE TEST SUMMARY\n')
        f.write(f"Participant: {participant_id}\n")
        f.write(f"Task: {task_name}\n")
        f.write(f"Session ID: {session_manager.session_id}\n")
        f.write(f"Events: {len(events)}\n")
        f.write('\nMetrics:\n')
        for k, v in metrics.items():
            f.write(f"{k}: {v}\n")

    # Generate analysis report (printed to stdout)
    # Use the existing analysis report generator (prints to stdout)
    generate_analysis_report(session_manager.session_dir, metrics, session_info, session_manager)

    # Return path for inspection
    return session_manager.session_dir


if __name__ == '__main__':
    participant = 'USER_SIM'

    # Create synthetic timestamps
    base = datetime.now()

    # Session 1 (T1) events
    events_t1 = [
        {'timestamp': (base).isoformat(), 'event': 'page_load', 'url': 'https://www.cheapoair.com'},
        {'timestamp': (base + timedelta(seconds=3)).isoformat(), 'event': 'click', 'element': 'Origin input', 'selector': '#origin', 'x': 100, 'y': 200},
        {'timestamp': (base + timedelta(seconds=8)).isoformat(), 'event': 'click', 'element': 'Destination input', 'selector': '#destination', 'x': 150, 'y': 220},
        {'timestamp': (base + timedelta(seconds=12)).isoformat(), 'event': 'click', 'element': 'Search', 'selector': '.search-btn', 'x': 300, 'y': 500},
        {'timestamp': (base + timedelta(seconds=13)).isoformat(), 'event': 'navigation', 'from_url': 'https://www.cheapoair.com', 'to_url': 'https://www.cheapoair.com/results'}
    ]

    # Session 2 (T2) events (same participant)
    base2 = base + timedelta(minutes=5)
    events_t2 = [
        {'timestamp': (base2).isoformat(), 'event': 'page_load', 'url': 'https://www.cheapoair.com/results'},
        {'timestamp': (base2 + timedelta(seconds=2)).isoformat(), 'event': 'click', 'element': 'Flight A - $200', 'selector': '.flight-A', 'x': 400, 'y': 600},
        {'timestamp': (base2 + timedelta(seconds=12)).isoformat(), 'event': 'click', 'element': 'Back', 'selector': '.back', 'x': 30, 'y': 40},
        {'timestamp': (base2 + timedelta(seconds=20)).isoformat(), 'event': 'click', 'element': 'Flight B - $180', 'selector': '.flight-B', 'x': 410, 'y': 610},
        {'timestamp': (base2 + timedelta(seconds=22)).isoformat(), 'event': 'navigation', 'from_url': 'https://www.cheapoair.com/results', 'to_url': 'https://www.cheapoair.com/flight/selected'}
    ]

    print('\nRunning simulated session for T1...')
    dir1 = run_simulated_session(participant, 'T1', events_t1)
    print(f'Files for session 1 saved under: {dir1}')

    print('\nRunning simulated session for T2 (same user)...')
    dir2 = run_simulated_session(participant, 'T2', events_t2)
    print(f'Files for session 2 saved under: {dir2}')

    # List created files for the user directory
    user_dir = Path('sessions') / participant
    print('\nContents of user directory:')
    for p in sorted(user_dir.rglob('*')):
        print(p)

    print('\nSmoke test complete.')

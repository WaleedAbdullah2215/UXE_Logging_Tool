#!/usr/bin/env python3
"""
Session Analysis Script
Generates detailed UX analysis report from session data
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def generate_analysis_report(session_dir, metrics, session_info, session_manager):
    """Generate and print analysis report"""
    
    print("\n" + "="*70)
    print("📊 DETAILED UX ANALYSIS REPORT")
    print("="*70)
    
    # Session Overview
    print(f"\n📋 SESSION OVERVIEW")
    print(f"   Participant ID:  {session_info['participant_id']}")
    print(f"   Task:            {session_info['task_name']}")
    print(f"   Session ID:      {session_manager.session_id}")
    print(f"   Duration:        {session_manager.duration_seconds:.1f} seconds")
    
    # Interaction Metrics
    print(f"\n📈 INTERACTION METRICS")
    print(f"   Total Events:        {metrics['total_events']}")
    print(f"   Click Frequency:     {metrics['click_frequency']:.2f} clicks/minute")
    print(f"   Max Scroll Depth:    {metrics['scroll_depth_max']:.1f}%")
    print(f"   Completion Time:     {metrics['task_completion_time']:.1f} seconds")
    
    # Event Breakdown
    print(f"\n📊 EVENT BREAKDOWN")
    breakdown = metrics['event_breakdown']
    sorted_events = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    for event_type, count in sorted_events:
        percentage = (count / metrics['total_events']) * 100
        print(f"   {event_type:15s} {count:4d} ({percentage:5.1f}%)")
    
    # Usability Issues
    print(f"\n⚠️  USABILITY ISSUES")
    issues_found = False
    
    if metrics['hesitation_count'] > 0:
        print(f"   🤔 Hesitations: {metrics['hesitation_count']} (idle >5 sec)")
        issues_found = True
    
    if len(metrics.get('rage_clicks', [])) > 0:
        print(f"   😤 Rage Clicks: {len(metrics['rage_clicks'])} detected")
        issues_found = True
    
    if len(metrics.get('navigation_loops', [])) > 0:
        print(f"   🔄 Navigation Loops: {len(metrics['navigation_loops'])}")
        issues_found = True
    
    if metrics['back_button_usage'] > 0:
        print(f"   ⬅️  Back Button: Used {metrics['back_button_usage']} times")
        issues_found = True
    
    if not issues_found:
        print(f"   ✅ No major usability issues detected!")
    
    # Calculate Score
    score = 100
    if metrics['scroll_depth_max'] < 50:
        score -= 15
    if metrics['hesitation_count'] > 3:
        score -= 10
    if len(metrics.get('rage_clicks', [])) > 0:
        score -= 20
    if len(metrics.get('navigation_loops', [])) > 2:
        score -= 15
    if metrics['click_frequency'] > 20:
        score -= 10
    score = max(0, score)
    
    print(f"\n🎯 USABILITY SCORE: {score}/100")
    if score >= 80:
        print(f"   Rating: ✅ Excellent - Smooth user experience")
    elif score >= 60:
        print(f"   Rating: ⚠️  Good - Minor issues detected")
    elif score >= 40:
        print(f"   Rating: ⚠️  Fair - Several usability concerns")
    else:
        print(f"   Rating: ❌ Poor - Significant usability problems")


def load_session_data(session_path: str):
    """Load session metrics and events"""
    session_dir = Path(session_path)
    
    metrics_file = session_dir / "exports" / "metrics.json"
    if not metrics_file.exists():
        print(f"❌ Metrics file not found: {metrics_file}")
        sys.exit(1)
    
    with open(metrics_file) as f:
        data = json.load(f)
    
    return data


def main():
    """Main analysis function for command-line use"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_session.py <session_directory>")
        print("\nExample:")
        print("  python analyze_session.py sessions/P001/P001_20260302_143022")
        sys.exit(1)
    
    session_path = sys.argv[1]
    
    print("\n" + "="*70)
    print("UX SESSION ANALYSIS REPORT")
    print("="*70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    data = load_session_data(session_path)
    
    # Create mock session manager for compatibility
    class MockSessionManager:
        def __init__(self, data):
            self.session_id = data['session_info']['session_id']
            self.duration_seconds = data['session_info']['duration_seconds']
    
    session_manager = MockSessionManager(data)
    
    # Generate report
    generate_analysis_report(
        Path(session_path),
        data['metrics'],
        data['session_info'],
        session_manager
    )
    
    print("\n" + "="*70)
    print("END OF REPORT")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

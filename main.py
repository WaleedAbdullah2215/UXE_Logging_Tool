#!/usr/bin/env python3
"""
UX Interaction Logging Tool - Simplified Single Command Version
Just run: python main.py
"""

import asyncio
from session_manager import SessionManager
from browser_controller import BrowserController
from event_logger import EventLogger
from screenshot_manager import ScreenshotManager
from metrics_engine import MetricsEngine
from exporter import Exporter
from analyze_session import generate_analysis_report
from datetime import datetime
from pathlib import Path


# Fixed task for CheapOair study
TASK_NAME = "Find the cheapest flight from Islamabad to Dubai"
TARGET_URL = "https://www.cheapoair.com"


def get_next_user_id():
    """Get next sequential user ID (USER001, USER002, etc.)"""
    sessions_dir = Path("sessions")
    sessions_dir.mkdir(exist_ok=True)
    
    # Find existing user directories
    existing_users = []
    for user_dir in sessions_dir.glob("USER*"):
        if user_dir.is_dir():
            try:
                num = int(user_dir.name.replace("USER", ""))
                existing_users.append(num)
            except ValueError:
                continue
    
    next_num = max(existing_users) + 1 if existing_users else 1
    return f"USER{next_num:03d}"


def calculate_task_completion(events):
    """
    Calculate task completion percentage
    Task: Find the cheapest flight from Islamabad to Dubai
    
    Steps:
    1. Enter origin (Islamabad) - 20%
    2. Enter destination (Dubai) - 20%
    3. Click search button - 30%
    4. View search results - 20%
    5. Click on a flight option - 10%
    """
    completion = {
        'percentage': 0,
        'steps_completed': [],
        'status': 'Not Started'
    }
    
    # Check for origin input (Islamabad/ISB)
    origin_entered = any(
        (e.get('event') == 'click' and e.get('element') and 
         ('islamabad' in e.get('element', '').lower() or 'isb' in e.get('element', '').lower())) or
        (e.get('event') == 'keypress' and any(
            'origin' in ev.get('selector', '').lower() or 'from' in ev.get('selector', '').lower()
            for ev in events[:events.index(e)+1] if ev.get('event') == 'click'
        ))
        for e in events
    )
    
    # Check for destination input (Dubai/DXB)
    destination_entered = any(
        (e.get('event') == 'click' and e.get('element') and 
         ('dubai' in e.get('element', '').lower() or 'dxb' in e.get('element', '').lower())) or
        (e.get('event') == 'keypress' and any(
            'dest' in ev.get('selector', '').lower() or 'to' in ev.get('selector', '').lower()
            for ev in events[:events.index(e)+1] if ev.get('event') == 'click'
        ))
        for e in events
    )
    
    # Check for search button click
    search_clicked = any(
        e.get('event') == 'click' and e.get('element') and 
        ('search' in e.get('element', '').lower() or 'find' in e.get('element', '').lower())
        for e in events
    )
    
    # Check for navigation to results page
    results_viewed = any(
        e.get('event') == 'navigation' and 
        ('result' in e.get('to_url', '').lower() or 'flight' in e.get('to_url', '').lower())
        for e in events
    )
    
    # Check for flight selection
    flight_selected = False
    if results_viewed:
        results_index = next((i for i, e in enumerate(events) 
                            if e.get('event') == 'navigation' and 
                            ('result' in e.get('to_url', '').lower() or 'flight' in e.get('to_url', '').lower())), -1)
        if results_index >= 0:
            flight_selected = any(
                e.get('event') == 'click' and e.get('element') and
                ('select' in e.get('element', '').lower() or 'book' in e.get('element', '').lower() or
                 'choose' in e.get('element', '').lower() or 'view' in e.get('element', '').lower())
                for e in events[results_index:]
            )
    
    # Calculate completion
    percentage = 0
    steps = []
    
    if origin_entered:
        percentage += 20
        steps.append("✓ Origin entered (Islamabad)")
    else:
        steps.append("✗ Origin not entered")
    
    if destination_entered:
        percentage += 20
        steps.append("✓ Destination entered (Dubai)")
    else:
        steps.append("✗ Destination not entered")
    
    if search_clicked:
        percentage += 30
        steps.append("✓ Search initiated")
    else:
        steps.append("✗ Search not initiated")
    
    if results_viewed:
        percentage += 20
        steps.append("✓ Results viewed")
    else:
        steps.append("✗ Results not viewed")
    
    if flight_selected:
        percentage += 10
        steps.append("✓ Flight selected")
    else:
        steps.append("✗ Flight not selected")
    
    completion['percentage'] = percentage
    completion['steps_completed'] = steps
    
    if percentage == 0:
        completion['status'] = 'Not Started'
    elif percentage < 100:
        completion['status'] = 'Partially Completed'
    else:
        completion['status'] = 'Fully Completed'
    
    return completion


def create_human_readable_summary(session_dir, events, metrics, session_info, session_manager):
    """Create plain English summary of the session"""
    summary_dir = session_dir / "summary"
    summary_dir.mkdir(exist_ok=True)
    
    summary_file = summary_dir / "SUMMARY.txt"
    
    task_completion = metrics.get('task_completion', {'percentage': 0, 'steps_completed': [], 'status': 'Unknown'})
    
    with open(summary_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("UX STUDY SESSION SUMMARY - PLAIN ENGLISH REPORT\n")
        f.write("="*70 + "\n\n")
        
        # Basic Info
        f.write("WHO & WHAT\n")
        f.write("-" * 70 + "\n")
        f.write(f"Participant: {session_info['participant_id']}\n")
        f.write(f"Task Given: {session_info['task_name']}\n")
        f.write(f"Website: CheapOair.com\n")
        f.write(f"Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        
        # Task Completion
        f.write("TASK COMPLETION\n")
        f.write("-" * 70 + "\n")
        f.write(f"Status: {task_completion['status']}\n")
        f.write(f"Completion: {task_completion['percentage']}%\n\n")
        f.write("Steps:\n")
        for step in task_completion['steps_completed']:
            f.write(f"  {step}\n")
        f.write("\n")
        
        if task_completion['percentage'] == 100:
            f.write("✅ User successfully completed the entire task!\n\n")
        elif task_completion['percentage'] >= 50:
            f.write("⚠️  User completed most of the task but didn't finish.\n\n")
        else:
            f.write("❌ User did not complete the task.\n\n")
        
        # Duration
        duration = session_manager.duration_seconds
        f.write("HOW LONG DID IT TAKE?\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Time: {duration:.0f} seconds ({duration/60:.1f} minutes)\n")
        if duration < 30:
            f.write("Assessment: Very quick!\n")
        elif duration < 60:
            f.write("Assessment: Good pace.\n")
        elif duration < 120:
            f.write("Assessment: Moderate time.\n")
        else:
            f.write("Assessment: Longer session.\n")
        f.write("\n")
        
        # Activity Level
        f.write("WHAT DID THE USER DO?\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Actions: {metrics['total_events']} interactions recorded\n\n")
        
        breakdown = metrics['event_breakdown']
        if 'click' in breakdown:
            f.write(f"Clicks: {breakdown['click']} times\n")
        if 'scroll' in breakdown:
            f.write(f"Scrolling: {breakdown['scroll']} times (max depth: {metrics['scroll_depth_max']:.0f}%)\n")
        if 'keypress' in breakdown:
            f.write(f"Typing: {breakdown['keypress']} keystrokes\n")
        if 'mousemove' in breakdown:
            f.write(f"Mouse Movement: {breakdown['mousemove']} movements\n")
        f.write("\n")
        
        # Problems Detected
        f.write("DID THE USER HAVE ANY PROBLEMS?\n")
        f.write("-" * 70 + "\n")
        
        problems_found = False
        
        if metrics['hesitation_count'] > 0:
            f.write(f"⚠️  HESITATIONS: {metrics['hesitation_count']} times (paused >5 seconds)\n")
            problems_found = True
        
        if len(metrics.get('rage_clicks', [])) > 0:
            f.write(f"⚠️  RAGE CLICKS: {len(metrics['rage_clicks'])} incidents (frustration detected)\n")
            problems_found = True
        
        if len(metrics.get('navigation_loops', [])) > 0:
            f.write(f"⚠️  NAVIGATION LOOPS: {len(metrics['navigation_loops'])} times (user went back)\n")
            problems_found = True
        
        if not problems_found:
            f.write("✅ NO MAJOR PROBLEMS DETECTED!\n")
        f.write("\n")
        
        # Overall Score
        f.write("OVERALL USABILITY SCORE\n")
        f.write("-" * 70 + "\n")
        
        score = 100
        if metrics['scroll_depth_max'] < 50:
            score -= 15
        if metrics['hesitation_count'] > 3:
            score -= 10
        if len(metrics.get('rage_clicks', [])) > 0:
            score -= 20
        if len(metrics.get('navigation_loops', [])) > 2:
            score -= 15
        score = max(0, score)
        
        f.write(f"Score: {score}/100\n\n")
        
        if score >= 80:
            f.write("Rating: ⭐⭐⭐⭐⭐ EXCELLENT\n")
        elif score >= 60:
            f.write("Rating: ⭐⭐⭐⭐ GOOD\n")
        elif score >= 40:
            f.write("Rating: ⭐⭐⭐ FAIR\n")
        else:
            f.write("Rating: ⭐⭐ NEEDS IMPROVEMENT\n")
        
        f.write("\n")
        f.write("="*70 + "\n")
        f.write("END OF SUMMARY\n")
        f.write("="*70 + "\n")
    
    print(f"✓ Human-readable summary created: {summary_file}")


async def main():
    """Main execution flow - fully automated"""
    
    # Auto-assign participant ID
    participant_id = get_next_user_id()
    session_info = {
        'participant_id': participant_id,
        'task_name': TASK_NAME,
        'target_url': TARGET_URL
    }
    
    print("\n" + "="*70)
    print("🚀 UX INTERACTION LOGGING TOOL - CHEAPOAIR STUDY")
    print("="*70)
    print(f"\n📋 Session Details:")
    print(f"   Participant ID: {session_info['participant_id']}")
    print(f"   Task: {session_info['task_name']}")
    print(f"   Website: {session_info['target_url']}")
    print("\n⚠️  Privacy Notice:")
    print("   • Keyboard text content is NOT stored")
    print("   • Only interaction patterns are logged")
    print("="*70 + "\n")
    
    # Initialize components
    session_manager = SessionManager(
        participant_id=session_info['participant_id'],
        task_name=session_info['task_name']
    )
    
    event_logger = EventLogger(session_manager.session_dir)
    screenshot_manager = ScreenshotManager(session_manager.session_dir)
    
    browser_controller = BrowserController(
        event_logger=event_logger,
        screenshot_manager=screenshot_manager,
        session_id=session_manager.session_id
    )
    
    print(f"✓ Session ID: {session_manager.session_id}")
    print(f"✓ Output directory: {session_manager.session_dir}")
    print(f"\n🌐 Launching browser...")
    print("\n" + "="*70)
    print("📹 RECORDING IN PROGRESS")
    print("="*70)
    print(f"Task: {TASK_NAME}")
    print("Close the browser when done.")
    print("="*70 + "\n")
    
    try:
        await browser_controller.start(session_info['target_url'])
        await browser_controller.wait_for_close()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping recording...")
    finally:
        await browser_controller.stop()
        session_manager.end_session()
        
        # Generate analytics
        print("\n📊 Generating analytics...")
        metrics_engine = MetricsEngine(event_logger.events)
        metrics = metrics_engine.compute_metrics()
        
        # Calculate task completion
        task_completion = calculate_task_completion(event_logger.events)
        metrics['task_completion'] = task_completion
        
        # Export data
        print("💾 Exporting data...")
        exporter = Exporter(session_manager.session_dir)
        exporter.export_all(
            events=event_logger.events,
            metrics=metrics,
            session_info={
                **session_info,
                'session_id': session_manager.session_id,
                'start_time': session_manager.start_time,
                'end_time': session_manager.end_time,
                'duration_seconds': session_manager.duration_seconds
            }
        )
        
        # Create human-readable summary
        print("📝 Creating plain English summary...")
        create_human_readable_summary(
            session_manager.session_dir,
            event_logger.events,
            metrics,
            session_info,
            session_manager
        )
        
        print("\n" + "="*70)
        print("✅ SESSION COMPLETE")
        print("="*70)
        print(f"Session ID: {session_manager.session_id}")
        print(f"Duration: {session_manager.duration_seconds:.1f} seconds")
        print(f"Events captured: {len(event_logger.events)}")
        print(f"Task Completion: {task_completion['percentage']}% ({task_completion['status']})")
        print("="*70)
        
        # Auto-run analysis
        print("\n📈 Generating detailed analysis report...\n")
        generate_analysis_report(session_manager.session_dir, metrics, session_info, session_manager)
        
        print("\n" + "="*70)
        print("🎉 ALL DONE!")
        print("="*70)
        print(f"📁 All files saved to: {session_manager.session_dir}")
        print(f"📄 Easy-to-read summary: {session_manager.session_dir}/summary/SUMMARY.txt")
        print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

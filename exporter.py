"""
Exporter - Exports session data in multiple formats
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any


class Exporter:
    """Exports session data to various formats"""
    
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.export_dir = session_dir / "exports"
    
    def export_all(self, events: List[Dict[str, Any]], metrics: Dict[str, Any], session_info: Dict[str, Any]):
        """Export all data formats"""
        self.export_raw_events_json(events)
        self.export_session_summary_csv(metrics, session_info)
        self.export_timeline_csv(events)
        self.export_metrics_json(metrics, session_info)
        
        print(f"✓ Exported raw_events.json ({len(events)} events)")
        print(f"✓ Exported session_summary.csv")
        print(f"✓ Exported timeline.csv")
        print(f"✓ Exported metrics.json")
    
    def export_raw_events_json(self, events: List[Dict[str, Any]]):
        """Export raw events as JSON"""
        filepath = self.export_dir / "raw_events.json"
        with open(filepath, 'w') as f:
            json.dump(events, f, indent=2)
    
    def export_session_summary_csv(self, metrics: Dict[str, Any], session_info: Dict[str, Any]):
        """Export session summary as CSV"""
        filepath = self.export_dir / "session_summary.csv"
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            
            # Session info
            writer.writerow(['Session ID', session_info.get('session_id', '')])
            writer.writerow(['Participant ID', session_info.get('participant_id', '')])
            writer.writerow(['Task Name', session_info.get('task_name', '')])
            writer.writerow(['Target URL', session_info.get('target_url', '')])
            writer.writerow(['Start Time', session_info.get('start_time', '')])
            writer.writerow(['End Time', session_info.get('end_time', '')])
            writer.writerow(['Duration (seconds)', f"{session_info.get('duration_seconds', 0):.2f}"])
            writer.writerow([])
            
            # Metrics
            writer.writerow(['Total Events', metrics.get('total_events', 0)])
            writer.writerow(['Task Completion Time (seconds)', f"{metrics.get('task_completion_time', 0):.2f}"])
            writer.writerow(['Click Frequency (per minute)', f"{metrics.get('click_frequency', 0):.2f}"])
            writer.writerow(['Max Scroll Depth (%)', f"{metrics.get('scroll_depth_max', 0):.1f}"])
            writer.writerow(['Hesitation Count', metrics.get('hesitation_count', 0)])
            writer.writerow(['Rage Click Count', len(metrics.get('rage_clicks', []))])
            writer.writerow(['Navigation Loops', len(metrics.get('navigation_loops', []))])
            writer.writerow(['Back Button Usage', metrics.get('back_button_usage', 0)])
            writer.writerow([])
            
            # Event breakdown
            writer.writerow(['Event Type', 'Count'])
            for event_type, count in metrics.get('event_breakdown', {}).items():
                writer.writerow([event_type, count])
    
    def export_timeline_csv(self, events: List[Dict[str, Any]]):
        """Export event timeline as CSV"""
        filepath = self.export_dir / "timeline.csv"
        
        if not events:
            return
        
        # Get all unique keys
        all_keys = set()
        for event in events:
            all_keys.update(event.keys())
        
        fieldnames = ['timestamp', 'event'] + sorted(list(all_keys - {'timestamp', 'event'}))
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(events)
    
    def export_metrics_json(self, metrics: Dict[str, Any], session_info: Dict[str, Any]):
        """Export metrics with session info as JSON"""
        filepath = self.export_dir / "metrics.json"
        
        output = {
            'session_info': session_info,
            'metrics': metrics
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)

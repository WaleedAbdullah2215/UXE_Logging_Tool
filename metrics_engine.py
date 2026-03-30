"""
Metrics Engine - Computes UX analytics from event logs
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict


class MetricsEngine:
    """Analyzes events and computes UX metrics"""
    
    def __init__(self, events: List[Dict[str, Any]]):
        self.events = events
    
    def compute_metrics(self) -> Dict[str, Any]:
        """Compute all UX metrics"""
        if not self.events:
            return {}
        
        return {
            'total_events': len(self.events),
            'task_completion_time': self._calculate_duration(),
            'click_frequency': self._calculate_click_frequency(),
            'scroll_depth_max': self._calculate_max_scroll_depth(),
            'idle_periods': self._detect_idle_periods(),
            'rage_clicks': self._detect_rage_clicks(),
            'navigation_loops': self._detect_navigation_loops(),
            'back_button_usage': self._count_back_navigation(),
            'hesitation_count': self._count_hesitations(),
            'event_breakdown': self._event_breakdown()
        }
    
    def _calculate_duration(self) -> float:
        """Calculate total session duration in seconds"""
        if len(self.events) < 2:
            return 0.0
        
        start = datetime.fromisoformat(self.events[0]['timestamp'])
        end = datetime.fromisoformat(self.events[-1]['timestamp'])
        return (end - start).total_seconds()
    
    def _calculate_click_frequency(self) -> float:
        """Calculate clicks per minute"""
        duration = self._calculate_duration()
        if duration == 0:
            return 0.0
        
        click_count = sum(1 for e in self.events if e.get('event') == 'click')
        return (click_count / duration) * 60
    
    def _calculate_max_scroll_depth(self) -> float:
        """Find maximum scroll depth percentage"""
        scroll_events = [e for e in self.events if e.get('event') == 'scroll']
        if not scroll_events:
            return 0.0
        
        return max(e.get('scroll_depth_percent', 0) for e in scroll_events)
    
    def _detect_idle_periods(self) -> List[Dict[str, Any]]:
        """Detect periods of inactivity > 5 seconds"""
        idle_periods = []
        
        for i in range(1, len(self.events)):
            prev_time = datetime.fromisoformat(self.events[i-1]['timestamp'])
            curr_time = datetime.fromisoformat(self.events[i]['timestamp'])
            gap = (curr_time - prev_time).total_seconds()
            
            if gap > 5.0:
                idle_periods.append({
                    'start': self.events[i-1]['timestamp'],
                    'end': self.events[i]['timestamp'],
                    'duration_seconds': gap
                })
        
        return idle_periods
    
    def _detect_rage_clicks(self) -> List[Dict[str, Any]]:
        """Detect rage clicks: 3+ clicks within 1 second at same location"""
        rage_clicks = []
        click_events = [e for e in self.events if e.get('event') == 'click']
        
        for i in range(len(click_events) - 2):
            window = click_events[i:i+3]
            
            # Check if within 1 second
            start_time = datetime.fromisoformat(window[0]['timestamp'])
            end_time = datetime.fromisoformat(window[2]['timestamp'])
            
            if (end_time - start_time).total_seconds() <= 1.0:
                # Check if same location (within 20px tolerance)
                coords = [(e.get('x', 0), e.get('y', 0)) for e in window]
                if self._are_coords_similar(coords):
                    rage_clicks.append({
                        'timestamp': window[0]['timestamp'],
                        'location': f"({coords[0][0]}, {coords[0][1]})",
                        'selector': window[0].get('selector', 'unknown')
                    })
        
        return rage_clicks
    
    def _are_coords_similar(self, coords: List[tuple], tolerance: int = 20) -> bool:
        """Check if coordinates are within tolerance"""
        if len(coords) < 2:
            return False
        
        x_vals = [c[0] for c in coords]
        y_vals = [c[1] for c in coords]
        
        return (max(x_vals) - min(x_vals) <= tolerance and 
                max(y_vals) - min(y_vals) <= tolerance)
    
    def _detect_navigation_loops(self) -> List[Dict[str, Any]]:
        """Detect when user navigates back to previously visited pages"""
        nav_events = [e for e in self.events if e.get('event') == 'navigation']
        visited_urls = []
        loops = []
        
        for nav in nav_events:
            to_url = nav.get('to_url', '')
            if to_url in visited_urls:
                loops.append({
                    'timestamp': nav['timestamp'],
                    'url': to_url,
                    'revisit_count': visited_urls.count(to_url) + 1
                })
            visited_urls.append(to_url)
        
        return loops
    
    def _count_back_navigation(self) -> int:
        """Count back button usage (heuristic: navigation to previously visited URL)"""
        return len(self._detect_navigation_loops())
    
    def _count_hesitations(self) -> int:
        """Count hesitation periods (idle > 5 seconds)"""
        return len(self._detect_idle_periods())
    
    def _event_breakdown(self) -> Dict[str, int]:
        """Count events by type"""
        breakdown = defaultdict(int)
        for event in self.events:
            event_type = event.get('event', 'unknown')
            breakdown[event_type] += 1
        return dict(breakdown)

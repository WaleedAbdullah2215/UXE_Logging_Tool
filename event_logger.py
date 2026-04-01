"""
Event Logger - Central logging engine for all interaction events
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json


class EventLogger:

    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.events: List[Dict[str, Any]] = []
        self.log_file = session_dir / "logs" / "raw_events.jsonl"

    def log_event(self, event_data: Dict[str, Any]):
        event = {'timestamp': datetime.now().isoformat(), **event_data}
        self.events.append(event)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')


    def log_click(self, url: str, element_text: str, selector: str,
                  x: int, y: int, session_id: str):
        self.log_event({
            'event': 'click', 'url': url,
            'element': element_text, 'selector': selector,
            'x': x, 'y': y, 'session_id': session_id
        })

    def log_scroll(self, url: str, scroll_y: int, scroll_depth_percent: float,
                   scroll_direction: str, session_id: str):
        self.log_event({
            'event': 'scroll', 'url': url,
            'scroll_y': scroll_y,
            'scroll_depth_percent': scroll_depth_percent,
            'scroll_direction': scroll_direction,
            'session_id': session_id
        })

    def log_keypress(self, url: str, key_type: str, session_id: str):
        self.log_event({
            'event': 'keypress', 'url': url,
            'key_type': key_type, 'session_id': session_id
        })

    def log_input_start(self, url: str, field_name: str, selector: str, session_id: str):
        self.log_event({
            'event': 'input_start', 'url': url,
            'field_name': field_name, 'selector': selector,
            'session_id': session_id
        })

    def log_input_end(self, url: str, field_name: str, selector: str,
                      typing_start: Optional[str], typing_end: Optional[str],
                      session_id: str):
        self.log_event({
            'event': 'input_end', 'url': url,
            'field_name': field_name, 'selector': selector,
            'typing_start': typing_start, 'typing_end': typing_end,
            'session_id': session_id
        })

    def log_navigation(self, from_url: str, to_url: str, session_id: str):
        self.log_event({
            'event': 'navigation',
            'from_url': from_url, 'to_url': to_url,
            'session_id': session_id
        })

    def log_page_load(self, url: str, load_time_ms: float, session_id: str):
        self.log_event({
            'event': 'page_load', 'url': url,
            'load_time_ms': load_time_ms, 'session_id': session_id
        })

    def log_focus_change(self, url: str, focus_state: str, session_id: str):
        self.log_event({
            'event': 'focus_change', 'url': url,
            'focus_state': focus_state, 'session_id': session_id
        })

    def log_mouse_move(self, url: str, x: int, y: int, session_id: str):
        self.log_event({
            'event': 'mousemove', 'url': url,
            'x': x, 'y': y, 'session_id': session_id
        })

    def log_form_error(self, url: str, field_name: str, selector: str,
                       message: str, session_id: str):
        self.log_event({
            'event': 'form_error', 'url': url,
            'field_name': field_name, 'selector': selector,
            'message': message, 'session_id': session_id
        })

    def log_form_submit(self, url: str, selector: str, session_id: str):
        self.log_event({
            'event': 'form_submit', 'url': url,
            'selector': selector, 'session_id': session_id
        })

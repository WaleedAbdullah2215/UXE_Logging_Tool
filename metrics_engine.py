"""
Metrics Engine - Computes all UX analytics from event logs
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict


IDLE_THRESHOLD = 3.0  # seconds — detect inactivity > 3s


class MetricsEngine:

    def __init__(self, events: List[Dict[str, Any]],
                 idle_threshold: float = IDLE_THRESHOLD):
        self.events = events or []
        self.idle_threshold = idle_threshold

    # ── Public entry point ────────────────────────────────────────────────────

    def compute_metrics(self) -> Dict[str, Any]:
        if not self.events:
            return self._empty_metrics()

        idle_periods   = self._detect_idle_periods()
        rage_clicks    = self._detect_rage_clicks()
        nav_loops      = self._detect_navigation_loops()
        repeated       = self._repeated_actions()
        breakdown      = self._event_breakdown()
        duration       = self._duration()
        click_count    = breakdown.get('click', 0)
        error_count    = breakdown.get('form_error', 0)
        pages_visited  = self._pages_visited()
        backtracks     = len(nav_loops)
        hes_total      = sum(p['duration_seconds'] for p in idle_periods)
        hes_avg        = hes_total / len(idle_periods) if idle_periods else 0.0

        return {
            # ── Performance metrics ──────────────────────────────────────────
            'total_events':            len(self.events),
            'task_completion_time':    duration,
            'click_frequency':         self._click_frequency(duration, click_count),
            'scroll_depth_max':        self._max_scroll_depth(),
            'click_count':             click_count,
            'error_count':             error_count,
            'backtrack_count':         backtracks,
            'pages_visited':           pages_visited,
            'success_rate':            self._success_rate(),

            # ── Behavioral metrics ───────────────────────────────────────────
            'hesitation_count':        len(idle_periods),
            'hesitation_total_seconds': round(hes_total, 2),
            'hesitation_avg_seconds':  round(hes_avg, 2),
            'misclick_rate':           self._misclick_rate(),
            'navigation_depth':        self._navigation_depth(),
            'repeated_actions':        repeated,

            # ── Detail lists ─────────────────────────────────────────────────
            'idle_periods':            idle_periods,
            'rage_clicks':             rage_clicks,
            'navigation_loops':        nav_loops,
            'back_button_usage':       backtracks,
            'event_breakdown':         breakdown,

            # ── Task-wise summary ────────────────────────────────────────────
            'task_summaries':          self._task_summaries(),
        }

    # ── Performance helpers ───────────────────────────────────────────────────

    def _duration(self) -> float:
        if len(self.events) < 2:
            return 0.0
        t0 = self._ts(self.events[0].get('timestamp'))
        t1 = self._ts(self.events[-1].get('timestamp'))
        return (t1 - t0).total_seconds() if t0 and t1 else 0.0

    def _click_frequency(self, duration: float, click_count: int) -> float:
        return (click_count / duration * 60) if duration > 0 else 0.0

    def _max_scroll_depth(self) -> float:
        depths = [e.get('scroll_depth_percent', 0)
                  for e in self.events if e.get('event') == 'scroll']
        return max(depths) if depths else 0.0

    def _pages_visited(self) -> int:
        urls = set()
        for e in self.events:
            if e.get('event') in ('page_load', 'navigation'):
                u = e.get('url') or e.get('to_url')
                if u:
                    urls.add(u)
        return len(urls)

    def _success_rate(self) -> float:
        """Heuristic: session is successful if user reached a results/review page."""
        reached_results = any(
            e.get('event') == 'navigation' and
            any(k in (e.get('to_url') or '').lower()
                for k in ('result', 'flight', 'review', 'book', 'checkout'))
            for e in self.events
        )
        return 1.0 if reached_results else 0.0

    # ── Behavioral helpers ────────────────────────────────────────────────────

    def _detect_idle_periods(self) -> List[Dict[str, Any]]:
        idle = []
        for i in range(1, len(self.events)):
            t0 = self._ts(self.events[i-1].get('timestamp'))
            t1 = self._ts(self.events[i].get('timestamp'))
            if not t0 or not t1:
                continue
            gap = (t1 - t0).total_seconds()
            if gap > self.idle_threshold:
                idle.append({
                    'start':            self.events[i-1]['timestamp'],
                    'end':              self.events[i]['timestamp'],
                    'duration_seconds': round(gap, 2),
                    'page':             (self.events[i-1].get('url') or
                                         self.events[i-1].get('to_url') or '')
                })
        return idle

    def _detect_rage_clicks(self) -> List[Dict[str, Any]]:
        clicks = [e for e in self.events if e.get('event') == 'click']
        rage = []
        for i in range(len(clicks) - 2):
            w = clicks[i:i+3]
            t0 = self._ts(w[0]['timestamp'])
            t2 = self._ts(w[2]['timestamp'])
            if t0 and t2 and (t2 - t0).total_seconds() <= 1.0:
                coords = [(e.get('x', 0), e.get('y', 0)) for e in w]
                if self._coords_close(coords):
                    rage.append({
                        'timestamp': w[0]['timestamp'],
                        'location':  f"({coords[0][0]}, {coords[0][1]})",
                        'selector':  w[0].get('selector', 'unknown'),
                        'element':   w[0].get('element', '')
                    })
        return rage

    def _detect_navigation_loops(self) -> List[Dict[str, Any]]:
        navs = [e for e in self.events if e.get('event') == 'navigation']
        visited, loops = [], []
        for nav in navs:
            url = nav.get('to_url', '')
            if url in visited:
                loops.append({
                    'timestamp':    nav['timestamp'],
                    'url':          url,
                    'revisit_count': visited.count(url) + 1
                })
            visited.append(url)
        return loops

    def _misclick_rate(self) -> float:
        """Fraction of clicks that were rapid re-clicks on the same selector."""
        clicks = [e for e in self.events if e.get('event') == 'click']
        if not clicks:
            return 0.0
        misclicks = 0
        by_sel = defaultdict(list)
        for c in clicks:
            by_sel[c.get('selector', 'unknown')].append(self._ts(c.get('timestamp')))
        for times in by_sel.values():
            times = sorted(t for t in times if t)
            for i in range(1, len(times)):
                if (times[i] - times[i-1]).total_seconds() <= 2.0:
                    misclicks += 1
        return round(misclicks / len(clicks), 3)

    def _navigation_depth(self) -> int:
        """Max number of unique pages visited in a single forward sequence."""
        visited, max_depth = [], 0
        for e in self.events:
            if e.get('event') in ('navigation', 'page_load'):
                url = e.get('to_url') or e.get('url')
                if not url:
                    continue
                if url in visited:
                    max_depth = max(max_depth, len(visited))
                    visited = [url]
                else:
                    visited.append(url)
        return max(max_depth, len(visited))

    def _repeated_actions(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for e in self.events:
            if e.get('event') == 'click':
                key = e.get('selector') or e.get('element') or 'unknown'
                counts[key] += 1
        return {k: v for k, v in counts.items() if v > 1}

    def _event_breakdown(self) -> Dict[str, int]:
        bd = defaultdict(int)
        for e in self.events:
            bd[e.get('event', 'unknown')] += 1
        return dict(bd)

    # ── Task-wise summary ─────────────────────────────────────────────────────

    def _task_summaries(self) -> List[Dict[str, Any]]:
        """
        Single task: Find the cheapest flight from Islamabad to Dubai.
        We break it into 5 measurable sub-steps and report each.
        """
        def first_match(fn):
            for e in self.events:
                if fn(e):
                    return self._ts(e.get('timestamp'))
            return None

        def last_match(fn):
            for e in reversed(self.events):
                if fn(e):
                    return self._ts(e.get('timestamp'))
            return None

        def dur(t0, t1):
            if t0 and t1:
                d = (t1 - t0).total_seconds()
                return round(d, 2) if d >= 0 else None
            return None

        errors = sum(1 for e in self.events if e.get('event') == 'form_error')

        # Step 1 – Enter origin
        s1_start = first_match(lambda e: e.get('event') == 'input_start' and
                               any(k in (e.get('field_name') or '').lower()
                                   for k in ('origin', 'from', 'departure', 'source')))
        s1_end   = first_match(lambda e: e.get('event') == 'input_end' and
                               any(k in (e.get('field_name') or '').lower()
                                   for k in ('origin', 'from', 'departure', 'source')))
        # fallback: click on ISB suggestion
        if not s1_end:
            s1_end = first_match(lambda e: e.get('event') == 'click' and
                                 any(k in (e.get('element') or '').lower()
                                     for k in ('islamabad', 'isb')))

        # Step 2 – Enter destination
        s2_start = first_match(lambda e: e.get('event') == 'input_start' and
                               any(k in (e.get('field_name') or '').lower()
                                   for k in ('dest', 'to', 'arrival', 'destination')))
        s2_end   = first_match(lambda e: e.get('event') == 'input_end' and
                               any(k in (e.get('field_name') or '').lower()
                                   for k in ('dest', 'to', 'arrival', 'destination')))
        if not s2_end:
            s2_end = first_match(lambda e: e.get('event') == 'click' and
                                 any(k in (e.get('element') or '').lower()
                                     for k in ('dubai', 'dxb')))

        # Step 3 – Click search
        s3_start = first_match(lambda e: e.get('event') == 'click' and
                               any(k in (e.get('element') or '').lower()
                                   for k in ('search', 'find flight', 'search flight')))
        s3_end   = first_match(lambda e: e.get('event') == 'navigation' and
                               any(k in (e.get('to_url') or '').lower()
                                   for k in ('result', 'flight', 'search')))

        # Step 4 – View results
        s4_start = s3_end
        s4_end   = first_match(lambda e: e.get('event') == 'click' and
                               any(k in (e.get('element') or '').lower()
                                   for k in ('select', 'book', 'choose', 'view deal', 'view')))

        # Step 5 – Select cheapest flight
        s5_start = s4_end
        s5_end   = last_match(lambda e: e.get('event') == 'click' and
                              any(k in (e.get('element') or '').lower()
                                  for k in ('select', 'book', 'continue', 'proceed')))

        steps = [
            ('S1', 'Enter Origin (Islamabad)',    s1_start, s1_end),
            ('S2', 'Enter Destination (Dubai)',   s2_start, s2_end),
            ('S3', 'Click Search',                s3_start, s3_end),
            ('S4', 'View Results',                s4_start, s4_end),
            ('S5', 'Select Cheapest Flight',      s5_start, s5_end),
        ]

        summaries = []
        for sid, sname, t0, t1 in steps:
            summaries.append({
                'task_id':          sid,
                'task_name':        sname,
                'start_time':       t0.isoformat() if t0 else None,
                'end_time':         t1.isoformat() if t1 else None,
                'duration_seconds': dur(t0, t1),
                'success':          bool(t0 and t1),
                'errors':           errors if sid == 'S3' else 0,
                'hesitations':      len([p for p in self._detect_idle_periods()
                                         if t0 and t1 and
                                         self._ts(p['start']) and
                                         t0 <= self._ts(p['start']) <= t1])
            })

        return summaries

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _coords_close(self, coords: List[tuple], tol: int = 20) -> bool:
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        return (max(xs) - min(xs) <= tol) and (max(ys) - min(ys) <= tol)

    def _ts(self, val) -> Optional[datetime]:
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(val, fmt)
            except Exception:
                continue
        return None

    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            'total_events': 0, 'task_completion_time': 0,
            'click_frequency': 0, 'scroll_depth_max': 0,
            'click_count': 0, 'error_count': 0,
            'backtrack_count': 0, 'pages_visited': 0, 'success_rate': 0.0,
            'hesitation_count': 0, 'hesitation_total_seconds': 0.0,
            'hesitation_avg_seconds': 0.0, 'misclick_rate': 0.0,
            'navigation_depth': 0, 'repeated_actions': {},
            'idle_periods': [], 'rage_clicks': [],
            'navigation_loops': [], 'back_button_usage': 0,
            'event_breakdown': {}, 'task_summaries': []
        }

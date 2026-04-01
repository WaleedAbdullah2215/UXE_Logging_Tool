

import os
from datetime import datetime
from pathlib import Path


class SessionManager:
    
    def __init__(self, participant_id: str, task_name: str, task_id: str = None):
        self.participant_id = participant_id
        self.task_name = task_name
        self.task_id = task_id
        self.start_time = datetime.now()
        self.end_time = None
        self.session_id = self._generate_session_id()
        self.session_dir = self._create_session_directory()
    
    def _generate_session_id(self) -> str:
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        if self.task_id:
            return f"{self.participant_id}_{self.task_id}_{timestamp}"
        return f"{self.participant_id}_{timestamp}"
    
    def _create_session_directory(self) -> Path:
        base_dir = Path("sessions") / self.participant_id / self.session_id
        base_dir.mkdir(parents=True, exist_ok=True)
        
        (base_dir / "screenshots").mkdir(exist_ok=True)
        (base_dir / "logs").mkdir(exist_ok=True)
        (base_dir / "exports").mkdir(exist_ok=True)
        
        return base_dir
    
    def end_session(self):
        self.end_time = datetime.now()
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

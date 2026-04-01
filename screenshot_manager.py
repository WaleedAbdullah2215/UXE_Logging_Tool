from playwright.async_api import Page
from pathlib import Path
from datetime import datetime
import asyncio


class ScreenshotManager:
    
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.screenshot_dir = session_dir / "screenshots"
        self.screenshot_count = 0
    
    async def capture(self, page: Page, event_type: str, url: str):
        """Capture screenshot with metadata"""
        try:
            self.screenshot_count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{self.screenshot_count:04d}_{event_type}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            await page.screenshot(path=str(filepath), full_page=False)
            
        except Exception as e:
            print(f"⚠️  Screenshot failed: {e}")

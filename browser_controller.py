"""
Browser Controller - Manages Playwright browser and event injection
"""

from playwright.async_api import async_playwright, Page, Browser
from pathlib import Path
from event_logger import EventLogger
from screenshot_manager import ScreenshotManager
import asyncio
from datetime import datetime


class BrowserController:
    """Controls browser automation and event tracking"""
    
    def __init__(self, event_logger: EventLogger, screenshot_manager: ScreenshotManager, session_id: str):
        self.event_logger = event_logger
        self.screenshot_manager = screenshot_manager
        self.session_id = session_id
        self.playwright = None
        self.browser: Browser = None
        self.page: Page = None
        self.current_url = ""
        self.js_tracker = self._load_js_tracker()
    
    def _load_js_tracker(self) -> str:
        """Load JavaScript tracker code"""
        js_path = Path(__file__).parent / "js_tracker.js"
        return js_path.read_text()
    
    async def start(self, target_url: str):
        """Launch browser and start tracking"""
        self.playwright = await async_playwright().start()
        
        # Launch Chromium in headed mode
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        # Create context and page
        context = await self.browser.new_context(
            viewport=None,  # Use full window
            record_video_dir=None
        )
        
        self.page = await context.new_page()
        
        # Set up event handlers
        await self._setup_event_handlers()
        
        # Navigate to target
        page_load_start = datetime.now()
        await self.page.goto(target_url, wait_until='domcontentloaded')
        page_load_time = (datetime.now() - page_load_start).total_seconds() * 1000
        
        self.current_url = target_url
        
        # Inject tracker
        await self._inject_tracker()
        
        # Log page load
        self.event_logger.log_page_load(target_url, page_load_time, self.session_id)
        
        # Take initial screenshot
        await self.screenshot_manager.capture(self.page, "page_load", target_url)
    
    async def _inject_tracker(self):
        """Inject JavaScript tracker into page"""
        try:
            # Create event bridge
            await self.page.expose_function('__UX_LOG_EVENT__', self._handle_js_event)
        except Exception as e:
            # Function already registered, that's ok
            pass
        
        # Inject tracker script
        await self.page.evaluate(self.js_tracker)
    
    async def _handle_js_event(self, event_data: dict):
        """Handle events from injected JavaScript"""
        event_type = event_data.get('type')
        url = self.page.url
        
        if event_type == 'click':
            self.event_logger.log_click(
                url=url,
                element_text=event_data.get('element', ''),
                selector=event_data.get('selector', ''),
                x=event_data.get('x', 0),
                y=event_data.get('y', 0),
                session_id=self.session_id
            )
            # Screenshot on click
            await self.screenshot_manager.capture(self.page, "click", url)
        
        elif event_type == 'scroll':
            self.event_logger.log_scroll(
                url=url,
                scroll_y=event_data.get('scroll_y', 0),
                scroll_depth_percent=event_data.get('scroll_depth_percent', 0),
                session_id=self.session_id
            )
        
        elif event_type == 'keypress':
            self.event_logger.log_keypress(
                url=url,
                key_type=event_data.get('key_type', 'KeyPressed'),
                session_id=self.session_id
            )
        
        elif event_type == 'mousemove':
            self.event_logger.log_mouse_move(
                url=url,
                x=event_data.get('x', 0),
                y=event_data.get('y', 0),
                session_id=self.session_id
            )
        
        elif event_type == 'focus_change':
            self.event_logger.log_focus_change(
                url=url,
                focus_state=event_data.get('focus_state', 'unknown'),
                session_id=self.session_id
            )
    
    async def _setup_event_handlers(self):
        """Set up Playwright-level event handlers"""
        
        # Handle navigation
        async def on_navigation(frame):
            if frame == self.page.main_frame:
                new_url = self.page.url
                if new_url != self.current_url:
                    self.event_logger.log_navigation(
                        from_url=self.current_url,
                        to_url=new_url,
                        session_id=self.session_id
                    )
                    self.current_url = new_url
                    
                    # Re-inject tracker on new page
                    await self._inject_tracker()
                    
                    # Screenshot on navigation
                    await self.screenshot_manager.capture(self.page, "navigation", new_url)
        
        self.page.on('framenavigated', on_navigation)
    
    async def wait_for_close(self):
        """Wait for browser to close or Ctrl+C"""
        try:
            while not self.page.is_closed():
                await asyncio.sleep(0.5)
        except:
            pass
    
    async def stop(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

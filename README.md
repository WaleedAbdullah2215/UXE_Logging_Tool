Automated UX research tool for CheapOair flight booking studies. Records detailed user interaction data with zero website modification.


```bash
pip install -r requirements.txt
playwright install chromium

python main.py
```

That's it! The browser opens to CheapOair, you perform your task, close the browser, and get automatic analysis.

## What It Does

### Automatically Captures
- Mouse clicks with element details
- Mouse movements
- Scroll behavior and depth
- Keyboard events (NO text content)
- Page navigation
- Screenshots at key moments
- Timestamps for everything

### Automatically Analyzes
- Task completion time
- Click frequency
- Hesitation detection (>5 sec idle)
- Rage click detection
- Navigation patterns
- Usability score (0-100)

### Automatically Generates
- JSON event logs
- CSV timeline
- Session summary
- Detailed analysis report
- Screenshots timeline

## How It Works

1. Run `python main.py`
2. Browser opens to CheapOair
3. Perform your task (search flights, etc.)
4. Close the browser when done
5. Automatic analysis displays
6. All files saved to `sessions/` folder

## Auto-Assigned Tasks

The tool randomly assigns one of these tasks:
- Book a one-way flight from New York to Los Angeles
- Search for round-trip flights from Chicago to Miami
- Find the cheapest flight from San Francisco to Seattle
- Compare flight prices from Boston to Denver

## Output Structure

```
sessions/{participant_id}/{session_id}/
├── screenshots/          # Auto-captured images
├── logs/                # Real-time event log
└── exports/             # Final reports
    ├── raw_events.json
    ├── timeline.csv
    ├── session_summary.csv
    └── metrics.json
```

## Privacy & Ethics

- Keyboard text content is NEVER stored
- Only interaction patterns logged
- All data stored locally
- No cloud upload
- Sensitive fields automatically masked

## Requirements

- Python 3.11+
- macOS (tested)
- Chromium (via Playwright)

## License

MIT License - See LICENSE file


**What dv.sh does on each start:**

1. Kills any process holding port 8000 or 5173 (by port scan, not just stored PIDs)
2. Kills any previously tracked PIDs from `.pids/`
3. Runs `npm install` in stock_ui if `node_modules` is missing
4. Starts FastAPI in the background, then polls `/api/health` up to 15 seconds before proceeding
5. Starts Vite in the background, polls `http://localhost:5173` until ready
6. Prints the URLs, log file locations, and stop/status commands

Logs stream to `logs/api.log` and `logs/ui.log` (both gitignored) so you can `tail -f logs/api.log` in a separate terminal if you want to watch live output.


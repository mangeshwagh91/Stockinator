# Stockinator - Multi-Agent Trading Platform

## Motive
Stockinator is built to democratize institutional-grade algorithmic trading for retail users through an autonomous, transparent, and risk-first multi-agent system.

Core goals:

1. Eliminate emotional trading with rule-based execution.
2. Combine technical, sentiment, and ML intelligence into one decision score.
3. Preserve user control through manual override and kill-switch style operation.
4. Support Indian market constraints such as brokerage and risk caps.
5. Keep capital preservation as the first system priority.

## High-Level Workflow

1. Scraping Agent gathers prices, news, and sentiment.
2. Algo Agent computes indicator/pattern consensus.
3. Prediction Agent computes success score.
4. Orchestrator validates score, costs, cooldown, and limits.
5. Trade Agent prepares executable order plan.
6. Risk Monitor enforces daily and position-level limits.
7. Memory Agent stores decisions and outcomes for learning loops.
8. Frontend shows realtime status, scores, and controls.

## Project Structure

```text
Stockinator/
	backend/
		app/
			agents/
				scraping_agent.py
				algo_agent.py
				prediction_agent.py
				trade_agent.py
				memory_agent.py
			orchestrator/
				runtime.py
			risk/
				monitor.py
			memory/
				store.py
			api/
				v1/
					endpoints/
						control.py
						data.py
						trades.py
						ws.py
						system.py
			services/
			models/
			schemas/
			main.py
		requirements.txt
	frontend/
		src/
			components/
			pages/
				SystemControl.tsx
			features/
				dashboard/
					components/
						AgentCycleCard.tsx
					hooks/
						useSystemWorkflow.ts
					types.ts
			lib/
				backendApi.ts
			App.tsx
```

## Start Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Validation Commands

```powershell
# Frontend build
cd frontend
npm run build

# Backend syntax check
cd ..\backend
python -m compileall app
```

## Notes

1. The previous duplicate multi-agent folder tree has been removed and consolidated into backend + frontend.
2. System workflow endpoints are available under /api/v1/system.
3. The System Control page is available at /system.

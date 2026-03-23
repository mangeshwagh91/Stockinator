import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.orchestrator.runtime import Orchestrator
from app.api.dependencies import get_database

async def test_cycle():
    print("Initializing Orchestrator...")
    orchestrator = Orchestrator()
    db = next(get_database())
    try:
        print("Running full agent cycle for BANKNIFTY...")
        result = await orchestrator.run_cycle("BANKNIFTY", db)
        print(f"\\n--- CYCLE RESULT ---")
        print(f"Symbol: {result.symbol}")
        print(f"Score: {result.score}")
        print(f"Decision: {result.decision}")
        print(f"Reasoning: {result.reasoning}")
        if result.trade_execution:
            print("Trade Execution: SUCCESS")
            print(result.trade_execution)
        else:
            print("Trade Execution: NONE")
            
        print("Memory Processed:", result.memory_processed)
    except Exception as e:
        print(f"Error running cycle: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_cycle())

import asyncio
import logging
from typing import Dict, Any
from app.worker.celery_app import celery_app
from app.tools.implementations import run_tool_by_name

logger = logging.getLogger("celery_tasks")


@celery_app.task(name="execute_tool_task", bind=True)
def execute_tool_task(self, tool_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task wrapper for executing potentially long-running I/O tools.
    Prevents blocking the main FastAPI event loop.
    """
    logger.info(f"Celery executing tool '{tool_name}' with args {kwargs}")
    try:
        result = run_tool_by_name(tool_name, kwargs)
        return {"status": "success", "result": result, "tool_name": tool_name}
    except Exception as exc:
        logger.error(f"Error in Celery tool execution '{tool_name}': {str(exc)}")
        return {
            "status": "error",
            "result": f"Celery Task Execution Error: {str(exc)}",
            "tool_name": tool_name,
        }


async def dispatch_tool_execution(tool_name: str, kwargs: Dict[str, Any], timeout: float = 30.0) -> str:
    """
    Dispatch a tool to Celery asynchronously and wait for its completion
    without blocking the FastAPI event loop.
    Falls back gracefully to direct execution if Celery or Redis is unavailable.
    """
    try:
        # Offload tool task to Celery
        async_result = execute_tool_task.delay(tool_name, kwargs)

        start_time = asyncio.get_event_loop().time()
        while not async_result.ready():
            await asyncio.sleep(0.2)
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(f"Celery task timed out for tool '{tool_name}', falling back to direct execution.")
                return run_tool_by_name(tool_name, kwargs)

        data = async_result.result
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return str(data)

    except Exception as e:
        logger.warning(f"Failed to dispatch to Celery ({str(e)}). Running directly.")
        # Fallback to direct execution
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, run_tool_by_name, tool_name, kwargs)

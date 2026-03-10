import logging
from pythonjsonlogger import jsonlogger
from pathlib import Path

# Absolute path based on this file's location
LOG_PATH = Path(__file__).parent.parent / "logs" / "retrieval_logs.jsonl"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("rag_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # prevent duplicate logs

if not logger.handlers:
    logHandler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

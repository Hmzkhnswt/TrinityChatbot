import logging
import os

logger = logging.getLogger(str(os.environ.get("LOGGER")))
logger.setLevel(logging.DEBUG)

os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/app.log")

console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

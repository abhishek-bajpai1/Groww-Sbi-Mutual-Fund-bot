import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("groww_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("GrowwBot")

def log_query(query, route, answer):
    logger.info(f"Query: {query} | Route: {route} | Answer: {answer[:50]}...")

def log_error(error_msg):
    logger.error(f"Error: {error_msg}")

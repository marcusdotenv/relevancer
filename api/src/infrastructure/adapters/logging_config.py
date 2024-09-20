import logging
import sys

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout), 
        ]
    )
    logging.getLogger("uvicorn.access").disabled = True


import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

# Create a function to configure logging
def configure_logging():
    log_folder = os.path.join(os.path.dirname(__file__), 'log')
    os.makedirs(log_folder, exist_ok=True)
    log_filename = os.path.join(log_folder, 'measurement_data.log')
    
    # Create a TimedRotatingFileHandler
    handler = TimedRotatingFileHandler(log_filename, when="H", interval=1, backupCount=24)  # Rotate every hour, keep 24 backups
    handler.suffix = "%Y-%m-%d_%H-%M-%S.log"  # Add a timestamp to rotated log files
    handler.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}.log$"
    
    # Configure logging format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add the handler to the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)  # Set the logging level to INFO

# Call the function to configure logging
configure_logging()

# Example usage of logging
logging.info("Logging initialized.")

# Now, your logging will rotate every hour, keeping 24 backups.

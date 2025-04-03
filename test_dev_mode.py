"""Test script to verify development mode works correctly."""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set development mode environment variable
os.environ["ALARM_BLOCK_DEV_MODE"] = "true"

# Add project root to path if needed
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import config to verify environment variables are read correctly
try:
    from backend.config import config, IS_RASPBERRY_PI, USE_PI_HARDWARE, DEV_MODE
    logger.info(f"Config loaded successfully")
    logger.info(f"Development mode: {DEV_MODE}")
    logger.info(f"Running on Raspberry Pi: {IS_RASPBERRY_PI}")
    logger.info(f"Using Pi hardware: {USE_PI_HARDWARE}")
except Exception as e:
    logger.error(f"Failed to import config: {e}")
    sys.exit(1)

# Try importing dependencies
try:
    from backend.dependencies import get_settings_manager, get_audio_manager
    logger.info("Dependencies imported successfully")
except Exception as e:
    logger.error(f"Failed to import dependencies: {e}")
    sys.exit(1)

# Try importing mock PiHandler
try:
    from backend.mock_pi_handler import MockPiHandler
    logger.info("MockPiHandler imported successfully")
except Exception as e:
    logger.error(f"Failed to import MockPiHandler: {e}")
    sys.exit(1)

# Try initializing components
try:
    settings_manager = get_settings_manager()
    audio_manager = get_audio_manager()
    logger.info("Components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    sys.exit(1)

logger.info("All tests passed successfully!")

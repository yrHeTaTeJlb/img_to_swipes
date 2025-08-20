import logging
from src.config import current_config

logger = logging.getLogger("img_to_swipes")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler(current_config().artifacts_dir / "img_to_swipes.log"))

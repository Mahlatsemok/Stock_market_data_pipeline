import logging

from stock_pipeline.config import PROJECT_ROOT

LOG_DIR = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def setup_logging():

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.FileHandler(
                LOG_DIR / "pipeline.log"
            ),
            logging.StreamHandler()
        ]
    )

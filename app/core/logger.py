try:
    from loguru import logger
except ModuleNotFoundError:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    logger = logging.getLogger("shopwave")
    logger.debug("Loguru is not installed; using standard logging fallback.")

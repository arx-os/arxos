def test_logging_output(caplog):
    import structlog
    logger = structlog.get_logger()
    with caplog.at_level("INFO"):
        logger.info("test_event", value=42)
    assert any("test_event" in msg for msg in caplog.text) 
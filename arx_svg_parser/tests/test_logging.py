import pytest
import structlog
import asyncio
from arx_svg_parser.utils.logging import configure_logging, setup_logging_for_environment
from arx_svg_parser.utils.performance import log_performance, log_operation, PerformanceMonitor

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    configure_logging(log_level="DEBUG", enable_json=False)

def test_structured_logging(caplog):
    """Test structured logging output."""
    logger = structlog.get_logger(__name__)
    
    with caplog.at_level("INFO"):
        logger.info("test_event", user_id="123", action="login", status="success")
    
    # Verify structured log contains expected fields
    log_record = caplog.records[-1]
    assert "test_event" in log_record.message
    assert "user_id" in log_record.message
    assert "action" in log_record.message
    assert "status" in log_record.message

def test_log_levels(caplog):
    """Test different log levels."""
    logger = structlog.get_logger(__name__)
    
    with caplog.at_level("DEBUG"):
        logger.debug("debug_message", detail="debug_info")
        logger.info("info_message", detail="info_info")
        logger.warning("warning_message", detail="warning_info")
        logger.error("error_message", detail="error_info")
    
    # Verify all levels are logged
    messages = [record.message for record in caplog.records]
    assert any("debug_message" in msg for msg in messages)
    assert any("info_message" in msg for msg in messages)
    assert any("warning_message" in msg for msg in messages)
    assert any("error_message" in msg for msg in messages)

def test_performance_logging_decorator():
    """Test performance logging decorator."""
    @log_performance
    def test_function():
        return "success"
    
    result = test_function()
    assert result == "success"

@pytest.mark.asyncio
async def test_async_performance_logging():
    """Test async performance logging decorator."""
    @log_performance
    async def test_async_function():
        await asyncio.sleep(0.01)
        return "async_success"
    
    result = await test_async_function()
    assert result == "async_success"

def test_log_operation_context_manager(caplog):
    """Test log_operation context manager."""
    with caplog.at_level("INFO"):
        with log_operation("test_operation", user_id="123"):
            pass
    
    # Verify operation start and completion logs
    messages = [record.message for record in caplog.records]
    assert any("operation_start" in msg for msg in messages)
    assert any("operation_completed" in msg for msg in messages)

def test_performance_monitor_class(caplog):
    """Test PerformanceMonitor class."""
    with caplog.at_level("INFO"):
        with PerformanceMonitor("test_monitor", user_id="123"):
            pass
    
    # Verify monitor start and completion logs
    messages = [record.message for record in caplog.records]
    assert any("operation_start" in msg for msg in messages)
    assert any("operation_completed" in msg for msg in messages)

@pytest.mark.asyncio
async def test_async_performance_monitor(caplog):
    """Test async PerformanceMonitor class."""
    with caplog.at_level("INFO"):
        async with PerformanceMonitor("test_async_monitor", user_id="123"):
            await asyncio.sleep(0.01)
    
    # Verify monitor start and completion logs
    messages = [record.message for record in caplog.records]
    assert any("operation_start" in msg for msg in messages)
    assert any("operation_completed" in msg for msg in messages)

def test_error_logging(caplog):
    """Test error logging with context."""
    logger = structlog.get_logger(__name__)
    
    with caplog.at_level("ERROR"):
        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.error("operation_failed",
                        error=str(e),
                        error_type=type(e).__name__,
                        context="test_context")
    
    # Verify error log contains expected fields
    log_record = caplog.records[-1]
    assert "operation_failed" in log_record.message
    assert "Test error" in log_record.message
    assert "ValueError" in log_record.message

def test_environment_specific_logging():
    """Test environment-specific logging configuration."""
    # Test development environment
    setup_logging_for_environment()
    
    # Verify logging is configured
    logger = structlog.get_logger(__name__)
    logger.info("test_environment_logging", environment="test")

def test_logging_with_context_vars(caplog):
    """Test logging with context variables."""
    import structlog.contextvars
    
    logger = structlog.get_logger(__name__)
    
    # Bind context variables
    structlog.contextvars.bind_contextvars(
        request_id="test_req_123",
        user_id="test_user",
        operation="test_operation"
    )
    
    with caplog.at_level("INFO"):
        logger.info("context_test", additional_field="test_value")
    
    # Verify context variables are included in log
    log_record = caplog.records[-1]
    assert "request_id" in log_record.message
    assert "user_id" in log_record.message
    assert "operation" in log_record.message
    assert "additional_field" in log_record.message

def test_logging_performance_metrics(caplog):
    """Test logging with performance metrics."""
    logger = structlog.get_logger(__name__)
    
    with caplog.at_level("INFO"):
        logger.info("performance_test",
                   duration=0.123,
                   memory_usage="50MB",
                   cpu_usage="25%",
                   operation="test_operation")
    
    # Verify performance metrics are logged
    log_record = caplog.records[-1]
    assert "duration" in log_record.message
    assert "memory_usage" in log_record.message
    assert "cpu_usage" in log_record.message

def test_security_event_logging(caplog):
    """Test security event logging."""
    logger = structlog.get_logger(__name__)
    
    with caplog.at_level("WARNING"):
        logger.warning("security_event",
                      event_type="login_attempt",
                      user_id="test_user",
                      ip_address="192.168.1.1",
                      success=False,
                      reason="invalid_credentials")
    
    # Verify security event is logged
    log_record = caplog.records[-1]
    assert "security_event" in log_record.message
    assert "login_attempt" in log_record.message
    assert "test_user" in log_record.message 
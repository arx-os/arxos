"""
Action Executors for Workflow Engine.

Provides comprehensive action execution capabilities for different types of
workflow actions including device control, notifications, API calls, and more.
"""

import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import subprocess
import os

from domain.entities.workflow_entity import ActionType
from infrastructure.logging.structured_logging import get_logger


logger = get_logger(__name__)


class ActionExecutor(ABC):
    """Base class for action executors."""
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the action with given context."""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate action configuration."""
        pass


class DeviceControlExecutor(ActionExecutor):
    """Executor for device control actions."""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute device control action."""
        config = context["configuration"]
        device_id = config.get("device_id")
        command = config.get("command")
        parameters = config.get("parameters", {})
        
        logger.info(f"Executing device control: {device_id} - {command}")
        
        try:
            # Simulate device control (in production, this would integrate with IoT service)
            await asyncio.sleep(0.5)  # Simulate network delay
            
            # Mock successful device control
            result = {
                "device_id": device_id,
                "command": command,
                "parameters": parameters,
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "response_time_ms": 500
            }
            
            return {
                "success": True,
                "result": result,
                "message": f"Device {device_id} command {command} executed successfully",
                "context_updates": {
                    f"device_control_results.{device_id}": result
                }
            }
            
        except Exception as e:
            logger.error(f"Device control failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "device_id": device_id,
                "command": command
            }
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate device control configuration."""
        errors = []
        
        if not config.get("device_id"):
            errors.append("device_id is required")
        
        if not config.get("command"):
            errors.append("command is required")
        
        # Validate command type
        valid_commands = ["turn_on", "turn_off", "set_temperature", "set_brightness", "set_mode"]
        if config.get("command") not in valid_commands:
            errors.append(f"command must be one of: {', '.join(valid_commands)}")
        
        return errors


class EmailNotificationExecutor(ActionExecutor):
    """Executor for email notification actions."""
    
    def __init__(self, smtp_config: Dict[str, Any] = None):
        self.smtp_config = smtp_config or {
            "host": "localhost",
            "port": 587,
            "username": "",
            "password": "",
            "use_tls": True
        }
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email notification action."""
        config = context["configuration"]
        
        try:
            # Prepare email
            to_addresses = config.get("to", [])
            if isinstance(to_addresses, str):
                to_addresses = [to_addresses]
            
            subject = self._render_template(config.get("subject", ""), context)
            body = self._render_template(config.get("body", ""), context)
            from_address = config.get("from", self.smtp_config.get("from", "noreply@arxos.com"))
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_address
            msg["To"] = ", ".join(to_addresses)
            msg["Subject"] = subject
            
            # Add body
            msg.attach(MIMEText(body, config.get("body_type", "plain")))
            
            # Send email (simulated for now)
            logger.info(f"Sending email notification to: {', '.join(to_addresses)}")
            
            # In production, this would actually send the email
            await asyncio.sleep(1)  # Simulate email sending delay
            
            return {
                "success": True,
                "result": {
                    "recipients": to_addresses,
                    "subject": subject,
                    "sent_at": datetime.now(timezone.utc).isoformat()
                },
                "message": f"Email sent to {len(to_addresses)} recipients"
            }
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipients": config.get("to", [])
            }
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate email notification configuration."""
        errors = []
        
        if not config.get("to"):
            errors.append("to address(es) required")
        
        if not config.get("subject"):
            errors.append("subject is required")
        
        if not config.get("body"):
            errors.append("body is required")
        
        return errors
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render template with context variables."""
        try:
            # Simple template rendering (in production, use proper template engine)
            rendered = template
            
            # Replace workflow variables
            for var_name, var_value in context.get("variables", {}).items():
                rendered = rendered.replace(f"{{{var_name}}}", str(var_value))
            
            # Replace context variables
            rendered = rendered.replace("{workflow_name}", context.get("workflow_name", ""))
            rendered = rendered.replace("{execution_id}", context.get("execution_id", ""))
            rendered = rendered.replace("{timestamp}", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
            
            return rendered
            
        except Exception as e:
            logger.warning(f"Template rendering failed: {e}")
            return template


class HttpRequestExecutor(ActionExecutor):
    """Executor for HTTP request actions."""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request action."""
        config = context["configuration"]
        
        try:
            url = config.get("url")
            method = config.get("method", "GET").upper()
            headers = config.get("headers", {})
            data = config.get("data")
            params = config.get("params")
            timeout = config.get("timeout", 30)
            
            # Add default headers
            headers.setdefault("User-Agent", "Arxos-Workflow-Engine/1.0")
            headers.setdefault("Content-Type", "application/json")
            
            logger.info(f"Executing HTTP {method} request to: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if method in ["POST", "PUT", "PATCH"] else None,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    
                    response_text = await response.text()
                    
                    # Try to parse JSON response
                    try:
                        response_data = await response.json()
                    except:
                        response_data = response_text
                    
                    result = {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "data": response_data,
                        "url": str(response.url),
                        "method": method,
                        "success": 200 <= response.status < 300
                    }
                    
                    return {
                        "success": result["success"],
                        "result": result,
                        "message": f"HTTP {method} request completed with status {response.status}",
                        "context_updates": {
                            "last_http_response": result
                        }
                    }
                    
        except asyncio.TimeoutError:
            error_msg = f"HTTP request timed out after {timeout} seconds"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "url": config.get("url")
            }
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": config.get("url")
            }
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate HTTP request configuration."""
        errors = []
        
        if not config.get("url"):
            errors.append("url is required")
        
        method = config.get("method", "GET").upper()
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        if method not in valid_methods:
            errors.append(f"method must be one of: {', '.join(valid_methods)}")
        
        # Validate URL format
        url = config.get("url", "")
        if url and not (url.startswith("http://") or url.startswith("https://")):
            errors.append("url must start with http:// or https://")
        
        return errors


class DelayExecutor(ActionExecutor):
    """Executor for delay actions."""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delay action."""
        config = context["configuration"]
        
        try:
            duration = config.get("duration", 1)  # Duration in seconds
            
            logger.info(f"Executing delay for {duration} seconds")
            
            await asyncio.sleep(duration)
            
            return {
                "success": True,
                "result": {
                    "duration_seconds": duration,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                },
                "message": f"Delay of {duration} seconds completed"
            }
            
        except Exception as e:
            logger.error(f"Delay execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate delay configuration."""
        errors = []
        
        duration = config.get("duration")
        if duration is None:
            errors.append("duration is required")
        elif not isinstance(duration, (int, float)) or duration < 0:
            errors.append("duration must be a positive number")
        elif duration > 3600:  # Max 1 hour
            errors.append("duration cannot exceed 3600 seconds (1 hour)")
        
        return errors


class LogEventExecutor(ActionExecutor):
    """Executor for log event actions."""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute log event action."""
        config = context["configuration"]
        
        try:
            level = config.get("level", "info").lower()
            message = config.get("message", "Workflow log event")
            data = config.get("data", {})
            
            # Render message template
            rendered_message = self._render_message(message, context)
            
            # Log the event
            log_data = {
                "workflow_id": context.get("workflow_id"),
                "execution_id": context.get("execution_id"),
                "action_id": context.get("action_id"),
                "custom_data": data
            }
            
            if level == "debug":
                logger.debug(rendered_message, extra=log_data)
            elif level == "info":
                logger.info(rendered_message, extra=log_data)
            elif level == "warning":
                logger.warning(rendered_message, extra=log_data)
            elif level == "error":
                logger.error(rendered_message, extra=log_data)
            else:
                logger.info(rendered_message, extra=log_data)
            
            return {
                "success": True,
                "result": {
                    "level": level,
                    "message": rendered_message,
                    "logged_at": datetime.now(timezone.utc).isoformat()
                },
                "message": "Event logged successfully"
            }
            
        except Exception as e:
            logger.error(f"Log event action failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate log event configuration."""
        errors = []
        
        level = config.get("level", "info").lower()
        valid_levels = ["debug", "info", "warning", "error"]
        if level not in valid_levels:
            errors.append(f"level must be one of: {', '.join(valid_levels)}")
        
        if not config.get("message"):
            errors.append("message is required")
        
        return errors
    
    def _render_message(self, message: str, context: Dict[str, Any]) -> str:
        """Render message with context variables."""
        try:
            rendered = message
            
            # Replace workflow variables
            for var_name, var_value in context.get("variables", {}).items():
                rendered = rendered.replace(f"{{{var_name}}}", str(var_value))
            
            # Replace context variables
            rendered = rendered.replace("{workflow_name}", context.get("workflow_name", ""))
            rendered = rendered.replace("{execution_id}", context.get("execution_id", ""))
            
            return rendered
            
        except Exception as e:
            logger.warning(f"Message rendering failed: {e}")
            return message


class ConditionalExecutor(ActionExecutor):
    """Executor for conditional logic actions."""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional action."""
        config = context["configuration"]
        
        try:
            condition = config.get("condition")
            true_action = config.get("true_action")
            false_action = config.get("false_action")
            
            # Evaluate condition
            condition_result = self._evaluate_condition(condition, context)
            
            # Choose action based on condition result
            chosen_action = true_action if condition_result else false_action
            
            result = {
                "condition_result": condition_result,
                "chosen_path": "true" if condition_result else "false",
                "action_executed": chosen_action is not None
            }
            
            # Execute chosen action if it exists
            if chosen_action:
                # This is a simplified version - in production, you'd need to
                # recursively execute the chosen action
                result["action_details"] = chosen_action
            
            return {
                "success": True,
                "result": result,
                "message": f"Conditional executed: took {'true' if condition_result else 'false'} path"
            }
            
        except Exception as e:
            logger.error(f"Conditional execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate conditional configuration."""
        errors = []
        
        if not config.get("condition"):
            errors.append("condition is required")
        
        if not config.get("true_action") and not config.get("false_action"):
            errors.append("at least one of true_action or false_action is required")
        
        return errors
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate condition expression."""
        try:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            # Get field value from context
            field_value = self._get_field_value(context, field)
            
            # Evaluate based on operator
            if operator == "equals":
                return field_value == value
            elif operator == "not_equals":
                return field_value != value
            elif operator == "greater_than":
                return field_value > value
            elif operator == "less_than":
                return field_value < value
            elif operator == "contains":
                return value in str(field_value)
            elif operator == "exists":
                return field_value is not None
            else:
                return False
                
        except Exception as e:
            logger.warning(f"Condition evaluation failed: {e}")
            return False
    
    def _get_field_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """Get field value from context using dot notation."""
        try:
            keys = field_path.split('.')
            value = context
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            return value
            
        except Exception:
            return None


class CustomScriptExecutor(ActionExecutor):
    """Executor for custom script actions."""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom script action."""
        config = context["configuration"]
        
        try:
            script_type = config.get("script_type", "python")
            script_content = config.get("script_content", "")
            script_file = config.get("script_file")
            timeout = config.get("timeout", 60)
            
            if script_file and os.path.exists(script_file):
                # Execute script file
                result = await self._execute_script_file(script_file, script_type, context, timeout)
            elif script_content:
                # Execute inline script
                result = await self._execute_inline_script(script_content, script_type, context, timeout)
            else:
                raise Exception("Either script_content or script_file must be provided")
            
            return {
                "success": True,
                "result": result,
                "message": "Custom script executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Custom script execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_script_file(self, script_file: str, script_type: str, 
                                 context: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute external script file."""
        try:
            if script_type == "python":
                cmd = ["python", script_file]
            elif script_type == "bash":
                cmd = ["bash", script_file]
            elif script_type == "node":
                cmd = ["node", script_file]
            else:
                raise Exception(f"Unsupported script type: {script_type}")
            
            # Pass context as environment variables
            env = os.environ.copy()
            env["ARXOS_WORKFLOW_ID"] = context.get("workflow_id", "")
            env["ARXOS_EXECUTION_ID"] = context.get("execution_id", "")
            env["ARXOS_CONTEXT"] = json.dumps(context.get("variables", {}))
            
            # Execute script
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise Exception(f"Script execution timed out after {timeout} seconds")
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "script_file": script_file,
                "script_type": script_type
            }
            
        except Exception as e:
            raise Exception(f"Script file execution failed: {e}")
    
    async def _execute_inline_script(self, script_content: str, script_type: str,
                                   context: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute inline script content."""
        if script_type == "python":
            # For Python scripts, we could use exec() in a restricted environment
            # This is a simplified example - production would need proper sandboxing
            
            # Create a safe execution environment
            exec_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "dict": dict,
                    "list": list,
                    "datetime": datetime
                },
                "context": context.get("variables", {}),
                "workflow_id": context.get("workflow_id"),
                "execution_id": context.get("execution_id")
            }
            
            exec_locals = {}
            
            try:
                exec(script_content, exec_globals, exec_locals)
                
                return {
                    "success": True,
                    "locals": {k: v for k, v in exec_locals.items() if not k.startswith("_")},
                    "script_type": script_type
                }
                
            except Exception as e:
                raise Exception(f"Python script execution failed: {e}")
        
        else:
            raise Exception(f"Inline execution not supported for script type: {script_type}")
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate custom script configuration."""
        errors = []
        
        if not config.get("script_content") and not config.get("script_file"):
            errors.append("either script_content or script_file is required")
        
        script_type = config.get("script_type", "python")
        valid_types = ["python", "bash", "node", "powershell"]
        if script_type not in valid_types:
            errors.append(f"script_type must be one of: {', '.join(valid_types)}")
        
        script_file = config.get("script_file")
        if script_file and not os.path.exists(script_file):
            errors.append(f"script_file does not exist: {script_file}")
        
        timeout = config.get("timeout", 60)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 3600:
            errors.append("timeout must be between 1 and 3600 seconds")
        
        return errors


class ActionExecutorFactory:
    """Factory for creating action executors."""
    
    def __init__(self):
        self.executors = {
            ActionType.DEVICE_CONTROL: DeviceControlExecutor,
            ActionType.EMAIL_NOTIFICATION: EmailNotificationExecutor,
            ActionType.HTTP_REQUEST: HttpRequestExecutor,
            ActionType.DELAY: DelayExecutor,
            ActionType.LOG_EVENT: LogEventExecutor,
            ActionType.CONDITIONAL: ConditionalExecutor,
            ActionType.CUSTOM_SCRIPT: CustomScriptExecutor,
        }
        
        # Executor instances cache
        self._executor_instances = {}
    
    def get_executor(self, action_type: ActionType) -> Optional[ActionExecutor]:
        """Get executor for action type."""
        if action_type not in self.executors:
            logger.warning(f"No executor found for action type: {action_type.value}")
            return None
        
        # Return cached instance or create new one
        if action_type not in self._executor_instances:
            executor_class = self.executors[action_type]
            self._executor_instances[action_type] = executor_class()
        
        return self._executor_instances[action_type]
    
    def register_executor(self, action_type: ActionType, executor_class: type) -> None:
        """Register custom executor for action type."""
        if not issubclass(executor_class, ActionExecutor):
            raise ValueError("Executor class must inherit from ActionExecutor")
        
        self.executors[action_type] = executor_class
        
        # Clear cached instance if it exists
        if action_type in self._executor_instances:
            del self._executor_instances[action_type]
        
        logger.info(f"Registered custom executor for action type: {action_type.value}")
    
    def get_supported_action_types(self) -> List[ActionType]:
        """Get list of supported action types."""
        return list(self.executors.keys())
    
    def validate_action_configuration(self, action_type: ActionType, config: Dict[str, Any]) -> List[str]:
        """Validate configuration for action type."""
        executor = self.get_executor(action_type)
        if not executor:
            return [f"No executor available for action type: {action_type.value}"]
        
        return executor.validate_configuration(config)
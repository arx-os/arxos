"""
Integration Connector Templates.

Pre-built connector templates for common enterprise integration patterns
and systems including databases, APIs, message queues, and file systems.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

from domain.entities.integration_entity import (
    IntegrationType, DataFormat, IntegrationDirection,
    TransformationType, ConnectorStatus
)
from infrastructure.logging.structured_logging import get_logger


logger = get_logger(__name__)


class ConnectorTemplateManager:
    """Manager for integration connector templates."""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize built-in connector templates."""
        return {
            # REST API Templates
            "rest_api_json": self._create_rest_api_template(),
            "rest_api_xml": self._create_rest_api_xml_template(),
            "rest_api_paginated": self._create_rest_api_paginated_template(),
            
            # Database Templates
            "mysql_connector": self._create_mysql_template(),
            "postgresql_connector": self._create_postgresql_template(),
            "mssql_connector": self._create_mssql_template(),
            
            # Message Queue Templates
            "rabbitmq_connector": self._create_rabbitmq_template(),
            "kafka_connector": self._create_kafka_template(),
            "sqs_connector": self._create_sqs_template(),
            
            # File System Templates
            "file_json": self._create_file_json_template(),
            "file_csv": self._create_file_csv_template(),
            "file_xml": self._create_file_xml_template(),
            
            # FTP Templates
            "ftp_connector": self._create_ftp_template(),
            "sftp_connector": self._create_sftp_template(),
            
            # Enterprise System Templates
            "salesforce_connector": self._create_salesforce_template(),
            "sap_connector": self._create_sap_template(),
            "sharepoint_connector": self._create_sharepoint_template(),
            
            # Cloud Service Templates
            "aws_s3_connector": self._create_aws_s3_template(),
            "azure_blob_connector": self._create_azure_blob_template(),
            "gcp_storage_connector": self._create_gcp_storage_template(),
        }
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get connector template by ID."""
        if template_id not in self.templates:
            raise ValueError(f"Template not found: {template_id}")
        
        # Return a deep copy to avoid template modification
        import copy
        return copy.deepcopy(self.templates[template_id])
    
    def list_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """List available connector templates."""
        templates = []
        
        for template_id, template_data in self.templates.items():
            if category and template_data.get("category") != category:
                continue
            
            templates.append({
                "id": template_id,
                "name": template_data["name"],
                "description": template_data["description"],
                "category": template_data.get("category", "general"),
                "connector_type": template_data["connector_type"],
                "direction": template_data["direction"],
                "tags": template_data.get("tags", [])
            })
        
        return templates
    
    def create_connector_from_template(self, template_id: str, 
                                     template_params: Dict[str, Any]) -> Dict[str, Any]:
        """Create connector configuration from template."""
        template = self.get_template(template_id)
        
        # Replace template parameters
        connector_config = self._replace_template_parameters(template, template_params)
        
        # Add timestamp
        connector_config["created_from_template"] = {
            "template_id": template_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        return connector_config
    
    def _replace_template_parameters(self, template: Dict[str, Any], 
                                   params: Dict[str, Any]) -> Dict[str, Any]:
        """Replace template parameters with actual values."""
        import json
        import re
        
        # Convert to JSON string for easy replacement
        template_json = json.dumps(template)
        
        # Replace parameters in format {{parameter_name}}
        for param_name, param_value in params.items():
            pattern = f"{{{{{param_name}}}}}"
            template_json = template_json.replace(pattern, str(param_value))
        
        # Convert back to dict
        return json.loads(template_json)
    
    # REST API Templates
    def _create_rest_api_template(self) -> Dict[str, Any]:
        """Create REST API JSON connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "REST API connector for {{api_name}}",
            "category": "api",
            "connector_type": IntegrationType.REST_API.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.JSON.value,
            "output_format": DataFormat.JSON.value,
            "source_endpoint": {
                "name": "{{api_name}} API Source",
                "url": "{{base_url}}/{{endpoint_path}}",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "{{auth_type}}",
                    "username": "{{username}}",
                    "password": "{{password}}",
                    "token": "{{api_token}}",
                    "key": "{{api_key_header}}",
                    "value": "{{api_key_value}}"
                },
                "headers": {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Arxos-Integration/1.0"
                },
                "timeout_seconds": 30,
                "retry_config": {
                    "max_retries": 3,
                    "backoff_factor": 2
                }
            },
            "target_endpoint": {
                "name": "{{api_name}} API Target",
                "url": "{{base_url}}/{{endpoint_path}}",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "{{auth_type}}",
                    "username": "{{username}}",
                    "password": "{{password}}",
                    "token": "{{api_token}}",
                    "key": "{{api_key_header}}",
                    "value": "{{api_key_value}}"
                },
                "headers": {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                "parameters": {
                    "method": "POST"
                }
            },
            "transformations": [],
            "error_handling": {
                "retry_on_failure": True,
                "max_retry_attempts": 3,
                "retry_delay_seconds": 5,
                "stop_on_error": False
            },
            "health_check_config": {
                "enabled": True,
                "endpoint": "{{base_url}}/health",
                "interval_seconds": 300
            },
            "tags": ["rest-api", "json", "{{api_name}}"]
        }
    
    def _create_rest_api_xml_template(self) -> Dict[str, Any]:
        """Create REST API XML connector template."""
        template = self._create_rest_api_template()
        template["input_format"] = DataFormat.XML.value
        template["output_format"] = DataFormat.XML.value
        template["source_endpoint"]["data_format"] = DataFormat.XML.value
        template["target_endpoint"]["data_format"] = DataFormat.XML.value
        template["source_endpoint"]["headers"]["Accept"] = "application/xml"
        template["source_endpoint"]["headers"]["Content-Type"] = "application/xml"
        template["target_endpoint"]["headers"]["Accept"] = "application/xml"
        template["target_endpoint"]["headers"]["Content-Type"] = "application/xml"
        template["tags"] = ["rest-api", "xml", "{{api_name}}"]
        return template
    
    def _create_rest_api_paginated_template(self) -> Dict[str, Any]:
        """Create paginated REST API connector template."""
        template = self._create_rest_api_template()
        template["source_endpoint"]["parameters"] = {
            "page": 1,
            "limit": 100,
            "pagination_style": "page_based"  # or "offset_based", "cursor_based"
        }
        template["transformations"] = [
            {
                "name": "Extract Pagination Data",
                "transformation_type": TransformationType.FIELD_MAPPING.value,
                "transformation_logic": {
                    "mapping": {
                        "data": "records",
                        "pagination.page": "current_page",
                        "pagination.total": "total_records"
                    }
                },
                "enabled": True,
                "order": 1
            }
        ]
        template["tags"].append("paginated")
        return template
    
    # Database Templates
    def _create_mysql_template(self) -> Dict[str, Any]:
        """Create MySQL connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "MySQL database connector for {{database_name}}",
            "category": "database",
            "connector_type": IntegrationType.DATABASE.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.JSON.value,
            "output_format": DataFormat.JSON.value,
            "source_endpoint": {
                "name": "MySQL Source",
                "url": "mysql://{{host}}:{{port}}/{{database_name}}",
                "integration_type": IntegrationType.DATABASE.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "basic",
                    "username": "{{username}}",
                    "password": "{{password}}"
                },
                "parameters": {
                    "connection_string": "mysql://{{username}}:{{password}}@{{host}}:{{port}}/{{database_name}}",
                    "query": "{{select_query}}",
                    "connection_pool_size": 10,
                    "connection_timeout": 30
                }
            },
            "target_endpoint": {
                "name": "MySQL Target",
                "url": "mysql://{{host}}:{{port}}/{{database_name}}",
                "integration_type": IntegrationType.DATABASE.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "basic",
                    "username": "{{username}}",
                    "password": "{{password}}"
                },
                "parameters": {
                    "connection_string": "mysql://{{username}}:{{password}}@{{host}}:{{port}}/{{database_name}}",
                    "table_name": "{{target_table}}",
                    "operation": "{{operation}}"  # insert, update, upsert
                }
            },
            "transformations": [
                {
                    "name": "Database Field Mapping",
                    "transformation_type": TransformationType.FIELD_MAPPING.value,
                    "transformation_logic": {
                        "mapping": {}  # To be filled with actual field mappings
                    },
                    "enabled": True,
                    "order": 1
                }
            ],
            "error_handling": {
                "dead_letter_queue": "failed_db_records",
                "retry_on_failure": True,
                "max_retry_attempts": 3
            },
            "tags": ["database", "mysql", "sql"]
        }
    
    def _create_postgresql_template(self) -> Dict[str, Any]:
        """Create PostgreSQL connector template."""
        template = self._create_mysql_template()
        template["description"] = "PostgreSQL database connector for {{database_name}}"
        template["source_endpoint"]["url"] = "postgresql://{{host}}:{{port}}/{{database_name}}"
        template["target_endpoint"]["url"] = "postgresql://{{host}}:{{port}}/{{database_name}}"
        template["source_endpoint"]["parameters"]["connection_string"] = "postgresql://{{username}}:{{password}}@{{host}}:{{port}}/{{database_name}}"
        template["target_endpoint"]["parameters"]["connection_string"] = "postgresql://{{username}}:{{password}}@{{host}}:{{port}}/{{database_name}}"
        template["tags"] = ["database", "postgresql", "sql"]
        return template
    
    def _create_mssql_template(self) -> Dict[str, Any]:
        """Create SQL Server connector template."""
        template = self._create_mysql_template()
        template["description"] = "SQL Server database connector for {{database_name}}"
        template["source_endpoint"]["url"] = "mssql://{{host}}:{{port}}/{{database_name}}"
        template["target_endpoint"]["url"] = "mssql://{{host}}:{{port}}/{{database_name}}"
        template["source_endpoint"]["parameters"]["connection_string"] = "mssql://{{username}}:{{password}}@{{host}}:{{port}}/{{database_name}}"
        template["target_endpoint"]["parameters"]["connection_string"] = "mssql://{{username}}:{{password}}@{{host}}:{{port}}/{{database_name}}"
        template["tags"] = ["database", "mssql", "sql-server", "sql"]
        return template
    
    # Message Queue Templates
    def _create_rabbitmq_template(self) -> Dict[str, Any]:
        """Create RabbitMQ connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "RabbitMQ message queue connector for {{queue_name}}",
            "category": "messaging",
            "connector_type": IntegrationType.MESSAGE_QUEUE.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.JSON.value,
            "output_format": DataFormat.JSON.value,
            "source_endpoint": {
                "name": "RabbitMQ Consumer",
                "url": "amqp://{{host}}:{{port}}/{{vhost}}",
                "integration_type": IntegrationType.MESSAGE_QUEUE.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "basic",
                    "username": "{{username}}",
                    "password": "{{password}}"
                },
                "parameters": {
                    "queue_name": "{{queue_name}}",
                    "exchange": "{{exchange_name}}",
                    "routing_key": "{{routing_key}}",
                    "durable": True,
                    "auto_ack": False,
                    "prefetch_count": 10
                }
            },
            "target_endpoint": {
                "name": "RabbitMQ Producer",
                "url": "amqp://{{host}}:{{port}}/{{vhost}}",
                "integration_type": IntegrationType.MESSAGE_QUEUE.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "basic",
                    "username": "{{username}}",
                    "password": "{{password}}"
                },
                "parameters": {
                    "queue_name": "{{target_queue_name}}",
                    "exchange": "{{target_exchange_name}}",
                    "routing_key": "{{target_routing_key}}",
                    "delivery_mode": 2  # Persistent
                }
            },
            "error_handling": {
                "dead_letter_exchange": "dlx",
                "dead_letter_routing_key": "failed.{{queue_name}}"
            },
            "tags": ["messaging", "rabbitmq", "amqp"]
        }
    
    def _create_kafka_template(self) -> Dict[str, Any]:
        """Create Apache Kafka connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "Apache Kafka connector for {{topic_name}}",
            "category": "messaging",
            "connector_type": IntegrationType.MESSAGE_QUEUE.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.JSON.value,
            "output_format": DataFormat.JSON.value,
            "source_endpoint": {
                "name": "Kafka Consumer",
                "url": "kafka://{{broker_list}}",
                "integration_type": IntegrationType.MESSAGE_QUEUE.value,
                "data_format": DataFormat.JSON.value,
                "parameters": {
                    "topic": "{{topic_name}}",
                    "consumer_group": "{{consumer_group}}",
                    "auto_offset_reset": "latest",
                    "enable_auto_commit": False,
                    "max_poll_records": 500
                }
            },
            "target_endpoint": {
                "name": "Kafka Producer",
                "url": "kafka://{{broker_list}}",
                "integration_type": IntegrationType.MESSAGE_QUEUE.value,
                "data_format": DataFormat.JSON.value,
                "parameters": {
                    "topic": "{{target_topic_name}}",
                    "acks": "all",
                    "retries": 3,
                    "batch_size": 16384,
                    "compression_type": "gzip"
                }
            },
            "tags": ["messaging", "kafka", "streaming"]
        }
    
    def _create_sqs_template(self) -> Dict[str, Any]:
        """Create Amazon SQS connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "Amazon SQS connector for {{queue_name}}",
            "category": "messaging",
            "connector_type": IntegrationType.MESSAGE_QUEUE.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.JSON.value,
            "output_format": DataFormat.JSON.value,
            "source_endpoint": {
                "name": "SQS Consumer",
                "url": "https://sqs.{{region}}.amazonaws.com/{{account_id}}/{{queue_name}}",
                "integration_type": IntegrationType.MESSAGE_QUEUE.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "aws",
                    "access_key": "{{aws_access_key}}",
                    "secret_key": "{{aws_secret_key}}",
                    "region": "{{region}}"
                },
                "parameters": {
                    "queue_name": "{{queue_name}}",
                    "wait_time_seconds": 20,
                    "max_messages": 10,
                    "visibility_timeout": 300
                }
            },
            "target_endpoint": {
                "name": "SQS Producer",
                "url": "https://sqs.{{region}}.amazonaws.com/{{account_id}}/{{target_queue_name}}",
                "integration_type": IntegrationType.MESSAGE_QUEUE.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "aws",
                    "access_key": "{{aws_access_key}}",
                    "secret_key": "{{aws_secret_key}}",
                    "region": "{{region}}"
                },
                "parameters": {
                    "queue_name": "{{target_queue_name}}",
                    "message_group_id": "{{message_group_id}}",
                    "deduplication_id": "auto"
                }
            },
            "tags": ["messaging", "sqs", "aws", "cloud"]
        }
    
    # File System Templates
    def _create_file_json_template(self) -> Dict[str, Any]:
        """Create JSON file connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "JSON file connector for {{file_description}}",
            "category": "file",
            "connector_type": IntegrationType.FILE_SYSTEM.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.JSON.value,
            "output_format": DataFormat.JSON.value,
            "source_endpoint": {
                "name": "JSON File Reader",
                "url": "file://{{source_file_path}}",
                "integration_type": IntegrationType.FILE_SYSTEM.value,
                "data_format": DataFormat.JSON.value,
                "parameters": {
                    "file_path": "{{source_file_path}}",
                    "encoding": "utf-8",
                    "watch_for_changes": "{{watch_changes}}"
                }
            },
            "target_endpoint": {
                "name": "JSON File Writer",
                "url": "file://{{target_file_path}}",
                "integration_type": IntegrationType.FILE_SYSTEM.value,
                "data_format": DataFormat.JSON.value,
                "parameters": {
                    "file_path": "{{target_file_path}}",
                    "encoding": "utf-8",
                    "overwrite": "{{overwrite_file}}",
                    "create_directories": True
                }
            },
            "error_handling": {
                "backup_failed_files": True,
                "backup_directory": "{{backup_directory}}"
            },
            "tags": ["file-system", "json", "local"]
        }
    
    def _create_file_csv_template(self) -> Dict[str, Any]:
        """Create CSV file connector template."""
        template = self._create_file_json_template()
        template["description"] = "CSV file connector for {{file_description}}"
        template["input_format"] = DataFormat.CSV.value
        template["output_format"] = DataFormat.CSV.value
        template["source_endpoint"]["data_format"] = DataFormat.CSV.value
        template["target_endpoint"]["data_format"] = DataFormat.CSV.value
        template["source_endpoint"]["parameters"]["delimiter"] = "{{delimiter}}"
        template["source_endpoint"]["parameters"]["has_header"] = "{{has_header}}"
        template["target_endpoint"]["parameters"]["delimiter"] = "{{delimiter}}"
        template["target_endpoint"]["parameters"]["include_header"] = "{{include_header}}"
        template["tags"] = ["file-system", "csv", "local"]
        return template
    
    def _create_file_xml_template(self) -> Dict[str, Any]:
        """Create XML file connector template."""
        template = self._create_file_json_template()
        template["description"] = "XML file connector for {{file_description}}"
        template["input_format"] = DataFormat.XML.value
        template["output_format"] = DataFormat.XML.value
        template["source_endpoint"]["data_format"] = DataFormat.XML.value
        template["target_endpoint"]["data_format"] = DataFormat.XML.value
        template["source_endpoint"]["parameters"]["root_element"] = "{{root_element}}"
        template["source_endpoint"]["parameters"]["namespace"] = "{{namespace}}"
        template["target_endpoint"]["parameters"]["root_element"] = "{{root_element}}"
        template["target_endpoint"]["parameters"]["namespace"] = "{{namespace}}"
        template["tags"] = ["file-system", "xml", "local"]
        return template
    
    # FTP Templates
    def _create_ftp_template(self) -> Dict[str, Any]:
        """Create FTP connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "FTP connector for {{server_description}}",
            "category": "file-transfer",
            "connector_type": IntegrationType.FTP_SFTP.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.PLAIN_TEXT.value,
            "output_format": DataFormat.PLAIN_TEXT.value,
            "source_endpoint": {
                "name": "FTP Source",
                "url": "ftp://{{host}}:{{port}}",
                "integration_type": IntegrationType.FTP_SFTP.value,
                "data_format": DataFormat.PLAIN_TEXT.value,
                "authentication": {
                    "type": "basic",
                    "username": "{{username}}",
                    "password": "{{password}}"
                },
                "parameters": {
                    "host": "{{host}}",
                    "port": "{{port}}",
                    "directory": "{{source_directory}}",
                    "file_pattern": "{{file_pattern}}",
                    "passive_mode": True,
                    "binary_mode": "{{binary_mode}}"
                }
            },
            "target_endpoint": {
                "name": "FTP Target",
                "url": "ftp://{{host}}:{{port}}",
                "integration_type": IntegrationType.FTP_SFTP.value,
                "data_format": DataFormat.PLAIN_TEXT.value,
                "authentication": {
                    "type": "basic",
                    "username": "{{username}}",
                    "password": "{{password}}"
                },
                "parameters": {
                    "host": "{{host}}",
                    "port": "{{port}}",
                    "directory": "{{target_directory}}",
                    "overwrite": "{{overwrite_files}}"
                }
            },
            "tags": ["ftp", "file-transfer", "remote"]
        }
    
    def _create_sftp_template(self) -> Dict[str, Any]:
        """Create SFTP connector template."""
        template = self._create_ftp_template()
        template["description"] = "SFTP connector for {{server_description}}"
        template["source_endpoint"]["url"] = "sftp://{{host}}:{{port}}"
        template["target_endpoint"]["url"] = "sftp://{{host}}:{{port}}"
        template["source_endpoint"]["authentication"]["type"] = "ssh_key"
        template["source_endpoint"]["authentication"]["private_key"] = "{{private_key_path}}"
        template["target_endpoint"]["authentication"]["type"] = "ssh_key"
        template["target_endpoint"]["authentication"]["private_key"] = "{{private_key_path}}"
        template["tags"] = ["sftp", "ssh", "file-transfer", "remote", "secure"]
        return template
    
    # Enterprise System Templates
    def _create_salesforce_template(self) -> Dict[str, Any]:
        """Create Salesforce connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "Salesforce CRM connector for {{object_name}}",
            "category": "enterprise",
            "connector_type": IntegrationType.REST_API.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.JSON.value,
            "output_format": DataFormat.JSON.value,
            "source_endpoint": {
                "name": "Salesforce API",
                "url": "https://{{instance}}.salesforce.com/services/data/v{{api_version}}/sobjects/{{object_name}}",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "oauth2",
                    "client_id": "{{client_id}}",
                    "client_secret": "{{client_secret}}",
                    "username": "{{username}}",
                    "password": "{{password}}",
                    "security_token": "{{security_token}}"
                },
                "headers": {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            },
            "target_endpoint": {
                "name": "Salesforce API",
                "url": "https://{{instance}}.salesforce.com/services/data/v{{api_version}}/sobjects/{{object_name}}",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "oauth2",
                    "client_id": "{{client_id}}",
                    "client_secret": "{{client_secret}}",
                    "username": "{{username}}",
                    "password": "{{password}}",
                    "security_token": "{{security_token}}"
                },
                "parameters": {
                    "method": "POST"
                }
            },
            "transformations": [
                {
                    "name": "Salesforce Field Mapping",
                    "transformation_type": TransformationType.FIELD_MAPPING.value,
                    "transformation_logic": {
                        "mapping": {
                            # Common Salesforce field mappings
                            "name": "Name",
                            "email": "Email__c",
                            "phone": "Phone",
                            "created_date": "CreatedDate"
                        }
                    },
                    "enabled": True,
                    "order": 1
                }
            ],
            "tags": ["salesforce", "crm", "enterprise", "cloud"]
        }
    
    def _create_sap_template(self) -> Dict[str, Any]:
        """Create SAP connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "SAP ERP connector for {{module_name}}",
            "category": "enterprise",
            "connector_type": IntegrationType.SOAP_WEB_SERVICE.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.XML.value,
            "output_format": DataFormat.XML.value,
            "source_endpoint": {
                "name": "SAP SOAP Service",
                "url": "http://{{sap_host}}:{{port}}/sap/bc/srt/rfc/sap/{{service_name}}",
                "integration_type": IntegrationType.SOAP_WEB_SERVICE.value,
                "data_format": DataFormat.XML.value,
                "authentication": {
                    "type": "basic",
                    "username": "{{username}}",
                    "password": "{{password}}"
                },
                "headers": {
                    "SOAPAction": "{{soap_action}}",
                    "Content-Type": "text/xml; charset=utf-8"
                },
                "parameters": {
                    "service_name": "{{service_name}}",
                    "operation": "{{operation_name}}"
                }
            },
            "transformations": [
                {
                    "name": "SAP XML to JSON",
                    "transformation_type": TransformationType.VALUE_CONVERSION.value,
                    "transformation_logic": {
                        "conversion_type": "xml_to_json"
                    },
                    "enabled": True,
                    "order": 1
                }
            ],
            "tags": ["sap", "erp", "enterprise", "soap", "xml"]
        }
    
    def _create_sharepoint_template(self) -> Dict[str, Any]:
        """Create SharePoint connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "SharePoint connector for {{site_name}}",
            "category": "enterprise",
            "connector_type": IntegrationType.REST_API.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.JSON.value,
            "output_format": DataFormat.JSON.value,
            "source_endpoint": {
                "name": "SharePoint REST API",
                "url": "https://{{tenant}}.sharepoint.com/sites/{{site_name}}/_api/web/lists/getbytitle('{{list_name}}')/items",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.JSON.value,
                "authentication": {
                    "type": "oauth2",
                    "client_id": "{{client_id}}",
                    "client_secret": "{{client_secret}}",
                    "tenant_id": "{{tenant_id}}"
                },
                "headers": {
                    "Accept": "application/json;odata=verbose",
                    "Content-Type": "application/json;odata=verbose"
                }
            },
            "tags": ["sharepoint", "microsoft", "enterprise", "collaboration"]
        }
    
    # Cloud Service Templates
    def _create_aws_s3_template(self) -> Dict[str, Any]:
        """Create AWS S3 connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "AWS S3 connector for {{bucket_name}}",
            "category": "cloud-storage",
            "connector_type": IntegrationType.REST_API.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.BINARY.value,
            "output_format": DataFormat.BINARY.value,
            "source_endpoint": {
                "name": "AWS S3 Bucket",
                "url": "https://{{bucket_name}}.s3.{{region}}.amazonaws.com",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.BINARY.value,
                "authentication": {
                    "type": "aws",
                    "access_key": "{{aws_access_key}}",
                    "secret_key": "{{aws_secret_key}}",
                    "region": "{{region}}"
                },
                "parameters": {
                    "bucket_name": "{{bucket_name}}",
                    "prefix": "{{object_prefix}}",
                    "delimiter": "/"
                }
            },
            "target_endpoint": {
                "name": "AWS S3 Bucket",
                "url": "https://{{bucket_name}}.s3.{{region}}.amazonaws.com",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.BINARY.value,
                "authentication": {
                    "type": "aws",
                    "access_key": "{{aws_access_key}}",
                    "secret_key": "{{aws_secret_key}}",
                    "region": "{{region}}"
                },
                "parameters": {
                    "bucket_name": "{{bucket_name}}",
                    "storage_class": "{{storage_class}}",
                    "server_side_encryption": "{{encryption}}"
                }
            },
            "tags": ["aws", "s3", "cloud", "storage", "object-storage"]
        }
    
    def _create_azure_blob_template(self) -> Dict[str, Any]:
        """Create Azure Blob Storage connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "Azure Blob Storage connector for {{container_name}}",
            "category": "cloud-storage",
            "connector_type": IntegrationType.REST_API.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.BINARY.value,
            "output_format": DataFormat.BINARY.value,
            "source_endpoint": {
                "name": "Azure Blob Container",
                "url": "https://{{storage_account}}.blob.core.windows.net/{{container_name}}",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.BINARY.value,
                "authentication": {
                    "type": "azure",
                    "account_name": "{{storage_account}}",
                    "account_key": "{{account_key}}"
                },
                "parameters": {
                    "container_name": "{{container_name}}",
                    "prefix": "{{blob_prefix}}"
                }
            },
            "tags": ["azure", "blob-storage", "cloud", "storage", "microsoft"]
        }
    
    def _create_gcp_storage_template(self) -> Dict[str, Any]:
        """Create Google Cloud Storage connector template."""
        return {
            "name": "{{connector_name}}",
            "description": "Google Cloud Storage connector for {{bucket_name}}",
            "category": "cloud-storage",
            "connector_type": IntegrationType.REST_API.value,
            "direction": IntegrationDirection.BIDIRECTIONAL.value,
            "input_format": DataFormat.BINARY.value,
            "output_format": DataFormat.BINARY.value,
            "source_endpoint": {
                "name": "GCS Bucket",
                "url": "https://storage.googleapis.com/storage/v1/b/{{bucket_name}}/o",
                "integration_type": IntegrationType.REST_API.value,
                "data_format": DataFormat.BINARY.value,
                "authentication": {
                    "type": "gcp",
                    "service_account_key": "{{service_account_key}}",
                    "project_id": "{{project_id}}"
                },
                "parameters": {
                    "bucket_name": "{{bucket_name}}",
                    "prefix": "{{object_prefix}}"
                }
            },
            "tags": ["gcp", "cloud-storage", "cloud", "storage", "google"]
        }
    
    def add_custom_template(self, template_id: str, template_data: Dict[str, Any]) -> None:
        """Add custom connector template."""
        required_fields = ["name", "connector_type", "direction"]
        for field in required_fields:
            if field not in template_data:
                raise ValueError(f"Template missing required field: {field}")
        
        self.templates[template_id] = template_data
        logger.info(f"Added custom connector template: {template_id}")
    
    def get_template_categories(self) -> List[str]:
        """Get list of template categories."""
        categories = set()
        for template in self.templates.values():
            categories.add(template.get("category", "general"))
        return sorted(list(categories))
    
    def validate_template_parameters(self, template_id: str, params: Dict[str, Any]) -> List[str]:
        """Validate template parameters."""
        template = self.get_template(template_id)
        errors = []
        
        # Extract required parameters from template
        import re
        template_str = str(template)
        param_pattern = r'\{\{(\w+)\}\}'
        required_params = set(re.findall(param_pattern, template_str))
        
        # Check if all required parameters are provided
        for param in required_params:
            if param not in params or params[param] is None:
                errors.append(f"Missing required parameter: {param}")
        
        return errors
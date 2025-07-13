"""
Data Vendor API Expansion Service

Provides advanced analytics, data masking, encryption, audit logging,
and GDPR/HIPAA compliance features for vendor data APIs.
"""

import json
import hashlib
import hmac
import base64
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, Counter
import statistics
import numpy as np
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from structlog import get_logger

from .base_manager import BaseManager
from models.database import get_db
from utils.auth import get_current_user
from utils.logging_config import get_logger

logger = get_logger()


class DataMaskingLevel(Enum):
    """Data masking levels for sensitive information."""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
    CUSTOM = "custom"


class ComplianceType(Enum):
    """Compliance types supported by the system."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    CCPA = "ccpa"
    SOX = "sox"


@dataclass
class AnalyticsMetrics:
    """Analytics metrics container."""
    total_records: int
    unique_vendors: int
    data_quality_score: float
    compliance_score: float
    last_updated: datetime
    trends: Dict[str, Any]
    predictions: Dict[str, Any]


@dataclass
class DataMaskingRule:
    """Data masking rule configuration."""
    field_name: str
    masking_level: DataMaskingLevel
    custom_pattern: Optional[str] = None
    replacement_char: str = "*"
    preserve_length: bool = True


@dataclass
class ComplianceConfig:
    """Compliance configuration."""
    compliance_type: ComplianceType
    enabled: bool
    data_retention_days: int
    audit_logging: bool
    encryption_required: bool
    consent_required: bool


class DataVendorAPIExpansion(BaseManager):
    """
    Advanced Data Vendor API Expansion service providing analytics,
    data masking, encryption, audit logging, and compliance features.
    """
    
    def __init__(self):
        super().__init__()
        self.analytics_cache = {}
        self.masking_rules = {}
        self.compliance_configs = {}
        self.audit_log = []
        self.encryption_key = None
        self.redis_client = None
        self._lock = threading.RLock()
        
        # Initialize encryption
        self._initialize_encryption()
        
        # Initialize compliance configurations
        self._initialize_compliance_configs()
        
        # Initialize masking rules
        self._initialize_masking_rules()
        
        logger.info("Data Vendor API Expansion service initialized")
    
    def _initialize_encryption(self):
        """Initialize encryption key and Fernet cipher."""
        try:
            # In production, this should come from environment variables
            key = Fernet.generate_key()
            self.encryption_key = key
            self.cipher = Fernet(key)
            logger.info("Encryption initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def _initialize_compliance_configs(self):
        """Initialize compliance configurations."""
        self.compliance_configs = {
            ComplianceType.GDPR: ComplianceConfig(
                compliance_type=ComplianceType.GDPR,
                enabled=True,
                data_retention_days=2555,  # 7 years
                audit_logging=True,
                encryption_required=True,
                consent_required=True
            ),
            ComplianceType.HIPAA: ComplianceConfig(
                compliance_type=ComplianceType.HIPAA,
                enabled=True,
                data_retention_days=2555,  # 7 years
                audit_logging=True,
                encryption_required=True,
                consent_required=True
            ),
            ComplianceType.CCPA: ComplianceConfig(
                compliance_type=ComplianceType.CCPA,
                enabled=True,
                data_retention_days=2555,
                audit_logging=True,
                encryption_required=True,
                consent_required=True
            ),
            ComplianceType.SOX: ComplianceConfig(
                compliance_type=ComplianceType.SOX,
                enabled=True,
                data_retention_days=2555,
                audit_logging=True,
                encryption_required=True,
                consent_required=False
            )
        }
        logger.info("Compliance configurations initialized")
    
    def _initialize_masking_rules(self):
        """Initialize default data masking rules."""
        self.masking_rules = {
            "email": DataMaskingRule("email", DataMaskingLevel.PARTIAL, replacement_char="*"),
            "phone": DataMaskingRule("phone", DataMaskingLevel.FULL, replacement_char="#"),
            "ssn": DataMaskingRule("ssn", DataMaskingLevel.FULL, replacement_char="*"),
            "credit_card": DataMaskingRule("credit_card", DataMaskingLevel.FULL, replacement_char="*"),
            "address": DataMaskingRule("address", DataMaskingLevel.PARTIAL, replacement_char="*"),
            "name": DataMaskingRule("name", DataMaskingLevel.PARTIAL, replacement_char="*"),
            "ip_address": DataMaskingRule("ip_address", DataMaskingLevel.FULL, replacement_char="*"),
            "mac_address": DataMaskingRule("mac_address", DataMaskingLevel.FULL, replacement_char="*")
        }
        logger.info("Data masking rules initialized")
    
    def get_analytics(self, vendor_id: Optional[str] = None, 
                     time_range: Optional[str] = None,
                     metrics: Optional[List[str]] = None) -> AnalyticsMetrics:
        """
        Get comprehensive analytics for vendor data.
        
        Args:
            vendor_id: Specific vendor ID to analyze
            time_range: Time range for analysis (e.g., "7d", "30d", "1y")
            metrics: Specific metrics to calculate
            
        Returns:
            AnalyticsMetrics object with comprehensive analytics
        """
        try:
            with self._lock:
                cache_key = f"analytics:{vendor_id}:{time_range}:{hash(tuple(metrics or []))}"
                
                # Check cache first
                if cache_key in self.analytics_cache:
                    cached_data = self.analytics_cache[cache_key]
                    if time.time() - cached_data.get('timestamp', 0) < 300:  # 5 minute cache
                        return cached_data['data']
                
                # Calculate analytics
                analytics = self._calculate_analytics(vendor_id, time_range, metrics)
                
                # Cache results
                self.analytics_cache[cache_key] = {
                    'data': analytics,
                    'timestamp': time.time()
                }
                
                # Log analytics access
                self._log_audit_event("analytics_access", {
                    "vendor_id": vendor_id,
                    "time_range": time_range,
                    "metrics": metrics
                })
                
                return analytics
                
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            raise
    
    def _calculate_analytics(self, vendor_id: Optional[str], 
                           time_range: Optional[str], 
                           metrics: Optional[List[str]]) -> AnalyticsMetrics:
        """Calculate comprehensive analytics metrics."""
        try:
            db = next(get_db())
            
            # Base query
            query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT vendor_id) as unique_vendors,
                    AVG(data_quality_score) as avg_quality,
                    AVG(compliance_score) as avg_compliance,
                    MAX(updated_at) as last_updated
                FROM vendor_data
            """
            
            params = {}
            if vendor_id:
                query += " WHERE vendor_id = :vendor_id"
                params['vendor_id'] = vendor_id
            
            if time_range:
                # Add time range filtering
                days = self._parse_time_range(time_range)
                query += f" AND updated_at >= NOW() - INTERVAL '{days} days'"
            
            result = db.execute(text(query), params).fetchone()
            
            # Calculate trends
            trends = self._calculate_trends(db, vendor_id, time_range)
            
            # Calculate predictions
            predictions = self._calculate_predictions(db, vendor_id, time_range)
            
            return AnalyticsMetrics(
                total_records=result.total_records or 0,
                unique_vendors=result.unique_vendors or 0,
                data_quality_score=float(result.avg_quality or 0.0),
                compliance_score=float(result.avg_compliance or 0.0),
                last_updated=result.last_updated or datetime.now(),
                trends=trends,
                predictions=predictions
            )
            
        except Exception as e:
            logger.error(f"Error calculating analytics: {e}")
            raise
    
    def _calculate_trends(self, db: Session, vendor_id: Optional[str], 
                         time_range: Optional[str]) -> Dict[str, Any]:
        """Calculate data trends over time."""
        try:
            trends = {
                "data_growth": [],
                "quality_improvement": [],
                "compliance_trends": [],
                "vendor_activity": []
            }
            
            # Calculate data growth trend
            growth_query = """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM vendor_data
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """
            
            if vendor_id:
                growth_query = growth_query.replace("WHERE", f"WHERE vendor_id = '{vendor_id}' AND")
            
            growth_results = db.execute(text(growth_query)).fetchall()
            
            for row in growth_results:
                trends["data_growth"].append({
                    "date": row.date.isoformat(),
                    "count": row.count
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {}
    
    def _calculate_predictions(self, db: Session, vendor_id: Optional[str], 
                             time_range: Optional[str]) -> Dict[str, Any]:
        """Calculate predictive analytics."""
        try:
            predictions = {
                "data_growth_forecast": [],
                "quality_prediction": 0.0,
                "compliance_risk": "low"
            }
            
            # Simple linear regression for data growth
            growth_data = self._get_historical_growth(db, vendor_id)
            if len(growth_data) > 1:
                # Calculate simple trend
                x = np.array(range(len(growth_data)))
                y = np.array([d['count'] for d in growth_data])
                
                if len(y) > 0:
                    slope = np.polyfit(x, y, 1)[0]
                    
                    # Predict next 7 days
                    for i in range(7):
                        predicted_count = slope * (len(growth_data) + i) + y[0]
                        predictions["data_growth_forecast"].append({
                            "day": i + 1,
                            "predicted_count": max(0, int(predicted_count))
                        })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error calculating predictions: {e}")
            return {}
    
    def _get_historical_growth(self, db: Session, vendor_id: Optional[str]) -> List[Dict]:
        """Get historical data growth for predictions."""
        try:
            query = """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM vendor_data
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """
            
            if vendor_id:
                query = query.replace("WHERE", f"WHERE vendor_id = '{vendor_id}' AND")
            
            results = db.execute(text(query)).fetchall()
            return [{"date": row.date.isoformat(), "count": row.count} for row in results]
            
        except Exception as e:
            logger.error(f"Error getting historical growth: {e}")
            return []
    
    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to days."""
        time_range_map = {
            "1d": 1, "7d": 7, "30d": 30, "90d": 90,
            "1y": 365, "2y": 730, "5y": 1825
        }
        return time_range_map.get(time_range, 30)
    
    def mask_sensitive_data(self, data: Dict[str, Any], 
                           masking_level: DataMaskingLevel = DataMaskingLevel.PARTIAL,
                           custom_rules: Optional[Dict[str, DataMaskingRule]] = None) -> Dict[str, Any]:
        """
        Mask sensitive data according to configured rules.
        
        Args:
            data: Data dictionary to mask
            masking_level: Level of masking to apply
            custom_rules: Custom masking rules
            
        Returns:
            Masked data dictionary
        """
        try:
            masked_data = data.copy()
            rules = custom_rules or self.masking_rules
            
            for field_name, rule in rules.items():
                if field_name in masked_data:
                    masked_data[field_name] = self._apply_masking_rule(
                        masked_data[field_name], rule, masking_level
                    )
            
            # Log masking operation
            self._log_audit_event("data_masking", {
                "fields_masked": list(rules.keys()),
                "masking_level": masking_level.value
            })
            
            return masked_data
            
        except Exception as e:
            logger.error(f"Error masking sensitive data: {e}")
            raise
    
    def _apply_masking_rule(self, value: Any, rule: DataMaskingRule, 
                           masking_level: DataMaskingLevel) -> Any:
        """Apply specific masking rule to a value."""
        if not value or masking_level == DataMaskingLevel.NONE:
            return value
        
        if masking_level == DataMaskingLevel.FULL:
            return rule.replacement_char * len(str(value))
        
        elif masking_level == DataMaskingLevel.PARTIAL:
            if rule.field_name == "email":
                return self._mask_email(value)
            elif rule.field_name == "phone":
                return self._mask_phone(value)
            elif rule.field_name == "ssn":
                return "***-**-" + str(value)[-4:]
            elif rule.field_name == "credit_card":
                return "****-****-****-" + str(value)[-4:]
            elif rule.field_name == "address":
                return self._mask_address(value)
            elif rule.field_name == "name":
                return self._mask_name(value)
            else:
                return rule.replacement_char * len(str(value))
        
        return value
    
    def _mask_email(self, email: str) -> str:
        """Mask email address."""
        if "@" not in email:
            return email
        
        username, domain = email.split("@", 1)
        if len(username) <= 2:
            masked_username = username
        else:
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number."""
        phone_str = str(phone).replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
        if len(phone_str) >= 4:
            return "***-***-" + phone_str[-4:]
        return phone
    
    def _mask_address(self, address: str) -> str:
        """Mask address."""
        parts = address.split()
        if len(parts) >= 2:
            return parts[0] + " " + "*" * len(parts[1]) + " " + " ".join(parts[2:])
        return address
    
    def _mask_name(self, name: str) -> str:
        """Mask name."""
        parts = name.split()
        if len(parts) >= 2:
            return parts[0] + " " + parts[1][0] + "*" * (len(parts[1]) - 1)
        return name
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive data using AES-256 encryption.
        
        Args:
            data: Data dictionary to encrypt
            
        Returns:
            Encrypted data dictionary
        """
        try:
            encrypted_data = {}
            
            for key, value in data.items():
                if self._is_sensitive_field(key):
                    encrypted_value = self.cipher.encrypt(str(value).encode())
                    encrypted_data[key] = base64.b64encode(encrypted_value).decode()
                else:
                    encrypted_data[key] = value
            
            # Log encryption operation
            self._log_audit_event("data_encryption", {
                "fields_encrypted": [k for k in data.keys() if self._is_sensitive_field(k)]
            })
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Error encrypting sensitive data: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data dictionary
            
        Returns:
            Decrypted data dictionary
        """
        try:
            decrypted_data = {}
            
            for key, value in encrypted_data.items():
                if self._is_sensitive_field(key) and isinstance(value, str):
                    try:
                        encrypted_bytes = base64.b64decode(value.encode())
                        decrypted_value = self.cipher.decrypt(encrypted_bytes)
                        decrypted_data[key] = decrypted_value.decode()
                    except Exception:
                        # If decryption fails, keep original value
                        decrypted_data[key] = value
                else:
                    decrypted_data[key] = value
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error decrypting sensitive data: {e}")
            raise
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field contains sensitive data."""
        sensitive_fields = {
            "email", "phone", "ssn", "credit_card", "password", "api_key",
            "address", "name", "ip_address", "mac_address", "social_security",
            "driver_license", "passport", "medical_record", "financial_data"
        }
        return field_name.lower() in sensitive_fields
    
    def check_compliance(self, data: Dict[str, Any], 
                        compliance_type: ComplianceType) -> Dict[str, Any]:
        """
        Check data compliance with specified regulations.
        
        Args:
            data: Data to check for compliance
            compliance_type: Type of compliance to check
            
        Returns:
            Compliance check results
        """
        try:
            config = self.compliance_configs.get(compliance_type)
            if not config or not config.enabled:
                return {"compliant": False, "errors": ["Compliance type not enabled"]}
            
            results = {
                "compliant": True,
                "warnings": [],
                "errors": [],
                "recommendations": []
            }
            
            if compliance_type == ComplianceType.GDPR:
                results = self._check_gdpr_compliance(data, config)
            elif compliance_type == ComplianceType.HIPAA:
                results = self._check_hipaa_compliance(data, config)
            elif compliance_type == ComplianceType.CCPA:
                results = self._check_ccpa_compliance(data, config)
            elif compliance_type == ComplianceType.SOX:
                results = self._check_sox_compliance(data, config)
            
            # Log compliance check
            self._log_audit_event("compliance_check", {
                "compliance_type": compliance_type.value,
                "compliant": results["compliant"],
                "error_count": len(results["errors"]),
                "warning_count": len(results["warnings"])
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            raise
    
    def _check_gdpr_compliance(self, data: Dict[str, Any], 
                              config: ComplianceConfig) -> Dict[str, Any]:
        """Check GDPR compliance."""
        results = {
            "compliant": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check for personal data
        personal_data_fields = ["email", "phone", "name", "address", "ip_address"]
        found_personal_data = [field for field in personal_data_fields if field in data]
        
        if found_personal_data:
            if not config.consent_required:
                results["errors"].append("GDPR requires explicit consent for personal data")
                results["compliant"] = False
            
            if not config.encryption_required:
                results["warnings"].append("GDPR recommends encryption for personal data")
            
            results["recommendations"].append("Implement data portability features")
            results["recommendations"].append("Add right to be forgotten functionality")
        
        return results
    
    def _check_hipaa_compliance(self, data: Dict[str, Any], 
                               config: ComplianceConfig) -> Dict[str, Any]:
        """Check HIPAA compliance."""
        results = {
            "compliant": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check for PHI (Protected Health Information)
        phi_fields = ["medical_record", "diagnosis", "treatment", "prescription", "patient_id"]
        found_phi = [field for field in phi_fields if field in data]
        
        if found_phi:
            if not config.encryption_required:
                results["errors"].append("HIPAA requires encryption for PHI")
                results["compliant"] = False
            
            if not config.audit_logging:
                results["errors"].append("HIPAA requires comprehensive audit logging")
                results["compliant"] = False
            
            results["recommendations"].append("Implement access controls for PHI")
            results["recommendations"].append("Add data retention policies")
        
        return results
    
    def _check_ccpa_compliance(self, data: Dict[str, Any], 
                              config: ComplianceConfig) -> Dict[str, Any]:
        """Check CCPA compliance."""
        results = {
            "compliant": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check for personal information
        personal_info_fields = ["email", "phone", "name", "address", "ip_address"]
        found_personal_info = [field for field in personal_info_fields if field in data]
        
        if found_personal_info:
            if not config.consent_required:
                results["warnings"].append("CCPA requires notice of data collection")
            
            results["recommendations"].append("Implement right to know functionality")
            results["recommendations"].append("Add right to delete functionality")
        
        return results
    
    def _check_sox_compliance(self, data: Dict[str, Any], 
                             config: ComplianceConfig) -> Dict[str, Any]:
        """Check SOX compliance."""
        results = {
            "compliant": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check for financial data
        financial_fields = ["financial_data", "accounting_record", "audit_trail"]
        found_financial_data = [field for field in financial_fields if field in data]
        
        if found_financial_data:
            if not config.audit_logging:
                results["errors"].append("SOX requires comprehensive audit trails")
                results["compliant"] = False
            
            if not config.encryption_required:
                results["warnings"].append("SOX recommends encryption for financial data")
            
            results["recommendations"].append("Implement data retention policies")
            results["recommendations"].append("Add access controls for financial data")
        
        return results
    
    def _log_audit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log audit event for compliance and security tracking."""
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "event_data": event_data,
                "user_id": getattr(get_current_user(), 'id', None),
                "session_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
            }
            
            with self._lock:
                self.audit_log.append(audit_entry)
                
                # Keep only last 10,000 audit entries
                if len(self.audit_log) > 10000:
                    self.audit_log = self.audit_log[-10000:]
            
            logger.info(f"Audit event logged: {event_type}")
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    def get_audit_log(self, event_type: Optional[str] = None, 
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get audit log entries with optional filtering.
        
        Args:
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of audit log entries
        """
        try:
            with self._lock:
                filtered_log = self.audit_log.copy()
                
                if event_type:
                    filtered_log = [entry for entry in filtered_log 
                                  if entry.get("event_type") == event_type]
                
                if start_date:
                    filtered_log = [entry for entry in filtered_log 
                                  if datetime.fromisoformat(entry["timestamp"]) >= start_date]
                
                if end_date:
                    filtered_log = [entry for entry in filtered_log 
                                  if datetime.fromisoformat(entry["timestamp"]) <= end_date]
                
                return filtered_log
                
        except Exception as e:
            logger.error(f"Error getting audit log: {e}")
            raise
    
    def export_data(self, data: Dict[str, Any], 
                   export_format: str = "json",
                   include_analytics: bool = True,
                   mask_sensitive: bool = True) -> str:
        """
        Export data in various formats with optional analytics and masking.
        
        Args:
            data: Data to export
            export_format: Export format (json, csv, xml, yaml)
            include_analytics: Include analytics in export
            mask_sensitive: Mask sensitive data in export
            
        Returns:
            Exported data string
        """
        try:
            export_data = data.copy()
            
            # Add analytics if requested
            if include_analytics:
                analytics = self.get_analytics()
                export_data["analytics"] = asdict(analytics)
            
            # Mask sensitive data if requested
            if mask_sensitive:
                export_data = self.mask_sensitive_data(export_data)
            
            # Export in requested format
            if export_format.lower() == "json":
                return json.dumps(export_data, indent=2, default=str)
            elif export_format.lower() == "csv":
                return self._export_to_csv(export_data)
            elif export_format.lower() == "xml":
                return self._export_to_xml(export_data)
            elif export_format.lower() == "yaml":
                return self._export_to_yaml(export_data)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            raise
    
    def _export_to_csv(self, data: Dict[str, Any]) -> str:
        """Export data to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        if data:
            writer.writerow(data.keys())
            writer.writerow(data.values())
        
        return output.getvalue()
    
    def _export_to_xml(self, data: Dict[str, Any]) -> str:
        """Export data to XML format."""
        def dict_to_xml(data_dict, root_name="data"):
            xml_parts = [f"<{root_name}>"]
            
            for key, value in data_dict.items():
                if isinstance(value, dict):
                    xml_parts.append(dict_to_xml(value, key))
                else:
                    xml_parts.append(f"<{key}>{value}</{key}>")
            
            xml_parts.append(f"</{root_name}>")
            return "".join(xml_parts)
        
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{dict_to_xml(data)}'
    
    def _export_to_yaml(self, data: Dict[str, Any]) -> str:
        """Export data to YAML format."""
        import yaml
        
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the service."""
        try:
            with self._lock:
                return {
                    "analytics_cache_size": len(self.audit_log),
                    "masking_rules_count": len(self.masking_rules),
                    "compliance_configs_count": len(self.compliance_configs),
                    "audit_log_entries": len(self.audit_log),
                    "encryption_enabled": self.encryption_key is not None,
                    "service_uptime": time.time() - getattr(self, '_start_time', time.time())
                }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}


# Global instance
data_vendor_api_expansion = DataVendorAPIExpansion() 
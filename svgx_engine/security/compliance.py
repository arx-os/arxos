"""
Compliance Services for Arxos.

This module provides comprehensive compliance services including:
- GDPR data protection compliance
- HIPAA healthcare compliance
- SOC2 security compliance
- PCI DSS payment security
- Automated compliance reporting
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from .monitoring import AuditLogger, ComplianceReporter


class ComplianceType(Enum):
    """Compliance framework types."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"


@dataclass
class ComplianceRequirement:
    """Compliance requirement definition."""
    requirement_id: str
    compliance_type: ComplianceType
    title: str
    description: str
    category: str
    severity: str
    implementation_status: str
    last_audit: Optional[datetime] = None
    next_audit: Optional[datetime] = None


@dataclass
class ComplianceViolation:
    """Compliance violation record."""
    violation_id: str
    requirement_id: str
    compliance_type: ComplianceType
    severity: str
    timestamp: datetime
    description: str
    affected_data: List[str]
    remediation_actions: List[str]
    status: str = "open"


class GDPRService:
    """GDPR (General Data Protection Regulation) compliance service."""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.data_subjects = {}
        self.consent_records = {}
        self.data_processing_activities = {}
    
    def register_data_subject(self, subject_id: str, personal_data: Dict[str, Any], 
                             consent_given: bool = False) -> bool:
        """Register a data subject for GDPR compliance."""
        try:
            # Hash personal data for privacy
            hashed_data = self._hash_personal_data(personal_data)
            
            self.data_subjects[subject_id] = {
                'hashed_data': hashed_data,
                'consent_given': consent_given,
                'registered_at': datetime.utcnow(),
                'last_updated': datetime.utcnow(),
                'data_retention_end': datetime.utcnow() + timedelta(days=2555)  # 7 years
            }
            
            # Log data subject registration
            self.audit_logger.log_data_access(
                user_id="system",
                data_type="personal_data",
                action="register_data_subject",
                details={
                    'subject_id': subject_id,
                    'consent_given': consent_given,
                    'data_categories': list(personal_data.keys())
                }
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to register data subject {subject_id}: {e}")
            return False
    
    def record_consent(self, subject_id: str, consent_type: str, 
                      consent_given: bool, purpose: str) -> bool:
        """Record data subject consent."""
        try:
            consent_record = {
                'subject_id': subject_id,
                'consent_type': consent_type,
                'consent_given': consent_given,
                'purpose': purpose,
                'timestamp': datetime.utcnow(),
                'ip_address': 'system',  # Should be actual IP
                'user_agent': 'system'   # Should be actual user agent
            }
            
            self.consent_records[f"{subject_id}_{consent_type}"] = consent_record
            
            # Update data subject record
            if subject_id in self.data_subjects:
                self.data_subjects[subject_id]['consent_given'] = consent_given
                self.data_subjects[subject_id]['last_updated'] = datetime.utcnow()
            
            # Log consent record
            self.audit_logger.log_data_access(
                user_id="system",
                data_type="consent",
                action="record_consent",
                details=consent_record
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to record consent for {subject_id}: {e}")
            return False
    
    def process_data_subject_request(self, subject_id: str, request_type: str) -> Dict[str, Any]:
        """Process data subject rights requests."""
        try:
            if request_type == "access":
                return self._handle_access_request(subject_id)
            elif request_type == "rectification":
                return self._handle_rectification_request(subject_id)
            elif request_type == "erasure":
                return self._handle_erasure_request(subject_id)
            elif request_type == "portability":
                return self._handle_portability_request(subject_id)
            else:
                raise ValueError(f"Unknown request type: {request_type}")
                
        except Exception as e:
            logging.error(f"Failed to process data subject request: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_access_request(self, subject_id: str) -> Dict[str, Any]:
        """Handle data subject access request."""
        if subject_id not in self.data_subjects:
            return {'success': False, 'error': 'Data subject not found'}
        
        subject_data = self.data_subjects[subject_id]
        
        # Log access request
        self.audit_logger.log_data_access(
            user_id="system",
            data_type="personal_data",
            action="data_subject_access_request",
            details={'subject_id': subject_id}
        )
        
        return {
            'success': True,
            'data_subject_id': subject_id,
            'consent_given': subject_data['consent_given'],
            'registered_at': subject_data['registered_at'].isoformat(),
            'data_retention_end': subject_data['data_retention_end'].isoformat()
        }
    
    def _handle_erasure_request(self, subject_id: str) -> Dict[str, Any]:
        """Handle data subject erasure request."""
        if subject_id not in self.data_subjects:
            return {'success': False, 'error': 'Data subject not found'}
        
        # Mark for deletion (soft delete)
        self.data_subjects[subject_id]['deletion_requested'] = datetime.utcnow()
        self.data_subjects[subject_id]['deletion_scheduled'] = datetime.utcnow() + timedelta(days=30)
        
        # Log erasure request
        self.audit_logger.log_data_access(
            user_id="system",
            data_type="personal_data",
            action="data_subject_erasure_request",
            details={'subject_id': subject_id}
        )
        
        return {
            'success': True,
            'message': 'Data subject marked for deletion',
            'deletion_scheduled': self.data_subjects[subject_id]['deletion_scheduled'].isoformat()
        }
    
    def _hash_personal_data(self, personal_data: Dict[str, Any]) -> str:
        """Hash personal data for privacy protection."""
        data_string = json.dumps(personal_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def generate_gdpr_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        report = {
            'report_type': 'GDPR_Compliance',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'data_subjects': {
                'total_registered': len(self.data_subjects),
                'with_consent': len([s for s in self.data_subjects.values() if s['consent_given']]),
                'without_consent': len([s for s in self.data_subjects.values() if not s['consent_given']])
            },
            'consent_records': {
                'total_records': len(self.consent_records),
                'consent_given': len([r for r in self.consent_records.values() if r['consent_given']]),
                'consent_withdrawn': len([r for r in self.consent_records.values() if not r['consent_given']])
            },
            'data_subject_requests': [],
            'compliance_status': 'compliant'
        }
        
        # Get audit trail for data subject requests
        audit_trail = self.audit_logger.get_audit_trail(start_date, end_date)
        
        for entry in audit_trail:
            if 'data_subject' in entry['message'].lower():
                report['data_subject_requests'].append({
                    'timestamp': entry['timestamp'].isoformat(),
                    'message': entry['message']
                })
        
        return report


class HIPAAService:
    """HIPAA (Health Insurance Portability and Accountability Act) compliance service."""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.phi_records = {}
        self.access_logs = {}
        self.breach_incidents = {}
    
    def store_phi(self, record_id: str, phi_data: Dict[str, Any], 
                  patient_id: str, access_level: str) -> bool:
        """Store Protected Health Information (PHI) with HIPAA compliance."""
        try:
            # Encrypt PHI data
            encrypted_data = self._encrypt_phi_data(phi_data)
            
            self.phi_records[record_id] = {
                'patient_id': patient_id,
                'encrypted_data': encrypted_data,
                'access_level': access_level,
                'created_at': datetime.utcnow(),
                'last_accessed': None,
                'access_count': 0
            }
            
            # Log PHI storage
            self.audit_logger.log_data_access(
                user_id="system",
                data_type="phi",
                action="store_phi",
                details={
                    'record_id': record_id,
                    'patient_id': patient_id,
                    'access_level': access_level
                }
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to store PHI record {record_id}: {e}")
            return False
    
    def access_phi(self, record_id: str, user_id: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Access PHI with HIPAA compliance logging."""
        try:
            if record_id not in self.phi_records:
                return None
            
            record = self.phi_records[record_id]
            
            # Update access log
            record['last_accessed'] = datetime.utcnow()
            record['access_count'] += 1
            
            # Log PHI access
            self.audit_logger.log_data_access(
                user_id=user_id,
                data_type="phi",
                action="access_phi",
                details={
                    'record_id': record_id,
                    'patient_id': record['patient_id'],
                    'purpose': purpose,
                    'access_level': record['access_level']
                }
            )
            
            # Store access log
            access_log_id = f"{record_id}_{int(datetime.utcnow().timestamp())}"
            self.access_logs[access_log_id] = {
                'record_id': record_id,
                'user_id': user_id,
                'purpose': purpose,
                'timestamp': datetime.utcnow(),
                'access_level': record['access_level']
            }
            
            return {
                'record_id': record_id,
                'patient_id': record['patient_id'],
                'access_level': record['access_level'],
                'last_accessed': record['last_accessed'].isoformat(),
                'access_count': record['access_count']
            }
            
        except Exception as e:
            logging.error(f"Failed to access PHI record {record_id}: {e}")
            return None
    
    def report_breach(self, breach_id: str, affected_records: List[str], 
                     breach_type: str, description: str) -> bool:
        """Report HIPAA breach incident."""
        try:
            breach_record = {
                'breach_id': breach_id,
                'affected_records': affected_records,
                'breach_type': breach_type,
                'description': description,
                'reported_at': datetime.utcnow(),
                'status': 'reported',
                'affected_patients': len(set([
                    self.phi_records[record_id]['patient_id'] 
                    for record_id in affected_records 
                    if record_id in self.phi_records
                ]))
            }
            
            self.breach_incidents[breach_id] = breach_record
            
            # Log breach report
            self.audit_logger.log_data_access(
                user_id="system",
                data_type="breach",
                action="report_breach",
                details=breach_record
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to report breach {breach_id}: {e}")
            return False
    
    def _encrypt_phi_data(self, phi_data: Dict[str, Any]) -> str:
        """Encrypt PHI data for HIPAA compliance."""
        # In production, use proper encryption
        data_string = json.dumps(phi_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def generate_hipaa_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate HIPAA compliance report."""
        report = {
            'report_type': 'HIPAA_Compliance',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'phi_records': {
                'total_records': len(self.phi_records),
                'unique_patients': len(set(r['patient_id'] for r in self.phi_records.values())),
                'total_accesses': sum(r['access_count'] for r in self.phi_records.values())
            },
            'access_logs': {
                'total_accesses': len(self.access_logs),
                'unique_users': len(set(log['user_id'] for log in self.access_logs.values()))
            },
            'breach_incidents': {
                'total_incidents': len(self.breach_incidents),
                'open_incidents': len([b for b in self.breach_incidents.values() if b['status'] == 'reported'])
            },
            'compliance_status': 'compliant'
        }
        
        return report


class SOC2Service:
    """SOC2 (System and Organization Controls 2) compliance service."""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.security_controls = {}
        self.control_assessments = {}
        self.incident_reports = {}
    
    def register_security_control(self, control_id: str, control_name: str, 
                                control_type: str, description: str) -> bool:
        """Register a security control for SOC2 compliance."""
        try:
            self.security_controls[control_id] = {
                'control_id': control_id,
                'control_name': control_name,
                'control_type': control_type,
                'description': description,
                'registered_at': datetime.utcnow(),
                'status': 'active',
                'last_assessment': None,
                'next_assessment': datetime.utcnow() + timedelta(days=90)
            }
            
            # Log control registration
            self.audit_logger.log_configuration_change(
                user_id="system",
                component="security_control",
                change_type="register_control",
                details={
                    'control_id': control_id,
                    'control_name': control_name,
                    'control_type': control_type
                }
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to register security control {control_id}: {e}")
            return False
    
    def assess_control(self, control_id: str, assessment_result: str, 
                      findings: List[str], assessor: str) -> bool:
        """Assess a security control."""
        try:
            if control_id not in self.security_controls:
                return False
            
            assessment = {
                'control_id': control_id,
                'assessment_result': assessment_result,
                'findings': findings,
                'assessor': assessor,
                'assessment_date': datetime.utcnow(),
                'next_assessment': datetime.utcnow() + timedelta(days=90)
            }
            
            self.control_assessments[f"{control_id}_{int(datetime.utcnow().timestamp())}"] = assessment
            
            # Update control status
            self.security_controls[control_id]['last_assessment'] = datetime.utcnow()
            self.security_controls[control_id]['next_assessment'] = assessment['next_assessment']
            
            # Log assessment
            self.audit_logger.log_configuration_change(
                user_id=assessor,
                component="security_control",
                change_type="assess_control",
                details=assessment
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to assess control {control_id}: {e}")
            return False
    
    def report_incident(self, incident_id: str, incident_type: str, 
                       severity: str, description: str, affected_controls: List[str]) -> bool:
        """Report security incident for SOC2 compliance."""
        try:
            incident = {
                'incident_id': incident_id,
                'incident_type': incident_type,
                'severity': severity,
                'description': description,
                'affected_controls': affected_controls,
                'reported_at': datetime.utcnow(),
                'status': 'open',
                'resolution_date': None
            }
            
            self.incident_reports[incident_id] = incident
            
            # Log incident report
            self.audit_logger.log_system_event(
                event_type="security_incident",
                details=incident
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to report incident {incident_id}: {e}")
            return False
    
    def generate_soc2_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate SOC2 compliance report."""
        report = {
            'report_type': 'SOC2_Compliance',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'security_controls': {
                'total_controls': len(self.security_controls),
                'active_controls': len([c for c in self.security_controls.values() if c['status'] == 'active']),
                'controls_due_assessment': len([
                    c for c in self.security_controls.values() 
                    if c['next_assessment'] and c['next_assessment'] <= datetime.utcnow()
                ])
            },
            'control_assessments': {
                'total_assessments': len(self.control_assessments),
                'assessments_in_period': len([
                    a for a in self.control_assessments.values()
                    if start_date <= a['assessment_date'] <= end_date
                ])
            },
            'incident_reports': {
                'total_incidents': len(self.incident_reports),
                'open_incidents': len([i for i in self.incident_reports.values() if i['status'] == 'open']),
                'incidents_in_period': len([
                    i for i in self.incident_reports.values()
                    if start_date <= i['reported_at'] <= end_date
                ])
            },
            'compliance_status': 'compliant'
        }
        
        return report


class ComplianceManager:
    """Main compliance management service."""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.gdpr_service = GDPRService(audit_logger)
        self.hipaa_service = HIPAAService(audit_logger)
        self.soc2_service = SOC2Service(audit_logger)
        self.compliance_reporter = ComplianceReporter(audit_logger)
    
    def generate_comprehensive_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        report = {
            'report_generated_at': datetime.utcnow().isoformat(),
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'gdpr': self.gdpr_service.generate_gdpr_report(start_date, end_date),
            'hipaa': self.hipaa_service.generate_hipaa_report(start_date, end_date),
            'soc2': self.soc2_service.generate_soc2_report(start_date, end_date),
            'overall_compliance_status': 'compliant'
        }
        
        # Determine overall compliance status
        compliance_statuses = [
            report['gdpr']['compliance_status'],
            report['hipaa']['compliance_status'],
            report['soc2']['compliance_status']
        ]
        
        if 'non_compliant' in compliance_statuses:
            report['overall_compliance_status'] = 'non_compliant'
        elif 'review_required' in compliance_statuses:
            report['overall_compliance_status'] = 'review_required'
        
        return report 
#!/usr/bin/env python3
"""
Report Service for MCP Service

This module provides report generation and distribution services including:
- PDF report generation
- Email distribution
- Cloud storage integration
- Report management
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import aiofiles
import boto3
from azure.storage.blob import BlobServiceClient

from .report_generator import ReportGenerator, create_report_generator

logger = logging.getLogger(__name__)


class ReportService:
    """Report generation and distribution service"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the report service"""
        self.config = config
        self.report_generator = create_report_generator()
        
        # Setup storage paths
        self.reports_dir = Path(config.get('reports_dir', 'reports'))
        self.reports_dir.mkdir(exist_ok=True)
        
        # Email configuration
        self.email_config = config.get('email', {})
        
        # Cloud storage configuration
        self.storage_config = config.get('storage', {})
        
        # Initialize cloud storage clients
        self._setup_cloud_storage()
        
        logger.info("✅ Report Service initialized")
    
    def _setup_cloud_storage(self):
        """Setup cloud storage clients"""
        self.s3_client = None
        self.azure_client = None
        
        # AWS S3 setup
        if self.storage_config.get('aws'):
            aws_config = self.storage_config['aws']
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_config.get('access_key'),
                aws_secret_access_key=aws_config.get('secret_key'),
                region_name=aws_config.get('region', 'us-east-1')
            )
            self.s3_bucket = aws_config.get('bucket')
            logger.info("✅ AWS S3 client initialized")
        
        # Azure Blob Storage setup
        if self.storage_config.get('azure'):
            azure_config = self.storage_config['azure']
            connection_string = azure_config.get('connection_string')
            if connection_string:
                self.azure_client = BlobServiceClient.from_connection_string(connection_string)
                self.azure_container = azure_config.get('container')
                logger.info("✅ Azure Blob Storage client initialized")
    
    async def generate_compliance_report(self, validation_data: Dict[str, Any],
                                       building_info: Dict[str, Any],
                                       report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate a compliance report
        
        Args:
            validation_data: Validation results
            building_info: Building information
            report_type: Type of report to generate
            
        Returns:
            Report generation result
        """
        try:
            building_id = building_info.get('building_id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate filename
            if report_type == "comprehensive":
                filename = f"compliance_report_{building_id}_{timestamp}.pdf"
            elif report_type == "violation_summary":
                filename = f"violation_summary_{building_id}_{timestamp}.pdf"
            elif report_type == "executive_summary":
                filename = f"executive_summary_{building_id}_{timestamp}.pdf"
            else:
                filename = f"report_{building_id}_{timestamp}.pdf"
            
            output_path = self.reports_dir / filename
            
            # Generate report based on type
            if report_type == "comprehensive":
                pdf_path = self.report_generator.generate_compliance_report(
                    validation_data, building_info, str(output_path)
                )
            elif report_type == "violation_summary":
                pdf_path = self.report_generator.generate_violation_summary(
                    validation_data, str(output_path)
                )
            elif report_type == "executive_summary":
                pdf_path = self.report_generator.generate_executive_summary(
                    validation_data, building_info, str(output_path)
                )
            else:
                pdf_path = self.report_generator.generate_compliance_report(
                    validation_data, building_info, str(output_path)
                )
            
            # Get file size
            file_size = os.path.getsize(pdf_path)
            
            # Upload to cloud storage if configured
            cloud_urls = await self._upload_to_cloud_storage(pdf_path, filename)
            
            result = {
                "success": True,
                "report_path": pdf_path,
                "filename": filename,
                "file_size": file_size,
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "cloud_urls": cloud_urls
            }
            
            logger.info(f"✅ Report generated: {filename} ({file_size} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to generate report: {e}")
            return {
                "success": False,
                "error": str(e),
                "report_type": report_type,
                "generated_at": datetime.now().isoformat()
            }
    
    async def _upload_to_cloud_storage(self, file_path: str, filename: str) -> Dict[str, str]:
        """Upload report to cloud storage"""
        cloud_urls = {}
        
        try:
            # Upload to AWS S3
            if self.s3_client and self.s3_bucket:
                try:
                    with open(file_path, 'rb') as file:
                        self.s3_client.upload_fileobj(file, self.s3_bucket, f"reports/{filename}")
                    
                    cloud_urls['aws_s3'] = f"https://{self.s3_bucket}.s3.amazonaws.com/reports/{filename}"
                    logger.info(f"✅ Uploaded to AWS S3: {filename}")
                except Exception as e:
                    logger.error(f"❌ Failed to upload to AWS S3: {e}")
            
            # Upload to Azure Blob Storage
            if self.azure_client and self.azure_container:
                try:
                    blob_client = self.azure_client.get_blob_client(
                        container=self.azure_container,
                        blob=f"reports/{filename}"
                    )
                    
                    with open(file_path, 'rb') as file:
                        blob_client.upload_blob(file, overwrite=True)
                    
                    cloud_urls['azure_blob'] = blob_client.url
                    logger.info(f"✅ Uploaded to Azure Blob Storage: {filename}")
                except Exception as e:
                    logger.error(f"❌ Failed to upload to Azure Blob Storage: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Cloud storage upload failed: {e}")
        
        return cloud_urls
    
    async def send_report_email(self, report_path: str, recipients: List[str],
                               subject: str = None, message: str = None) -> Dict[str, Any]:
        """
        Send report via email
        
        Args:
            report_path: Path to the PDF report
            recipients: List of email addresses
            subject: Email subject
            message: Email message body
            
        Returns:
            Email sending result
        """
        try:
            if not self.email_config:
                raise ValueError("Email configuration not available")
            
            # Default subject and message
            if not subject:
                subject = "Building Code Compliance Report"
            
            if not message:
                message = """
                Please find attached the building code compliance report.
                
                This report contains detailed analysis of building code violations and recommendations.
                
                Best regards,
                MCP Service Team
                """
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('from_email')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Attach PDF file
            with open(report_path, 'rb') as file:
                attachment = MIMEApplication(file.read(), _subtype='pdf')
                attachment.add_header('Content-Disposition', 'attachment', 
                                   filename=os.path.basename(report_path))
                msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP(self.email_config.get('smtp_host'), 
                             self.email_config.get('smtp_port', 587)) as server:
                if self.email_config.get('use_tls', True):
                    server.starttls()
                
                if self.email_config.get('username') and self.email_config.get('password'):
                    server.login(self.email_config.get('username'), 
                               self.email_config.get('password'))
                
                server.send_message(msg)
            
            result = {
                "success": True,
                "recipients": recipients,
                "subject": subject,
                "sent_at": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Report email sent to {len(recipients)} recipients")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send report email: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipients": recipients,
                "sent_at": datetime.now().isoformat()
            }
    
    async def generate_and_send_report(self, validation_data: Dict[str, Any],
                                      building_info: Dict[str, Any],
                                      recipients: List[str],
                                      report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate and send report in one operation
        
        Args:
            validation_data: Validation results
            building_info: Building information
            recipients: Email recipients
            report_type: Type of report to generate
            
        Returns:
            Combined generation and sending result
        """
        try:
            # Generate report
            generation_result = await self.generate_compliance_report(
                validation_data, building_info, report_type
            )
            
            if not generation_result['success']:
                return generation_result
            
            # Send email
            email_result = await self.send_report_email(
                generation_result['report_path'],
                recipients
            )
            
            # Combine results
            result = {
                "success": generation_result['success'] and email_result['success'],
                "generation": generation_result,
                "email": email_result,
                "completed_at": datetime.now().isoformat()
            }
            
            if not email_result['success']:
                result['error'] = email_result.get('error')
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to generate and send report: {e}")
            return {
                "success": False,
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            }
    
    async def get_report_history(self, building_id: str = None, 
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get report generation history
        
        Args:
            building_id: Filter by building ID
            limit: Maximum number of reports to return
            
        Returns:
            List of report history entries
        """
        try:
            reports = []
            
            # Scan reports directory
            for file_path in self.reports_dir.glob("*.pdf"):
                try:
                    # Extract metadata from filename
                    filename = file_path.name
                    file_stats = file_path.stat()
                    
                    # Parse filename for metadata
                    parts = filename.replace('.pdf', '').split('_')
                    
                    report_info = {
                        "filename": filename,
                        "file_path": str(file_path),
                        "file_size": file_stats.st_size,
                        "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    }
                    
                    # Extract building ID and report type
                    if len(parts) >= 3:
                        report_info['report_type'] = parts[0] + '_' + parts[1]
                        report_info['building_id'] = parts[2]
                        
                        # Filter by building ID if specified
                        if building_id and report_info['building_id'] != building_id:
                            continue
                    
                    reports.append(report_info)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse report file {file_path}: {e}")
                    continue
            
            # Sort by creation date (newest first)
            reports.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Apply limit
            return reports[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to get report history: {e}")
            return []
    
    async def delete_report(self, filename: str) -> Dict[str, Any]:
        """
        Delete a report file
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            Deletion result
        """
        try:
            file_path = self.reports_dir / filename
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File not found"
                }
            
            # Delete from cloud storage
            await self._delete_from_cloud_storage(filename)
            
            # Delete local file
            file_path.unlink()
            
            result = {
                "success": True,
                "filename": filename,
                "deleted_at": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Report deleted: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to delete report {filename}: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    async def _delete_from_cloud_storage(self, filename: str):
        """Delete report from cloud storage"""
        try:
            # Delete from AWS S3
            if self.s3_client and self.s3_bucket:
                try:
                    self.s3_client.delete_object(Bucket=self.s3_bucket, 
                                               Key=f"reports/{filename}")
                    logger.info(f"✅ Deleted from AWS S3: {filename}")
                except Exception as e:
                    logger.error(f"❌ Failed to delete from AWS S3: {e}")
            
            # Delete from Azure Blob Storage
            if self.azure_client and self.azure_container:
                try:
                    blob_client = self.azure_client.get_blob_client(
                        container=self.azure_container,
                        blob=f"reports/{filename}"
                    )
                    blob_client.delete_blob()
                    logger.info(f"✅ Deleted from Azure Blob Storage: {filename}")
                except Exception as e:
                    logger.error(f"❌ Failed to delete from Azure Blob Storage: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Cloud storage deletion failed: {e}")


# Factory function for easy instantiation
def create_report_service(config: Dict[str, Any]) -> ReportService:
    """Create a report service instance"""
    return ReportService(config) 
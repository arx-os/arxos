"""
Logbook to Doc Generator Service

Automated utility that converts logbook entries into structured documentation
including changelogs, contributor summaries, and system evolution reports
with multiple output formats (Markdown, PDF, JSON).
"""

import json
import sqlite3
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import hashlib
from contextlib import contextmanager

from structlog import get_logger

logger = get_logger()


class LogEntryType(Enum):
    """Log entry type enumeration."""
    COMMIT = "commit"
    SYSTEM_LOG = "system_log"
    USER_ACTIVITY = "user_activity"
    ERROR = "error"
    PERFORMANCE = "performance"
    OBJECT_CHANGE = "object_change"
    API_CALL = "api_call"


class LogSeverity(Enum):
    """Log severity enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DocFormat(Enum):
    """Documentation format enumeration."""
    MARKDOWN = "markdown"
    PDF = "pdf"
    JSON = "json"
    HTML = "html"


@dataclass
class LogEntry:
    """Log entry data structure."""
    entry_id: str
    timestamp: datetime
    entry_type: LogEntryType
    severity: LogSeverity
    message: str
    author: Optional[str]
    commit_hash: Optional[str]
    object_id: Optional[str]
    metadata: Dict[str, Any]
    source: str
    created_at: datetime


@dataclass
class ContributorSummary:
    """Contributor summary data structure."""
    contributor_id: str
    contributor_name: str
    total_commits: int
    total_changes: int
    activity_period: Tuple[datetime, datetime]
    most_active_day: datetime
    commit_frequency: float
    impact_score: float
    recent_activities: List[Dict[str, Any]]
    top_contributions: List[str]


@dataclass
class ChangelogEntry:
    """Changelog entry data structure."""
    version: str
    release_date: datetime
    changes: List[Dict[str, Any]]
    contributors: List[str]
    impact_summary: str
    breaking_changes: List[str]
    new_features: List[str]
    bug_fixes: List[str]
    improvements: List[str]


@dataclass
class SystemEvolutionReport:
    """System evolution report data structure."""
    period_start: datetime
    period_end: datetime
    total_changes: int
    active_contributors: int
    system_growth: Dict[str, Any]
    major_events: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    architecture_changes: List[str]
    technology_updates: List[str]


@dataclass
class GeneratedDocumentation:
    """Generated documentation data structure."""
    document_id: str
    title: str
    format: DocFormat
    content: str
    metadata: Dict[str, Any]
    generated_at: datetime
    processing_time: float
    entry_count: int


class LogbookDocGenerator:
    """
    Logbook to Doc Generator service for automated documentation creation.
    
    Provides comprehensive log processing, documentation generation,
    and multi-format output capabilities.
    """
    
    def __init__(self, db_path: str = "logbook_docs.db"):
        self.db_path = db_path
        self._initialize_database()
        self._load_sample_data()
    
    def _initialize_database(self):
        """Initialize SQLite database for logbook documentation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Log entries table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS log_entries (
                        entry_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        entry_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        author TEXT,
                        commit_hash TEXT,
                        object_id TEXT,
                        metadata TEXT,
                        source TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Generated documentation table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS generated_docs (
                        document_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        format TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        generated_at TEXT NOT NULL,
                        processing_time REAL,
                        entry_count INTEGER
                    )
                """)
                
                # Templates table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS doc_templates (
                        template_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        format TEXT NOT NULL,
                        template_content TEXT NOT NULL,
                        variables TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_timestamp ON log_entries (timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_type ON log_entries (entry_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_author ON log_entries (author)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_commit ON log_entries (commit_hash)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_object ON log_entries (object_id)")
                
                conn.commit()
            logger.info("Logbook Doc Generator database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _load_sample_data(self):
        """Load sample logbook data for testing and demonstration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if data already exists
                cursor = conn.execute("SELECT COUNT(*) FROM log_entries")
                if cursor.fetchone()[0] > 0:
                    return  # Data already loaded
                
                # Sample log entries
                sample_entries = []
                entry_types = [LogEntryType.COMMIT, LogEntryType.SYSTEM_LOG, 
                             LogEntryType.USER_ACTIVITY, LogEntryType.ERROR]
                severities = [LogSeverity.INFO, LogSeverity.WARNING, 
                            LogSeverity.ERROR, LogSeverity.DEBUG]
                authors = ["john_doe", "jane_smith", "mike_wilson", "sarah_johnson"]
                
                for i in range(1000):  # Create 1000 sample log entries
                    entry_id = f"log_{i+1:04d}"
                    entry_type = entry_types[i % len(entry_types)]
                    severity = severities[i % len(severities)]
                    author = authors[i % len(authors)]
                    
                    # Generate sample messages based on type
                    if entry_type == LogEntryType.COMMIT:
                        message = f"Add feature: {['user authentication', 'data export', 'API integration', 'UI improvements'][i % 4]}"
                        commit_hash = f"commit_{hash(f'commit_{i}') % 1000000:06d}"
                        object_id = None
                    elif entry_type == LogEntryType.SYSTEM_LOG:
                        message = f"System {['startup', 'shutdown', 'backup', 'maintenance'][i % 4]} completed"
                        commit_hash = None
                        object_id = None
                    elif entry_type == LogEntryType.USER_ACTIVITY:
                        message = f"User {author} {['logged in', 'exported data', 'created object', 'updated settings'][i % 4]}"
                        commit_hash = None
                        object_id = f"obj_{i % 100:04d}"
                    else:  # ERROR
                        message = f"Error: {['connection timeout', 'validation failed', 'permission denied', 'resource not found'][i % 4]}"
                        commit_hash = None
                        object_id = None
                    
                    timestamp = datetime.now() - timedelta(days=i, hours=i % 24)
                    metadata = {
                        "source_file": f"file_{i % 10}.py",
                        "line_number": (i % 100) + 1,
                        "session_id": f"session_{i % 50:03d}",
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "ip_address": f"192.168.1.{i % 255}"
                    }
                    
                    sample_entries.append((
                        entry_id,
                        timestamp.isoformat(),
                        entry_type.value,
                        severity.value,
                        message,
                        author,
                        commit_hash,
                        object_id,
                        json.dumps(metadata),
                        "sample_source",
                        timestamp.isoformat()
                    ))
                
                # Insert sample entries
                conn.executemany("""
                    INSERT INTO log_entries 
                    (entry_id, timestamp, entry_type, severity, message, author,
                     commit_hash, object_id, metadata, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, sample_entries)
                
                conn.commit()
                logger.info(f"Loaded {len(sample_entries)} sample log entries")
        except Exception as e:
            logger.error(f"Failed to load sample data: {e}")
    
    def process_log_entries(self, 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          entry_types: Optional[List[LogEntryType]] = None,
                          authors: Optional[List[str]] = None) -> List[LogEntry]:
        """
        Process and retrieve log entries with filtering.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            entry_types: Filter by entry types
            authors: Filter by authors
            
        Returns:
            List of processed log entries
        """
        try:
            # Build query with filters
            query = "SELECT * FROM log_entries WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            if entry_types:
                placeholders = ','.join(['?' for _ in entry_types])
                query += f" AND entry_type IN ({placeholders})"
                params.extend([entry_type.value for entry_type in entry_types])
            
            if authors:
                placeholders = ','.join(['?' for _ in authors])
                query += f" AND author IN ({placeholders})"
                params.extend(authors)
            
            query += " ORDER BY timestamp DESC"
            
            # Execute query
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
            
            # Convert rows to LogEntry objects
            entries = []
            for row in rows:
                entry = LogEntry(
                    entry_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    entry_type=LogEntryType(row[2]),
                    severity=LogSeverity(row[3]),
                    message=row[4],
                    author=row[5],
                    commit_hash=row[6],
                    object_id=row[7],
                    metadata=json.loads(row[8]) if row[8] else {},
                    source=row[9],
                    created_at=datetime.fromisoformat(row[10])
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Process log entries failed: {e}")
            raise
    
    def generate_changelog(self, 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          version: str = "1.0.0") -> ChangelogEntry:
        """
        Generate changelog from log entries.
        
        Args:
            start_date: Start date for changelog
            end_date: End date for changelog
            version: Version number for the changelog
            
        Returns:
            ChangelogEntry with structured changelog data
        """
        try:
            # Get commit entries for the period
            entries = self.process_log_entries(
                start_date=start_date,
                end_date=end_date,
                entry_types=[LogEntryType.COMMIT]
            )
            
            # Categorize changes
            breaking_changes = []
            new_features = []
            bug_fixes = []
            improvements = []
            
            contributors = set()
            
            for entry in entries:
                if entry.author:
                    contributors.add(entry.author)
                
                # Categorize based on message content
                message_lower = entry.message.lower()
                
                if any(word in message_lower for word in ['breaking', 'deprecate', 'remove']):
                    breaking_changes.append({
                        "message": entry.message,
                        "author": entry.author,
                        "timestamp": entry.timestamp,
                        "commit_hash": entry.commit_hash
                    })
                elif any(word in message_lower for word in ['add', 'new', 'feature', 'implement']):
                    new_features.append({
                        "message": entry.message,
                        "author": entry.author,
                        "timestamp": entry.timestamp,
                        "commit_hash": entry.commit_hash
                    })
                elif any(word in message_lower for word in ['fix', 'bug', 'issue', 'resolve']):
                    bug_fixes.append({
                        "message": entry.message,
                        "author": entry.author,
                        "timestamp": entry.timestamp,
                        "commit_hash": entry.commit_hash
                    })
                else:
                    improvements.append({
                        "message": entry.message,
                        "author": entry.author,
                        "timestamp": entry.timestamp,
                        "commit_hash": entry.commit_hash
                    })
            
            # Create impact summary
            total_changes = len(breaking_changes) + len(new_features) + len(bug_fixes) + len(improvements)
            impact_summary = f"Version {version} includes {total_changes} changes: {len(new_features)} new features, {len(bug_fixes)} bug fixes, {len(improvements)} improvements"
            
            if breaking_changes:
                impact_summary += f", {len(breaking_changes)} breaking changes"
            
            return ChangelogEntry(
                version=version,
                release_date=end_date or datetime.now(),
                changes=entries,
                contributors=list(contributors),
                impact_summary=impact_summary,
                breaking_changes=breaking_changes,
                new_features=new_features,
                bug_fixes=bug_fixes,
                improvements=improvements
            )
            
        except Exception as e:
            logger.error(f"Generate changelog failed: {e}")
            raise
    
    def generate_contributor_summary(self, 
                                   contributor_id: str,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> ContributorSummary:
        """
        Generate contributor summary from log entries.
        
        Args:
            contributor_id: Contributor ID to analyze
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            ContributorSummary with contributor analysis
        """
        try:
            # Get entries for the contributor
            entries = self.process_log_entries(
                start_date=start_date,
                end_date=end_date,
                authors=[contributor_id]
            )
            
            if not entries:
                raise ValueError(f"No entries found for contributor: {contributor_id}")
            
            # Calculate metrics
            total_commits = len([e for e in entries if e.entry_type == LogEntryType.COMMIT])
            total_changes = len(entries)
            
            # Calculate activity period
            timestamps = [e.timestamp for e in entries]
            activity_start = min(timestamps)
            activity_end = max(timestamps)
            
            # Find most active day
            day_counts = {}
            for entry in entries:
                day = entry.timestamp.date()
                day_counts[day] = day_counts.get(day, 0) + 1
            
            most_active_day = max(day_counts.items(), key=lambda x: x[1])[0]
            most_active_datetime = datetime.combine(most_active_day, datetime.min.time())
            
            # Calculate commit frequency
            days_active = (activity_end - activity_start).days + 1
            commit_frequency = total_commits / days_active if days_active > 0 else 0
            
            # Calculate impact score (based on severity and type)
            impact_score = 0
            for entry in entries:
                if entry.severity == LogSeverity.CRITICAL:
                    impact_score += 10
                elif entry.severity == LogSeverity.ERROR:
                    impact_score += 5
                elif entry.severity == LogSeverity.WARNING:
                    impact_score += 2
                else:
                    impact_score += 1
            
            # Get recent activities
            recent_activities = []
            for entry in entries[:10]:  # Last 10 activities
                recent_activities.append({
                    "timestamp": entry.timestamp,
                    "message": entry.message,
                    "type": entry.entry_type.value,
                    "severity": entry.severity.value
                })
            
            # Get top contributions
            top_contributions = []
            for entry in entries:
                if entry.entry_type == LogEntryType.COMMIT and entry.message:
                    top_contributions.append(entry.message)
                    if len(top_contributions) >= 5:
                        break
            
            return ContributorSummary(
                contributor_id=contributor_id,
                contributor_name=contributor_id,  # Could be enhanced with user lookup
                total_commits=total_commits,
                total_changes=total_changes,
                activity_period=(activity_start, activity_end),
                most_active_day=most_active_datetime,
                commit_frequency=commit_frequency,
                impact_score=impact_score,
                recent_activities=recent_activities,
                top_contributions=top_contributions
            )
            
        except Exception as e:
            logger.error(f"Generate contributor summary failed: {e}")
            raise
    
    def generate_system_evolution_report(self,
                                       start_date: Optional[datetime] = None,
                                       end_date: Optional[datetime] = None) -> SystemEvolutionReport:
        """
        Generate system evolution report from log entries.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            SystemEvolutionReport with system evolution analysis
        """
        try:
            # Get all entries for the period
            entries = self.process_log_entries(
                start_date=start_date,
                end_date=end_date
            )
            
            if not entries:
                raise ValueError("No entries found for the specified period")
            
            # Calculate basic metrics
            total_changes = len(entries)
            contributors = set()
            for entry in entries:
                if entry.author:
                    contributors.add(entry.author)
            
            active_contributors = len(contributors)
            
            # Calculate system growth
            timestamps = [e.timestamp for e in entries]
            period_start = min(timestamps)
            period_end = max(timestamps)
            
            # Group by month for growth analysis
            monthly_counts = {}
            for entry in entries:
                month_key = entry.timestamp.strftime("%Y-%m")
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            
            system_growth = {
                "total_period_days": (period_end - period_start).days,
                "monthly_activity": monthly_counts,
                "growth_rate": total_changes / ((period_end - period_start).days + 1)
            }
            
            # Identify major events
            major_events = []
            for entry in entries:
                if entry.severity in [LogSeverity.CRITICAL, LogSeverity.ERROR]:
                    major_events.append({
                        "timestamp": entry.timestamp,
                        "message": entry.message,
                        "severity": entry.severity.value,
                        "type": entry.entry_type.value
                    })
            
            # Calculate performance metrics
            performance_metrics = {
                "total_errors": len([e for e in entries if e.severity == LogSeverity.ERROR]),
                "total_critical": len([e for e in entries if e.severity == LogSeverity.CRITICAL]),
                "error_rate": len([e for e in entries if e.severity == LogSeverity.ERROR]) / total_changes,
                "commit_rate": len([e for e in entries if e.entry_type == LogEntryType.COMMIT]) / total_changes
            }
            
            # Identify architecture changes
            architecture_changes = []
            for entry in entries:
                if entry.entry_type == LogEntryType.COMMIT:
                    message_lower = entry.message.lower()
                    if any(word in message_lower for word in ['architecture', 'refactor', 'restructure', 'migration']):
                        architecture_changes.append(entry.message)
            
            # Identify technology updates
            technology_updates = []
            for entry in entries:
                if entry.entry_type == LogEntryType.COMMIT:
                    message_lower = entry.message.lower()
                    if any(word in message_lower for word in ['upgrade', 'update', 'dependency', 'library', 'framework']):
                        technology_updates.append(entry.message)
            
            return SystemEvolutionReport(
                period_start=period_start,
                period_end=period_end,
                total_changes=total_changes,
                active_contributors=active_contributors,
                system_growth=system_growth,
                major_events=major_events,
                performance_metrics=performance_metrics,
                architecture_changes=architecture_changes,
                technology_updates=technology_updates
            )
            
        except Exception as e:
            logger.error(f"Generate system evolution report failed: {e}")
            raise
    
    def generate_documentation(self,
                             doc_type: str,
                             format: DocFormat,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             template_id: Optional[str] = None,
                             custom_variables: Optional[Dict[str, Any]] = None) -> GeneratedDocumentation:
        """
        Generate documentation in specified format.
        
        Args:
            doc_type: Type of documentation (changelog, contributor_summary, system_evolution)
            format: Output format
            start_date: Start date for data
            end_date: End date for data
            template_id: Template ID to use
            custom_variables: Custom variables for template
            
        Returns:
            GeneratedDocumentation with formatted content
        """
        try:
            start_time = time.time()
            
            # Generate base data
            if doc_type == "changelog":
                data = self.generate_changelog(start_date, end_date)
                title = f"Changelog - {data.version}"
            elif doc_type == "contributor_summary":
                if not custom_variables or "contributor_id" not in custom_variables:
                    raise ValueError("contributor_id required for contributor summary")
                data = self.generate_contributor_summary(
                    custom_variables["contributor_id"], start_date, end_date
                )
                title = f"Contributor Summary - {data.contributor_name}"
            elif doc_type == "system_evolution":
                data = self.generate_system_evolution_report(start_date, end_date)
                title = f"System Evolution Report - {data.period_start.date()} to {data.period_end.date()}"
            else:
                raise ValueError(f"Unknown documentation type: {doc_type}")
            
            # Generate content based on format
            if format == DocFormat.MARKDOWN:
                content = self._generate_markdown(doc_type, data, custom_variables)
            elif format == DocFormat.JSON:
                content = json.dumps(asdict(data), indent=2, default=str)
            elif format == DocFormat.HTML:
                content = self._generate_html(doc_type, data, custom_variables)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            processing_time = time.time() - start_time
            
            # Create documentation object
            doc = GeneratedDocumentation(
                document_id=f"doc_{int(time.time() * 1000)}",
                title=title,
                format=format,
                content=content,
                metadata={
                    "doc_type": doc_type,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "template_id": template_id,
                    "custom_variables": custom_variables
                },
                generated_at=datetime.now(),
                processing_time=processing_time,
                entry_count=len(data.changes) if hasattr(data, 'changes') else 0
            )
            
            # Save to database
            self._save_documentation(doc)
            
            return doc
            
        except Exception as e:
            logger.error(f"Generate documentation failed: {e}")
            raise
    
    def _generate_markdown(self, doc_type: str, data: Any, custom_variables: Optional[Dict[str, Any]] = None) -> str:
        """Generate Markdown content."""
        if doc_type == "changelog":
            return self._generate_changelog_markdown(data)
        elif doc_type == "contributor_summary":
            return self._generate_contributor_summary_markdown(data)
        elif doc_type == "system_evolution":
            return self._generate_system_evolution_markdown(data)
        else:
            raise ValueError(f"Unknown documentation type: {doc_type}")
    
    def _generate_changelog_markdown(self, changelog: ChangelogEntry) -> str:
        """Generate Markdown changelog."""
        md = f"# Changelog - {changelog.version}\n\n"
        md += f"**Release Date:** {changelog.release_date.strftime('%Y-%m-%d')}\n\n"
        md += f"**Contributors:** {', '.join(changelog.contributors)}\n\n"
        md += f"## Summary\n\n{changelog.impact_summary}\n\n"
        
        if changelog.breaking_changes:
            md += "## Breaking Changes\n\n"
            for change in changelog.breaking_changes:
                md += f"- {change['message']} (by {change['author']})\n"
            md += "\n"
        
        if changelog.new_features:
            md += "## New Features\n\n"
            for feature in changelog.new_features:
                md += f"- {feature['message']} (by {feature['author']})\n"
            md += "\n"
        
        if changelog.bug_fixes:
            md += "## Bug Fixes\n\n"
            for fix in changelog.bug_fixes:
                md += f"- {fix['message']} (by {fix['author']})\n"
            md += "\n"
        
        if changelog.improvements:
            md += "## Improvements\n\n"
            for improvement in changelog.improvements:
                md += f"- {improvement['message']} (by {improvement['author']})\n"
        
        return md
    
    def _generate_contributor_summary_markdown(self, summary: ContributorSummary) -> str:
        """Generate Markdown contributor summary."""
        md = f"# Contributor Summary - {summary.contributor_name}\n\n"
        md += f"**Contributor ID:** {summary.contributor_id}\n\n"
        md += f"## Activity Overview\n\n"
        md += f"- **Total Commits:** {summary.total_commits}\n"
        md += f"- **Total Changes:** {summary.total_changes}\n"
        md += f"- **Activity Period:** {summary.activity_period[0].strftime('%Y-%m-%d')} to {summary.activity_period[1].strftime('%Y-%m-%d')}\n"
        md += f"- **Most Active Day:** {summary.most_active_day.strftime('%Y-%m-%d')}\n"
        md += f"- **Commit Frequency:** {summary.commit_frequency:.2f} commits/day\n"
        md += f"- **Impact Score:** {summary.impact_score}\n\n"
        
        if summary.recent_activities:
            md += "## Recent Activities\n\n"
            for activity in summary.recent_activities:
                md += f"- **{activity['timestamp'].strftime('%Y-%m-%d %H:%M')}** - {activity['message']} ({activity['type']})\n"
            md += "\n"
        
        if summary.top_contributions:
            md += "## Top Contributions\n\n"
            for contribution in summary.top_contributions:
                md += f"- {contribution}\n"
        
        return md
    
    def _generate_system_evolution_markdown(self, report: SystemEvolutionReport) -> str:
        """Generate Markdown system evolution report."""
        md = f"# System Evolution Report\n\n"
        md += f"**Period:** {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}\n\n"
        md += f"## Overview\n\n"
        md += f"- **Total Changes:** {report.total_changes}\n"
        md += f"- **Active Contributors:** {report.active_contributors}\n"
        md += f"- **Growth Rate:** {report.system_growth['growth_rate']:.2f} changes/day\n\n"
        
        md += f"## Performance Metrics\n\n"
        md += f"- **Total Errors:** {report.performance_metrics['total_errors']}\n"
        md += f"- **Total Critical Issues:** {report.performance_metrics['total_critical']}\n"
        md += f"- **Error Rate:** {report.performance_metrics['error_rate']:.2%}\n"
        md += f"- **Commit Rate:** {report.performance_metrics['commit_rate']:.2%}\n\n"
        
        if report.major_events:
            md += "## Major Events\n\n"
            for event in report.major_events:
                md += f"- **{event['timestamp'].strftime('%Y-%m-%d %H:%M')}** - {event['message']} ({event['severity']})\n"
            md += "\n"
        
        if report.architecture_changes:
            md += "## Architecture Changes\n\n"
            for change in report.architecture_changes:
                md += f"- {change}\n"
            md += "\n"
        
        if report.technology_updates:
            md += "## Technology Updates\n\n"
            for update in report.technology_updates:
                md += f"- {update}\n"
        
        return md
    
    def _generate_html(self, doc_type: str, data: Any, custom_variables: Optional[Dict[str, Any]] = None) -> str:
        """Generate HTML content."""
        markdown_content = self._generate_markdown(doc_type, data, custom_variables)
        
        # Simple Markdown to HTML conversion
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{doc_type.title()} Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
{markdown_content.replace('**', '<strong>').replace('**', '</strong>').replace('\n', '<br>')}
</body>
</html>
        """
        return html
    
    def _save_documentation(self, doc: GeneratedDocumentation):
        """Save generated documentation to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO generated_docs 
                    (document_id, title, format, content, metadata, generated_at, processing_time, entry_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc.document_id,
                    doc.title,
                    doc.format.value,
                    doc.content,
                    json.dumps(doc.metadata),
                    doc.generated_at.isoformat(),
                    doc.processing_time,
                    doc.entry_count
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save documentation: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the logbook doc generator."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total log entries
                cursor = conn.execute("SELECT COUNT(*) FROM log_entries")
                total_entries = cursor.fetchone()[0]
                
                # Entries by type
                cursor = conn.execute("""
                    SELECT entry_type, COUNT(*) FROM log_entries 
                    GROUP BY entry_type
                """)
                entries_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Generated documents
                cursor = conn.execute("SELECT COUNT(*) FROM generated_docs")
                total_docs = cursor.fetchone()[0]
                
                # Recent generation activity
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM generated_docs 
                    WHERE generated_at >= ?
                """, ((datetime.now() - timedelta(hours=1)).isoformat(),))
                recent_generations = cursor.fetchone()[0]
            
            return {
                "total_entries": total_entries,
                "entries_by_type": entries_by_type,
                "total_docs_generated": total_docs,
                "recent_generations": recent_generations,
                "database_size": Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)} 
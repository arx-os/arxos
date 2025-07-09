#!/usr/bin/env python3
"""
Logbook to Doc Generator CLI Tool

Command-line interface for generating, exporting, and retrieving documentation
from logbook entries in multiple formats (Markdown, JSON, HTML).
"""

import argparse
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from services.logbook_doc_generator import LogbookDocGenerator, DocFormat

class LogbookDocGeneratorCLI:
    def __init__(self):
        self.generator = LogbookDocGenerator()

    def run(self, args=None):
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        if parsed_args.command == "generate":
            self.generate(parsed_args)
        elif parsed_args.command == "get":
            self.get(parsed_args)
        elif parsed_args.command == "status":
            self.status(parsed_args)
        else:
            parser.print_help()

    def create_parser(self):
        parser = argparse.ArgumentParser(
            description="Logbook to Doc Generator CLI Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Generate command
        gen_parser = subparsers.add_parser("generate", help="Generate documentation")
        gen_parser.add_argument("--doc-type", required=True, choices=["changelog", "contributor_summary", "system_evolution"], help="Type of documentation")
        gen_parser.add_argument("--format", default="markdown", choices=["markdown", "json", "html"], help="Output format")
        gen_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
        gen_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
        gen_parser.add_argument("--template-id", help="Template ID to use")
        gen_parser.add_argument("--contributor-id", help="Contributor ID (for contributor_summary)")
        gen_parser.add_argument("--output", help="Output file for documentation")

        # Get command
        get_parser = subparsers.add_parser("get", help="Retrieve generated documentation by ID")
        get_parser.add_argument("--document-id", required=True, help="Document ID to retrieve")
        get_parser.add_argument("--output", help="Output file for documentation")

        # Status command
        status_parser = subparsers.add_parser("status", help="Get service status and metrics")

        return parser

    def generate(self, args):
        print("📝 Generating documentation...")
        start_date = datetime.fromisoformat(args.start_date) if args.start_date else None
        end_date = datetime.fromisoformat(args.end_date) if args.end_date else None
        custom_vars = {"contributor_id": args.contributor_id} if args.contributor_id else None
        fmt = DocFormat(args.format.lower())
        doc = self.generator.generate_documentation(
            doc_type=args.doc_type,
            format=fmt,
            start_date=start_date,
            end_date=end_date,
            template_id=args.template_id,
            custom_variables=custom_vars
        )
        print(f"✅ Generated: {doc.title} ({doc.format.value})")
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(doc.content)
            print(f"💾 Saved to: {args.output}")
        else:
            print("\n---\n")
            print(doc.content[:1000] + ("..." if len(doc.content) > 1000 else ""))

    def get(self, args):
        print(f"🔎 Retrieving document {args.document_id}...")
        import sqlite3
        with sqlite3.connect(self.generator.db_path) as conn:
            cursor = conn.execute("SELECT title, format, content FROM generated_docs WHERE document_id = ?", (args.document_id,))
            row = cursor.fetchone()
            if not row:
                print("❌ Document not found.")
                return
            title, fmt, content = row
            print(f"✅ Retrieved: {title} ({fmt})")
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"💾 Saved to: {args.output}")
            else:
                print("\n---\n")
                print(content[:1000] + ("..." if len(content) > 1000 else ""))

    def status(self, args):
        print("📊 Logbook Doc Generator Status:")
        metrics = self.generator.get_performance_metrics()
        for k, v in metrics.items():
            print(f"- {k}: {v}")


def main():
    cli = LogbookDocGeneratorCLI()
    cli.run()

if __name__ == "__main__":
    main() 
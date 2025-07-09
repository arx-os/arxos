#!/usr/bin/env python3
"""
Logbook to Doc Generator Demo

Comprehensive demonstration of logbook entry processing, documentation generation,
and multi-format output for the ARXOS platform.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.logbook_doc_generator import LogbookDocGenerator, DocFormat

class LogbookDocGeneratorDemo:
    def __init__(self):
        self.generator = LogbookDocGenerator()
        self.results = {}

    def run_demo(self):
        print("🚀 Logbook to Doc Generator Demo\n" + "="*50)
        self.demo_changelog()
        self.demo_contributor_summary()
        self.demo_system_evolution()
        self.demo_multi_format()
        self.demo_performance()
        self.print_summary()

    def demo_changelog(self):
        print("\n📝 Changelog Generation Demo\n" + "-"*30)
        doc = self.generator.generate_documentation(doc_type="changelog", format=DocFormat.MARKDOWN)
        print(doc.content[:500] + ("..." if len(doc.content) > 500 else ""))
        self.results['changelog'] = doc

    def demo_contributor_summary(self):
        print("\n👤 Contributor Summary Demo\n" + "-"*30)
        entries = self.generator.process_log_entries()
        contributor = entries[0].author
        doc = self.generator.generate_documentation(doc_type="contributor_summary", format=DocFormat.MARKDOWN, custom_variables={"contributor_id": contributor})
        print(doc.content[:500] + ("..." if len(doc.content) > 500 else ""))
        self.results['contributor_summary'] = doc

    def demo_system_evolution(self):
        print("\n📈 System Evolution Report Demo\n" + "-"*30)
        doc = self.generator.generate_documentation(doc_type="system_evolution", format=DocFormat.MARKDOWN)
        print(doc.content[:500] + ("..." if len(doc.content) > 500 else ""))
        self.results['system_evolution'] = doc

    def demo_multi_format(self):
        print("\n🔄 Multi-Format Output Demo\n" + "-"*30)
        doc_json = self.generator.generate_documentation(doc_type="changelog", format=DocFormat.JSON)
        print("JSON Output Preview:\n", doc_json.content[:300] + ("..." if len(doc_json.content) > 300 else ""))
        doc_html = self.generator.generate_documentation(doc_type="changelog", format=DocFormat.HTML)
        print("HTML Output Preview:\n", doc_html.content[:300] + ("..." if len(doc_html.content) > 300 else ""))
        self.results['json'] = doc_json
        self.results['html'] = doc_html

    def demo_performance(self):
        print("\n⚡ Performance Analysis Demo\n" + "-"*30)
        import time
        start = time.time()
        doc = self.generator.generate_documentation(doc_type="changelog", format=DocFormat.MARKDOWN)
        elapsed = time.time() - start
        print(f"Generation Time: {elapsed:.3f}s for {doc.entry_count} entries")
        self.results['performance'] = elapsed

    def print_summary(self):
        print("\n📋 Demo Summary\n" + "="*50)
        print(f"Changelog generated: {self.results['changelog'].title}")
        print(f"Contributor summary generated: {self.results['contributor_summary'].title}")
        print(f"System evolution report generated: {self.results['system_evolution'].title}")
        print(f"JSON and HTML outputs generated.")
        print(f"Performance: {self.results['performance']:.3f}s for changelog generation.")
        print("\n🎉 Logbook to Doc Generator Demo Complete!")

if __name__ == "__main__":
    LogbookDocGeneratorDemo().run_demo() 
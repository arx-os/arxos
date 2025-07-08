"""
Advanced Symbol Management Demo

Demonstrates all major capabilities of the Advanced Symbol Management service:
- Git-like version control for symbols
- Real-time symbol editing collaboration
- AI-powered symbol search and recommendations
- Symbol dependency tracking and validation
- Symbol performance analytics and usage tracking
- Symbol marketplace and sharing features
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.advanced_symbol_management import AdvancedSymbolManagement


def main():
    """Main demonstration function"""
    print("🎯 Advanced Symbol Management Demo")
    print("=" * 50)
    
    # Initialize the service
    symbol_management = AdvancedSymbolManagement()
    print("✓ Service initialized successfully")
    
    # Sample symbol content for demonstration
    sample_symbols = {
        "electrical_switch": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <rect x="20" y="20" width="60" height="60" fill="gray" stroke="black" stroke-width="2"/>
  <circle cx="50" cy="35" r="8" fill="red"/>
  <circle cx="50" cy="65" r="8" fill="green"/>
  <text x="50" y="85" text-anchor="middle" font-size="12">Switch</text>
</svg>''',
        
        "mechanical_valve": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80" viewBox="0 0 120 80">
  <rect x="10" y="30" width="100" height="20" fill="blue" stroke="black" stroke-width="2"/>
  <circle cx="60" cy="40" r="15" fill="yellow" stroke="black" stroke-width="2"/>
  <line x1="60" y1="25" x2="60" y2="55" stroke="black" stroke-width="3"/>
  <text x="60" y="70" text-anchor="middle" font-size="12">Valve</text>
</svg>''',
        
        "plumbing_fixture": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="80" height="120" viewBox="0 0 80 120">
  <rect x="30" y="20" width="20" height="80" fill="white" stroke="black" stroke-width="2"/>
  <circle cx="40" cy="30" r="5" fill="none" stroke="black" stroke-width="2"/>
  <rect x="25" y="100" width="30" height="20" fill="white" stroke="black" stroke-width="2"/>
  <text x="40" y="115" text-anchor="middle" font-size="10">Fixture</text>
</svg>''',
        
        "hvac_duct": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="150" height="60" viewBox="0 0 150 60">
  <rect x="10" y="20" width="130" height="20" fill="lightblue" stroke="black" stroke-width="2"/>
  <rect x="10" y="20" width="130" height="20" fill="none" stroke="black" stroke-width="1" stroke-dasharray="5,5"/>
  <text x="75" y="45" text-anchor="middle" font-size="12">HVAC Duct</text>
</svg>'''
    }
    
    print(f"\n📊 Created {len(sample_symbols)} sample symbols")
    
    # 1. Version Control Demo
    print("\n🔧 Version Control Demo")
    print("-" * 30)
    
    symbol_id = "demo_electrical_switch"
    author = "demo_user"
    
    # Create initial version
    print(f"Creating initial version of {symbol_id}...")
    version1 = symbol_management.create_symbol_version(
        symbol_id, sample_symbols["electrical_switch"], author, "Initial electrical switch design"
    )
    
    print(f"  ✓ Version created: {version1.version_hash[:8]}")
    print(f"  ✓ File size: {version1.file_size} bytes")
    print(f"  ✓ Compression ratio: {version1.compression_ratio:.2%}")
    
    # Create modified version
    modified_symbol = sample_symbols["electrical_switch"].replace("Switch", "Smart Switch")
    print(f"\nCreating modified version...")
    version2 = symbol_management.create_symbol_version(
        symbol_id, modified_symbol, author, "Added smart functionality"
    )
    
    print(f"  ✓ Modified version: {version2.version_hash[:8]}")
    print(f"  ✓ Parent version: {version2.parent_hash[:8]}")
    
    # Get version history
    print(f"\nRetrieving version history...")
    history = symbol_management.get_version_history(symbol_id)
    print(f"  ✓ Total versions: {len(history)}")
    for i, version in enumerate(history):
        print(f"    {i+1}. {version.version_hash[:8]} - {version.message}")
    
    # Compare versions
    print(f"\nComparing versions...")
    comparison = symbol_management.compare_versions(symbol_id, version1.version_hash, version2.version_hash)
    print(f"  ✓ Changes detected: {comparison['changes']['total_changes']} lines")
    print(f"  ✓ Lines added: {comparison['changes']['lines_added']}")
    print(f"  ✓ Lines removed: {comparison['changes']['lines_removed']}")
    
    # 2. Collaboration Demo
    print("\n👥 Real-time Collaboration Demo")
    print("-" * 30)
    
    collaboration_symbol = "collaboration_demo"
    users = ["user1", "user2", "user3"]
    
    # Create initial symbol
    symbol_management.create_symbol_version(
        collaboration_symbol, sample_symbols["mechanical_valve"], "creator", "Initial valve design"
    )
    
    # Start collaboration sessions
    session_ids = []
    for user in users:
        session_id = symbol_management.start_collaboration_session(collaboration_symbol, user)
        session_ids.append(session_id)
        print(f"  ✓ {user} started session: {session_id[:8]}")
    
    # Simulate collaborative editing
    print(f"\nSimulating collaborative editing...")
    modifications = [
        ("user1", "Added pressure sensor"),
        ("user2", "Updated valve size"),
        ("user3", "Added safety features")
    ]
    
    for user, modification in modifications:
        modified_content = sample_symbols["mechanical_valve"].replace("Valve", f"Valve ({modification})")
        success = symbol_management.update_collaboration_content(session_ids[users.index(user)], user, modified_content)
        print(f"  ✓ {user}: {modification}")
    
    # End collaboration sessions
    print(f"\nEnding collaboration sessions...")
    for session_id in session_ids:
        success = symbol_management.end_collaboration_session(session_id)
        print(f"  ✓ Session ended: {session_id[:8]}")
    
    # Check final version
    final_version = symbol_management.get_symbol_version(collaboration_symbol)
    print(f"  ✓ Final version created with collaborative changes")
    print(f"  ✓ Message: {final_version.message}")
    
    # 3. AI Search Demo
    print("\n🔍 AI-Powered Search Demo")
    print("-" * 30)
    
    # Index all symbols
    print("Indexing symbols for search...")
    for symbol_id, content in sample_symbols.items():
        metadata = {
            "category": symbol_id.split("_")[0],
            "tags": symbol_id.split("_"),
            "complexity": "medium"
        }
        symbol_management.index_symbol_for_search(symbol_id, content, metadata)
        print(f"  ✓ Indexed: {symbol_id}")
    
    # Search for symbols
    search_queries = ["electrical", "valve", "fixture", "hvac"]
    
    for query in search_queries:
        print(f"\nSearching for '{query}'...")
        results = symbol_management.search_symbols(query, limit=3)
        
        print(f"  ✓ Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"    {i+1}. {result.symbol_id} (score: {result.score:.2f})")
            print(f"       Factors: {', '.join(result.relevance_factors)}")
    
    # Get AI recommendations
    print(f"\nGetting AI recommendations...")
    for symbol_id in sample_symbols.keys():
        recommendations = symbol_management.get_ai_recommendations(symbol_id)
        if recommendations:
            print(f"  ✓ Recommendations for {symbol_id}:")
            for i, rec in enumerate(recommendations[:2]):
                print(f"    {i+1}. {rec.symbol_id} (similarity: {rec.score:.2f})")
    
    # 4. Dependency Tracking Demo
    print("\n🔗 Dependency Tracking Demo")
    print("-" * 30)
    
    # Create symbols with dependencies
    print("Creating symbols with dependencies...")
    
    # Main system symbol
    main_system = "main_control_system"
    symbol_management.create_symbol_version(main_system, sample_symbols["electrical_switch"], "designer", "Main control system")
    
    # Add dependencies
    dependencies = [
        ("electrical_switch", "includes"),
        ("mechanical_valve", "controls"),
        ("plumbing_fixture", "monitors")
    ]
    
    for dep_id, dep_type in dependencies:
        success = symbol_management.add_symbol_dependency(main_system, dep_id, dep_type)
        print(f"  ✓ Added dependency: {main_system} -> {dep_id} ({dep_type})")
    
    # Get dependencies
    print(f"\nRetrieving dependencies...")
    deps = symbol_management.get_symbol_dependencies(main_system)
    print(f"  ✓ {len(deps)} dependencies found:")
    for dep in deps:
        print(f"    - {dep.dependency_id} ({dep.dependency_type})")
    
    # Validate dependencies
    print(f"\nValidating dependencies...")
    validation = symbol_management.validate_symbol_dependencies(main_system)
    print(f"  ✓ Valid: {validation['valid']}")
    if validation['errors']:
        print(f"  ❌ Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"  ⚠️  Warnings: {validation['warnings']}")
    
    # 5. Analytics Demo
    print("\n📈 Analytics Demo")
    print("-" * 30)
    
    # Track usage for all symbols
    print("Tracking symbol usage...")
    users = ["engineer1", "engineer2", "designer1", "operator1"]
    
    for symbol_id in sample_symbols.keys():
        for user in users:
            context = {"project": "demo_project", "session": "demo_session"}
            symbol_management.track_symbol_usage(symbol_id, user, context)
        print(f"  ✓ Tracked usage for: {symbol_id}")
    
    # Get analytics
    print(f"\nRetrieving analytics...")
    for symbol_id in sample_symbols.keys():
        analytics = symbol_management.get_symbol_analytics(symbol_id)
        if analytics:
            print(f"  ✓ {symbol_id}:")
            print(f"    - Usage count: {analytics.usage_count}")
            print(f"    - Popularity score: {analytics.popularity_score:.2f}")
            print(f"    - Last used: {analytics.last_used}")
    
    # Calculate popularity scores
    print(f"\nCalculating popularity scores...")
    for symbol_id in sample_symbols.keys():
        score = symbol_management.calculate_popularity_score(symbol_id)
        print(f"  ✓ {symbol_id}: {score:.2f}")
    
    # 6. Marketplace Demo
    print("\n🛒 Marketplace Demo")
    print("-" * 30)
    
    # Add symbols to marketplace
    marketplace_items = [
        {
            "symbol_id": "electrical_switch",
            "author": "electrical_engineer",
            "title": "Smart Electrical Switch",
            "description": "Advanced electrical switch with smart controls",
            "category": "electrical",
            "tags": ["switch", "smart", "control"],
            "price": 0.0,
            "license": "MIT"
        },
        {
            "symbol_id": "mechanical_valve",
            "author": "mechanical_engineer",
            "title": "Industrial Valve",
            "description": "High-performance industrial valve for heavy use",
            "category": "mechanical",
            "tags": ["valve", "industrial", "heavy-duty"],
            "price": 5.0,
            "license": "Commercial"
        },
        {
            "symbol_id": "plumbing_fixture",
            "author": "plumbing_specialist",
            "title": "Modern Plumbing Fixture",
            "description": "Contemporary plumbing fixture design",
            "category": "plumbing",
            "tags": ["fixture", "modern", "contemporary"],
            "price": 2.0,
            "license": "MIT"
        },
        {
            "symbol_id": "hvac_duct",
            "author": "hvac_expert",
            "title": "HVAC Duct System",
            "description": "Complete HVAC duct system for commercial buildings",
            "category": "hvac",
            "tags": ["hvac", "duct", "commercial"],
            "price": 10.0,
            "license": "Commercial"
        }
    ]
    
    print("Adding symbols to marketplace...")
    for item_data in marketplace_items:
        success = symbol_management.add_marketplace_item(**item_data)
        print(f"  ✓ Added: {item_data['title']} (${item_data['price']})")
    
    # Search marketplace
    print(f"\nSearching marketplace...")
    search_terms = ["electrical", "industrial", "modern", "commercial"]
    
    for term in search_terms:
        results = symbol_management.search_marketplace(term)
        print(f"  ✓ '{term}' search: {len(results)} results")
        for result in results[:2]:
            print(f"    - {result.title} by {result.author} (${result.price})")
    
    # Rate marketplace items
    print(f"\nRating marketplace items...")
    ratings = [
        ("electrical_switch", "user1", 4.5, "Excellent design!"),
        ("mechanical_valve", "user2", 4.0, "Very reliable"),
        ("plumbing_fixture", "user3", 5.0, "Perfect for my project"),
        ("hvac_duct", "user4", 4.8, "Great quality")
    ]
    
    for symbol_id, user, rating, review in ratings:
        success = symbol_management.rate_marketplace_item(symbol_id, user, rating, review)
        print(f"  ✓ {user} rated {symbol_id}: {rating}/5.0")
    
    # 7. Performance Demo
    print("\n⚡ Performance Demo")
    print("-" * 30)
    
    # Test with multiple concurrent operations
    print("Testing concurrent operations...")
    
    def concurrent_operation(symbol_id, user_id, operation_type):
        if operation_type == "version":
            symbol_management.create_symbol_version(
                symbol_id, sample_symbols["electrical_switch"], user_id, f"Concurrent version by {user_id}"
            )
        elif operation_type == "usage":
            symbol_management.track_symbol_usage(symbol_id, user_id)
        elif operation_type == "search":
            symbol_management.search_symbols("electrical")
    
    # Run concurrent operations
    threads = []
    operations = ["version", "usage", "search"]
    
    for i in range(3):
        for op_type in operations:
            thread = threading.Thread(
                target=concurrent_operation,
                args=(f"concurrent_symbol_{i}", f"user_{i}", op_type)
            )
            threads.append(thread)
            thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print(f"  ✓ Completed {len(threads)} concurrent operations")
    
    # 8. Statistics Demo
    print("\n📊 Service Statistics")
    print("-" * 30)
    
    stats = symbol_management.get_statistics()
    print(f"  ✓ Total symbols: {stats['total_symbols']}")
    print(f"  ✓ Total versions: {stats['total_versions']}")
    print(f"  ✓ Active sessions: {stats['active_sessions']}")
    print(f"  ✓ Search index size: {stats['search_index_size']}")
    print(f"  ✓ Marketplace items: {stats['marketplace_items']}")
    print(f"  ✓ Dependency relationships: {stats['dependency_relationships']}")
    print(f"  ✓ Analytics tracked: {stats['analytics_tracked']}")
    
    # Cleanup
    print("\n🧹 Cleanup")
    print("-" * 30)
    
    symbol_management.cleanup()
    print("  ✓ Service cleanup completed")
    
    print("\n🎉 Advanced Symbol Management Demo Completed!")
    print("=" * 50)
    print("\nKey Features Demonstrated:")
    print("  ✓ Git-like version control with history tracking")
    print("  ✓ Real-time collaboration with multiple users")
    print("  ✓ AI-powered search with relevance scoring")
    print("  ✓ Dependency tracking and validation")
    print("  ✓ Usage analytics and popularity scoring")
    print("  ✓ Marketplace with ratings and reviews")
    print("  ✓ Concurrent operations and thread safety")
    print("  ✓ Comprehensive statistics and monitoring")


if __name__ == '__main__':
    main() 
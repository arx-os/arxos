#!/usr/bin/env python3
"""
Load Testing Script for Arxos Platform

This script performs comprehensive load testing including:
- Normal load testing
- Peak load testing
- Stress testing
- Spike testing
- Performance analysis
- Report generation
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import Dict, List, Optional
import logging
import argparse
import csv
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LoadTestResult:
    """Load test result data class"""
    scenario_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    response_times: List[float]
    throughput: float
    error_rate: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    avg_response_time: float

class LoadTester:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.results = []
        
    async def run_load_tests(self, scenarios: List[Dict]) -> List[LoadTestResult]:
        """Run all load test scenarios"""
        logger.info("Starting load testing")
        
        results = []
        for scenario in scenarios:
            logger.info(f"Running scenario: {scenario['name']}")
            result = await self.run_scenario(scenario)
            results.append(result)
            
            # Wait between scenarios
            await asyncio.sleep(10)
        
        return results
    
    async def run_scenario(self, scenario: Dict) -> LoadTestResult:
        """Run a single load test scenario"""
        start_time = time.time()
        
        # Create tasks for concurrent users
        tasks = []
        for i in range(scenario['users']):
            task = asyncio.create_task(
                self.simulate_user(scenario['duration'], scenario['endpoints'])
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        all_response_times = []
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        
        for user_result in user_results:
            if isinstance(user_result, Exception):
                logger.error(f"User simulation failed: {user_result}")
                continue
            
            all_response_times.extend(user_result['response_times'])
            total_requests += user_result['total_requests']
            successful_requests += user_result['successful_requests']
            failed_requests += user_result['failed_requests']
        
        # Calculate metrics
        duration = time.time() - start_time
        throughput = total_requests / duration if duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate percentiles
        if all_response_times:
            p50_response_time = statistics.quantiles(all_response_times, n=100)[49]
            p95_response_time = statistics.quantiles(all_response_times, n=100)[94]
            p99_response_time = statistics.quantiles(all_response_times, n=100)[98]
            min_response_time = min(all_response_times)
            max_response_time = max(all_response_times)
            avg_response_time = statistics.mean(all_response_times)
        else:
            p50_response_time = p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = avg_response_time = 0
        
        return LoadTestResult(
            scenario_name=scenario['name'],
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            response_times=all_response_times,
            throughput=throughput,
            error_rate=error_rate,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            avg_response_time=avg_response_time
        )
    
    async def simulate_user(self, duration: int, endpoints: List[Dict]) -> Dict:
        """Simulate a single user session"""
        start_time = time.time()
        response_times = []
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                # Select random endpoint based on weights
                endpoint = self.select_endpoint(endpoints)
                
                request_start = time.time()
                try:
                    response = await self.make_request(session, endpoint)
                    response_time = (time.time() - request_start) * 1000
                    
                    response_times.append(response_time)
                    total_requests += 1
                    
                    if response.status < 400:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        logger.warning(f"Request failed: {response.status}")
                    
                except Exception as e:
                    response_time = (time.time() - request_start) * 1000
                    response_times.append(response_time)
                    total_requests += 1
                    failed_requests += 1
                    logger.error(f"Request error: {str(e)}")
                
                # Random delay between requests
                await asyncio.sleep(0.1)
        
        return {
            'response_times': response_times,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests
        }
    
    def select_endpoint(self, endpoints: List[Dict]) -> str:
        """Select endpoint based on configured weights"""
        import random
        
        # Calculate total weight
        total_weight = sum(ep['weight'] for ep in endpoints)
        
        # Select based on weights
        rand = random.uniform(0, total_weight)
        current_weight = 0
        
        for endpoint in endpoints:
            current_weight += endpoint['weight']
            if rand <= current_weight:
                return endpoint['name']
        
        return endpoints[0]['name']  # Fallback
    
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str) -> aiohttp.ClientResponse:
        """Make HTTP request to endpoint"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        
        if endpoint == "upload/svg":
            # Simulate file upload
            data = aiohttp.FormData()
            data.add_field('file', b'<svg><rect width="100" height="100"/></svg>', filename='test.svg')
            return await session.post(url, data=data, headers=self.headers)
        elif endpoint == "assemble/bim":
            # Simulate BIM assembly
            data = {'svg_content': '<svg><rect width="100" height="100"/></svg>', 'format': 'json'}
            return await session.post(url, data=data, headers=self.headers)
        elif endpoint == "export/create-job":
            # Simulate export job creation
            data = {'building_id': 'test_building', 'format': 'ifc-lite'}
            return await session.post(url, json=data, headers=self.headers)
        elif endpoint == "security/privacy/controls":
            # Simulate privacy controls
            data = {'data': {'test': 'data'}, 'classification': 'internal'}
            return await session.post(url, json=data, headers=self.headers)
        elif endpoint == "security/encryption/encrypt":
            # Simulate encryption
            data = {'data': 'test data', 'layer': 'storage'}
            return await session.post(url, json=data, headers=self.headers)
        else:
            # Default GET request
            return await session.get(url, headers=self.headers)
    
    def analyze_results(self, results: List[LoadTestResult]) -> Dict:
        """Analyze load test results"""
        analysis = {
            'summary': {
                'total_scenarios': len(results),
                'total_requests': sum(r.total_requests for r in results),
                'total_successful': sum(r.successful_requests for r in results),
                'total_failed': sum(r.failed_requests for r in results),
                'overall_error_rate': 0,
                'overall_throughput': 0
            },
            'scenarios': {},
            'performance_analysis': {},
            'recommendations': []
        }
        
        # Calculate overall metrics
        total_requests = analysis['summary']['total_requests']
        if total_requests > 0:
            analysis['summary']['overall_error_rate'] = (
                analysis['summary']['total_failed'] / total_requests * 100
            )
        
        # Analyze each scenario
        for result in results:
            analysis['scenarios'][result.scenario_name] = {
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'error_rate': result.error_rate,
                'throughput': result.throughput,
                'response_times': {
                    'avg': result.avg_response_time,
                    'p50': result.p50_response_time,
                    'p95': result.p95_response_time,
                    'p99': result.p99_response_time,
                    'min': result.min_response_time,
                    'max': result.max_response_time
                }
            }
        
        # Performance analysis
        all_response_times = []
        for result in results:
            all_response_times.extend(result.response_times)
        
        if all_response_times:
            analysis['performance_analysis'] = {
                'overall_avg_response_time': statistics.mean(all_response_times),
                'overall_p95_response_time': statistics.quantiles(all_response_times, n=100)[94],
                'overall_p99_response_time': statistics.quantiles(all_response_times, n=100)[98],
                'response_time_distribution': {
                    'fast': len([t for t in all_response_times if t < 100]),
                    'normal': len([t for t in all_response_times if 100 <= t < 1000]),
                    'slow': len([t for t in all_response_times if 1000 <= t < 5000]),
                    'very_slow': len([t for t in all_response_times if t >= 5000])
                }
            }
        
        # Generate recommendations
        analysis['recommendations'] = self.generate_recommendations(results)
        
        return analysis
    
    def generate_recommendations(self, results: List[LoadTestResult]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for result in results:
            if result.error_rate > 5:
                recommendations.append(
                    f"High error rate in {result.scenario_name}: {result.error_rate:.2f}%. "
                    "Investigate server errors and optimize error handling."
                )
            
            if result.p95_response_time > 2000:
                recommendations.append(
                    f"Slow response times in {result.scenario_name}: "
                    f"P95 = {result.p95_response_time:.2f}ms. "
                    "Consider performance optimization."
                )
            
            if result.throughput < 10:
                recommendations.append(
                    f"Low throughput in {result.scenario_name}: {result.throughput:.2f} req/s. "
                    "Consider scaling or optimization."
                )
        
        if not recommendations:
            recommendations.append("All scenarios performed within acceptable limits.")
        
        return recommendations
    
    def generate_report(self, results: List[LoadTestResult], analysis: Dict) -> str:
        """Generate comprehensive load test report"""
        report = f"""
# Arxos Platform Load Test Report

## Test Summary
- **Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Base URL**: {self.base_url}
- **Total Scenarios**: {analysis['summary']['total_scenarios']}
- **Total Requests**: {analysis['summary']['total_requests']:,}
- **Overall Error Rate**: {analysis['summary']['overall_error_rate']:.2f}%

## Scenario Results
"""
        
        for scenario_name, scenario_data in analysis['scenarios'].items():
            report += f"""
### {scenario_name}
- **Total Requests**: {scenario_data['total_requests']:,}
- **Successful Requests**: {scenario_data['successful_requests']:,}
- **Failed Requests**: {scenario_data['failed_requests']:,}
- **Error Rate**: {scenario_data['error_rate']:.2f}%
- **Throughput**: {scenario_data['throughput']:.2f} req/s
- **Response Times**:
  - Average: {scenario_data['response_times']['avg']:.2f}ms
  - P50: {scenario_data['response_times']['p50']:.2f}ms
  - P95: {scenario_data['response_times']['p95']:.2f}ms
  - P99: {scenario_data['response_times']['p99']:.2f}ms
  - Min: {scenario_data['response_times']['min']:.2f}ms
  - Max: {scenario_data['response_times']['max']:.2f}ms
"""
        
        if analysis['performance_analysis']:
            report += f"""
## Performance Analysis
- **Overall Average Response Time**: {analysis['performance_analysis']['overall_avg_response_time']:.2f}ms
- **Overall P95 Response Time**: {analysis['performance_analysis']['overall_p95_response_time']:.2f}ms
- **Overall P99 Response Time**: {analysis['performance_analysis']['overall_p99_response_time']:.2f}ms

### Response Time Distribution
- **Fast (<100ms)**: {analysis['performance_analysis']['response_time_distribution']['fast']:,}
- **Normal (100-1000ms)**: {analysis['performance_analysis']['response_time_distribution']['normal']:,}
- **Slow (1000-5000ms)**: {analysis['performance_analysis']['response_time_distribution']['slow']:,}
- **Very Slow (>5000ms)**: {analysis['performance_analysis']['response_time_distribution']['very_slow']:,}
"""
        
        report += f"""
## Recommendations
"""
        for recommendation in analysis['recommendations']:
            report += f"- {recommendation}\n"
        
        return report
    
    def save_results(self, results: List[LoadTestResult], analysis: Dict, output_file: str):
        """Save results to file"""
        # Save detailed results as JSON
        json_file = output_file.replace('.csv', '.json')
        with open(json_file, 'w') as f:
            json.dump({
                'results': [vars(r) for r in results],
                'analysis': analysis
            }, f, indent=2)
        
        # Save summary as CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Scenario', 'Total Requests', 'Successful', 'Failed', 'Error Rate (%)',
                'Throughput (req/s)', 'Avg Response Time (ms)', 'P95 Response Time (ms)'
            ])
            
            for result in results:
                writer.writerow([
                    result.scenario_name,
                    result.total_requests,
                    result.successful_requests,
                    result.failed_requests,
                    f"{result.error_rate:.2f}",
                    f"{result.throughput:.2f}",
                    f"{result.avg_response_time:.2f}",
                    f"{result.p95_response_time:.2f}"
                ])
        
        logger.info(f"Results saved to {json_file} and {output_file}")

def get_default_scenarios() -> List[Dict]:
    """Get default load test scenarios"""
    return [
        {
            "name": "Normal Load",
            "users": 50,
            "duration": 300,  # 5 minutes
            "endpoints": [
                {"name": "health", "weight": 20},
                {"name": "upload/svg", "weight": 15},
                {"name": "assemble/bim", "weight": 25},
                {"name": "export/create-job", "weight": 20},
                {"name": "security/privacy/controls", "weight": 10},
                {"name": "security/encryption/encrypt", "weight": 10}
            ]
        },
        {
            "name": "Peak Load",
            "users": 200,
            "duration": 600,  # 10 minutes
            "endpoints": [
                {"name": "health", "weight": 15},
                {"name": "upload/svg", "weight": 20},
                {"name": "assemble/bim", "weight": 30},
                {"name": "export/create-job", "weight": 25},
                {"name": "security/privacy/controls", "weight": 5},
                {"name": "security/encryption/encrypt", "weight": 5}
            ]
        },
        {
            "name": "Stress Test",
            "users": 500,
            "duration": 900,  # 15 minutes
            "endpoints": [
                {"name": "health", "weight": 10},
                {"name": "upload/svg", "weight": 25},
                {"name": "assemble/bim", "weight": 35},
                {"name": "export/create-job", "weight": 20},
                {"name": "security/privacy/controls", "weight": 5},
                {"name": "security/encryption/encrypt", "weight": 5}
            ]
        },
        {
            "name": "Spike Test",
            "users": 1000,
            "duration": 300,  # 5 minutes
            "endpoints": [
                {"name": "health", "weight": 5},
                {"name": "upload/svg", "weight": 30},
                {"name": "assemble/bim", "weight": 40},
                {"name": "export/create-job", "weight": 20},
                {"name": "security/privacy/controls", "weight": 2},
                {"name": "security/encryption/encrypt", "weight": 3}
            ]
        }
    ]

async def main():
    """Main load testing function"""
    parser = argparse.ArgumentParser(description='Load Testing for Arxos Platform')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Base URL for testing')
    parser.add_argument('--api-key', default='test-api-key', help='API key for authentication')
    parser.add_argument('--scenarios', help='Path to scenarios JSON file')
    parser.add_argument('--output', default='load_test_results.csv', help='Output file path')
    
    args = parser.parse_args()
    
    # Initialize load tester
    tester = LoadTester(args.base_url, args.api_key)
    
    # Load scenarios
    if args.scenarios and os.path.exists(args.scenarios):
        with open(args.scenarios, 'r') as f:
            scenarios = json.load(f)
    else:
        scenarios = get_default_scenarios()
    
    logger.info(f"Running load tests with {len(scenarios)} scenarios")
    
    # Run load tests
    results = await tester.run_load_tests(scenarios)
    
    # Analyze results
    analysis = tester.analyze_results(results)
    
    # Generate report
    report = tester.generate_report(results, analysis)
    
    # Save results
    tester.save_results(results, analysis, args.output)
    
    # Print summary
    print("\n" + "="*50)
    print("LOAD TEST SUMMARY")
    print("="*50)
    print(f"Total Scenarios: {analysis['summary']['total_scenarios']}")
    print(f"Total Requests: {analysis['summary']['total_requests']:,}")
    print(f"Overall Error Rate: {analysis['summary']['overall_error_rate']:.2f}%")
    
    if analysis['performance_analysis']:
        print(f"Overall Avg Response Time: {analysis['performance_analysis']['overall_avg_response_time']:.2f}ms")
        print(f"Overall P95 Response Time: {analysis['performance_analysis']['overall_p95_response_time']:.2f}ms")
    
    print("\nRECOMMENDATIONS:")
    for recommendation in analysis['recommendations']:
        print(f"- {recommendation}")
    
    print(f"\nDetailed report saved to: {args.output}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main()) 
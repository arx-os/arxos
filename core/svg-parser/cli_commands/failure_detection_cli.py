#!/usr/bin/env python3
"""
Failure Detection CLI Tool

This tool provides a command-line interface for failure detection operations, including anomaly detection, trend analysis, pattern recognition, failure prediction, risk assessment, and sample data generation.

Usage examples:
  python -m arx_svg_parser.cmd.failure_detection_cli analyze-trends data.csv --column temperature
  python -m arx_svg_parser.cmd.failure_detection_cli find-patterns data.csv --column pressure
  python -m arx_svg_parser.cmd.failure_detection_cli assess-risks components.json
  python -m arx_svg_parser.cmd.failure_detection_cli generate-sample sample.json --n-samples 500

Options can also be set via environment variables or config files if config support is added.
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from datetime import datetime
import os

# Use relative imports for package context
from ..services.failure_detection import FailureDetectionSystem

# Only import ML components if available
try:
    from services.failure_detection import AnomalyDetector, FailurePredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML components not available. Anomaly detection and failure prediction will be disabled.")

try:
    import yaml
except ImportError:
    yaml = None

def load_config(args) -> dict:
    config = {}
    config_file = getattr(args, 'config', None) or os.environ.get('ARXOS_FAILURE_DETECTION_CONFIG')
    if config_file:
        ext = Path(config_file).suffix.lower()
        try:
            with open(config_file, 'r') as f:
                if ext in ['.yaml', '.yml'] and yaml:
                    config = yaml.safe_load(f)
                elif ext == '.json':
                    config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}", file=sys.stderr)
    else:
        for default in [Path.cwd() / 'arxos_cli_config.yaml', Path.home() / 'arxos_cli_config.yaml']:
            if default.exists() and yaml:
                with open(default, 'r') as f:
                    config = yaml.safe_load(f)
                break
    for key, value in os.environ.items():
        if key.startswith('ARXOS_FAILURE_DETECTION_'):
            config[key[len('ARXOS_FAILURE_DETECTION_'):].lower()] = value
    for k, v in vars(args).items():
        if v is not None:
            config[k] = v
    return config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FailureDetectionCLI:
    """CLI interface for failure detection"""
    
    def __init__(self):
        self.system = FailureDetectionSystem()
    
    def load_data(self, data_file: str):
        """Load data from file"""
        # This method is not directly used in the new_code, but kept for compatibility
        # if not PANDAS_AVAILABLE:
        #     logger.error("pandas not available. Cannot load CSV files.")
        #     return None
        
        try:
            # Assuming data is a pandas DataFrame if pandas is available
            # For direct script execution, we'll try to load as CSV
            import pandas as pd
            data = pd.read_csv(data_file)
            logger.info(f"Loaded {len(data)} records with {len(data.columns)} columns")
            return data
        except ImportError:
            # Fallback for direct script execution if pandas is not available
            logger.warning("pandas not available. Cannot load CSV files. Attempting to load as JSON.")
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded {len(data)} records from JSON file")
                return data
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
                return None
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return None
    
    def detect_anomalies(self, data_file: str, output_file: str = None) -> None:
        """Detect anomalies in data"""
        if not ML_AVAILABLE:
            logger.error("ML components not available. Anomaly detection disabled.")
            return
        
        logger.info(f"Loading data from {data_file}")
        
        try:
            data = self.load_data(data_file)
            if data is None:
                return
            
            # Select numeric columns for anomaly detection
            numeric_data = data.select_dtypes(include=[np.number])
            
            if numeric_data.empty:
                logger.error("No numeric columns found for anomaly detection")
                return
            
            logger.info("Training anomaly detection model...")
            self.system.anomaly_detector.fit(numeric_data)
            
            logger.info("Detecting anomalies...")
            anomaly_scores = self.system.anomaly_detector.predict_scores(numeric_data)
            anomaly_predictions = self.system.anomaly_detector.predict(numeric_data)
            
            # Find anomaly indices
            anomaly_indices = np.where(anomaly_predictions == 1)[0]
            
            logger.info(f"Detected {len(anomaly_indices)} anomalies")
            
            # Create results
            results = {
                'timestamp': datetime.now().isoformat(),
                'data_file': data_file,
                'total_records': len(data),
                'anomalies_detected': len(anomaly_indices),
                'anomaly_indices': anomaly_indices.tolist(),
                'anomaly_scores': anomaly_scores.tolist(),
                'anomaly_details': []
            }
            
            for idx in anomaly_indices:
                if idx < len(data):
                    anomaly_detail = {
                        'index': int(idx),
                        'score': float(anomaly_scores[idx]),
                        'data_point': data.iloc[idx].to_dict()
                    }
                    results['anomaly_details'].append(anomaly_detail)
            
            # Save results
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"Results saved to {output_file}")
            else:
                print(json.dumps(results, indent=2, default=str))
        
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
    
    def analyze_trends(self, data_file: str, column: str = None, output_file: str = None) -> None:
        """Analyze trends in data"""
        logger.info(f"Loading data from {data_file}")
        
        try:
            data = self.load_data(data_file)
            if data is None:
                return
            
            if column and column not in data.columns:
                logger.error(f"Column '{column}' not found in data")
                return
            
            # Analyze trends for specified column or all numeric columns
            columns_to_analyze = [column] if column else data.select_dtypes(include=[np.number]).columns
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'data_file': data_file,
                'trends_detected': 0,
                'trend_details': []
            }
            
            for col in columns_to_analyze:
                if col in data.columns:
                    logger.info(f"Analyzing trends in column: {col}")
                    trends = self.system.trend_analyzer.detect_trends(data[col])
                    
                    for trend in trends:
                        trend_detail = {
                            'column': col,
                            'index': trend['index'],
                            'trend_type': trend['trend_type'],
                            'slope': trend['slope'],
                            'strength': trend['strength'],
                            'window_data': trend['window_data']
                        }
                        results['trend_details'].append(trend_detail)
                        results['trends_detected'] += 1
            
            logger.info(f"Detected {results['trends_detected']} trends")
            
            # Save results
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"Results saved to {output_file}")
            else:
                print(json.dumps(results, indent=2, default=str))
        
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
    
    def find_patterns(self, data_file: str, column: str = None, output_file: str = None) -> None:
        """Find repeating patterns in data"""
        logger.info(f"Loading data from {data_file}")
        
        try:
            data = self.load_data(data_file)
            if data is None:
                return
            
            if column and column not in data.columns:
                logger.error(f"Column '{column}' not found in data")
                return
            
            # Find patterns for specified column or all numeric columns
            columns_to_analyze = [column] if column else data.select_dtypes(include=[np.number]).columns
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'data_file': data_file,
                'patterns_found': 0,
                'pattern_details': []
            }
            
            for col in columns_to_analyze:
                if col in data.columns:
                    logger.info(f"Finding patterns in column: {col}")
                    patterns = self.system.pattern_recognizer.find_repeating_patterns(data[col])
                    
                    for pattern in patterns:
                        pattern_detail = {
                            'column': col,
                            'pattern': pattern['pattern'],
                            'start_indices': pattern['start_indices'],
                            'length': pattern['length'],
                            'occurrences': pattern['occurrences']
                        }
                        results['pattern_details'].append(pattern_detail)
                        results['patterns_found'] += 1
            
            logger.info(f"Found {results['patterns_found']} patterns")
            
            # Save results
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"Results saved to {output_file}")
            else:
                print(json.dumps(results, indent=2, default=str))
        
        except Exception as e:
            logger.error(f"Pattern recognition failed: {e}")
    
    def predict_failures(self, data_file: str, target_column: str = "failure", output_file: str = None) -> None:
        """Predict failures in data"""
        if not ML_AVAILABLE:
            logger.error("ML components not available. Failure prediction disabled.")
            return
        
        logger.info(f"Loading data from {data_file}")
        
        try:
            data = self.load_data(data_file)
            if data is None:
                return
            
            if target_column not in data.columns:
                logger.error(f"Target column '{target_column}' not found in data")
                return
            
            logger.info("Training failure prediction model...")
            self.system.failure_predictor.fit(data, target_column)
            
            logger.info("Making failure predictions...")
            failure_probs = self.system.failure_predictor.predict_proba(data)
            
            # Get feature importance
            feature_importance = self.system.failure_predictor.get_feature_importance()
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'data_file': data_file,
                'total_records': len(data),
                'predictions': [],
                'feature_importance': feature_importance,
                'high_risk_predictions': 0
            }
            
            # Process predictions
            for i, prob in enumerate(failure_probs[:, 1] if failure_probs.shape[1] > 1 else failure_probs[:, 0]):
                prediction = {
                    'index': i,
                    'failure_probability': float(prob),
                    'risk_level': 'high' if prob > 0.7 else 'medium' if prob > 0.3 else 'low'
                }
                results['predictions'].append(prediction)
                
                if prob > 0.7:
                    results['high_risk_predictions'] += 1
            
            logger.info(f"Generated {len(results['predictions'])} predictions")
            logger.info(f"High-risk predictions: {results['high_risk_predictions']}")
            
            # Save results
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"Results saved to {output_file}")
            else:
                print(json.dumps(results, indent=2, default=str))
        
        except Exception as e:
            logger.error(f"Failure prediction failed: {e}")
    
    def assess_risks(self, component_file: str = None, output_file: str = None) -> None:
        """Assess risks for components"""
        try:
            if component_file:
                logger.info(f"Loading component data from {component_file}")
                with open(component_file, 'r') as f:
                    components = json.load(f)
            else:
                logger.info("Generating sample component data")
                # Assuming generate_component_data is available in services.failure_detection
                from services.failure_detection import generate_component_data
                components = generate_component_data(10)
            
            logger.info(f"Assessing risks for {len(components)} components")
            assessments = self.system.assess_risks(components)
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'components_assessed': len(assessments),
                'high_risk_components': 0,
                'assessments': []
            }
            
            for assessment in assessments:
                assessment_detail = {
                    'component_id': assessment.component_id,
                    'risk_score': assessment.risk_score,
                    'risk_factors': assessment.risk_factors,
                    'recommendations': assessment.recommendations,
                    'risk_level': 'high' if assessment.risk_score > 0.7 else 'medium' if assessment.risk_score > 0.4 else 'low'
                }
                results['assessments'].append(assessment_detail)
                
                if assessment.risk_score > 0.7:
                    results['high_risk_components'] += 1
            
            logger.info(f"Completed risk assessment for {len(assessments)} components")
            logger.info(f"High-risk components: {results['high_risk_components']}")
            
            # Save results
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"Results saved to {output_file}")
            else:
                print(json.dumps(results, indent=2, default=str))
        
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
    
    def comprehensive_analysis(self, data_file: str, output_file: str = None) -> None:
        """Run comprehensive failure analysis"""
        logger.info(f"Running comprehensive analysis on {data_file}")
        
        try:
            data = self.load_data(data_file)
            if data is None:
                return
            
            # Run all analyses
            # Assuming process_telemetry_data and get_summary are available in FailureDetectionService
            patterns = self.system.process_telemetry_data(data, "comprehensive_analysis")
            
            # Only run ML-based predictions if available
            alerts = []
            if ML_AVAILABLE:
                alerts = self.system.predict_failures(data)
            
            # Generate component data for risk assessment
            # Assuming generate_component_data is available in services.failure_detection
            from services.failure_detection import generate_component_data
            components = generate_component_data(5)
            assessments = self.system.assess_risks(components)
            
            # Get summary
            summary = self.system.get_summary()
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'data_file': data_file,
                'analysis_summary': summary,
                'patterns_detected': len(patterns),
                'alerts_generated': len(alerts),
                'risk_assessments': len(assessments),
                'detailed_results': {
                    'patterns': [p.__dict__ for p in patterns],
                    'alerts': [a.__dict__ for a in alerts],
                    'assessments': [a.__dict__ for a in assessments]
                }
            }
            
            logger.info(f"Comprehensive analysis completed:")
            logger.info(f"  - Patterns detected: {len(patterns)}")
            logger.info(f"  - Alerts generated: {len(alerts)}")
            logger.info(f"  - Risk assessments: {len(assessments)}")
            
            # Save results
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                logger.info(f"Results saved to {output_file}")
            else:
                print(json.dumps(results, indent=2, default=str))
        
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
    
    def generate_sample_data(self, output_file: str, n_samples: int = 1000, failure_rate: float = 0.1) -> None:
        """Generate sample data for testing"""
        logger.info(f"Generating {n_samples} samples with {failure_rate:.1%} failure rate")
        
        try:
            # Assuming generate_failure_data is available in services.failure_detection
            from services.failure_detection import generate_failure_data
            import pandas as pd
            data = generate_failure_data(n_samples, failure_rate)
            
            if isinstance(data, pd.DataFrame):
                data.to_csv(output_file, index=False)
            else:
                # Save as JSON if pandas not available
                with open(output_file.replace('.csv', '.json'), 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Sample data saved to {output_file}")
        
        except Exception as e:
            logger.error(f"Failed to generate sample data: {e}")
    
    def save_model(self, model_file: str) -> None:
        """Save trained models"""
        try:
            # Assuming save_model is available in FailureDetectionService
            self.system.save_model(model_file)
            logger.info(f"Models saved to {model_file}")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def load_model(self, model_file: str) -> None:
        """Load trained models"""
        try:
            # Assuming load_model is available in FailureDetectionService
            self.system.load_model(model_file)
            logger.info(f"Models loaded from {model_file}")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Failure Detection CLI Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Detect anomalies command
    if ML_AVAILABLE:
        anomaly_parser = subparsers.add_parser('detect-anomalies', help='Detect anomalies in data')
        anomaly_parser.add_argument('data_file', help='Input data file (CSV)')
        anomaly_parser.add_argument('--output', help='Output file for results')
    
    # Analyze trends command
    trend_parser = subparsers.add_parser('analyze-trends', help='Analyze trends in data')
    trend_parser.add_argument('data_file', help='Input data file (CSV)')
    trend_parser.add_argument('--column', help='Specific column to analyze')
    trend_parser.add_argument('--output', help='Output file for results')
    
    # Find patterns command
    pattern_parser = subparsers.add_parser('find-patterns', help='Find repeating patterns in data')
    pattern_parser.add_argument('data_file', help='Input data file (CSV)')
    pattern_parser.add_argument('--column', help='Specific column to analyze')
    pattern_parser.add_argument('--output', help='Output file for results')
    
    # Predict failures command
    if ML_AVAILABLE:
        predict_parser = subparsers.add_parser('predict-failures', help='Predict failures in data')
        predict_parser.add_argument('data_file', help='Input data file (CSV)')
        predict_parser.add_argument('--target', default='failure', help='Target column for prediction')
        predict_parser.add_argument('--output', help='Output file for results')
    
    # Assess risks command
    risk_parser = subparsers.add_parser('assess-risks', help='Assess risks for components')
    risk_parser.add_argument('--component-file', help='Component data file (JSON)')
    risk_parser.add_argument('--output', help='Output file for results')
    
    # Comprehensive analysis command
    comprehensive_parser = subparsers.add_parser('comprehensive', help='Run comprehensive failure analysis')
    comprehensive_parser.add_argument('data_file', help='Input data file (CSV)')
    comprehensive_parser.add_argument('--output', help='Output file for results')
    
    # Generate sample data command
    sample_parser = subparsers.add_parser('generate-sample', help='Generate sample data for testing')
    sample_parser.add_argument('output_file', help='Output file for sample data')
    sample_parser.add_argument('--samples', type=int, default=1000, help='Number of samples')
    sample_parser.add_argument('--failure-rate', type=float, default=0.1, help='Failure rate')
    
    # Save model command
    if ML_AVAILABLE:
        save_parser = subparsers.add_parser('save-model', help='Save trained models')
        save_parser.add_argument('model_file', help='Model file path')
    
    # Load model command
    if ML_AVAILABLE:
        load_parser = subparsers.add_parser('load-model', help='Load trained models')
        load_parser.add_argument('model_file', help='Model file path')
    
    # Add config argument
    parser.add_argument('--config', help='Path to a YAML or JSON config file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args)
    logger.info(f"Loaded config: {config}")
    
    if not args.command:
        parser.print_help()
        return
    
    cli = FailureDetectionCLI()
    
    try:
        if args.command == 'detect-anomalies' and ML_AVAILABLE:
            cli.detect_anomalies(args.data_file, args.output)
        
        elif args.command == 'analyze-trends':
            cli.analyze_trends(args.data_file, args.column, args.output)
        
        elif args.command == 'find-patterns':
            cli.find_patterns(args.data_file, args.column, args.output)
        
        elif args.command == 'predict-failures' and ML_AVAILABLE:
            cli.predict_failures(args.data_file, args.target, args.output)
        
        elif args.command == 'assess-risks':
            cli.assess_risks(args.component_file, args.output)
        
        elif args.command == 'comprehensive':
            cli.comprehensive_analysis(args.data_file, args.output)
        
        elif args.command == 'generate-sample':
            cli.generate_sample_data(args.output_file, args.samples, args.failure_rate)
        
        elif args.command == 'save-model' and ML_AVAILABLE:
            cli.save_model(args.model_file)
        
        elif args.command == 'load-model' and ML_AVAILABLE:
            cli.load_model(args.model_file)
        
        else:
            logger.error(f"Command '{args.command}' not available or requires additional dependencies")
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 
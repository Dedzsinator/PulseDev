"""
External Dataset Integration Service for PulseDev+ AI Training

This service downloads and processes datasets from Kaggle and Hugging Face
to enhance AI model training for developer behavior analysis.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datasets import load_dataset
from huggingface_hub import hf_hub_download
import json
from datetime import datetime
import requests
from pathlib import Path

# Optional Kaggle import - will be handled at runtime
try:
    import kaggle
    KAGGLE_AVAILABLE = True
except Exception:
    KAGGLE_AVAILABLE = False
    kaggle = None

class ExternalDatasetService:
    """
    Handles downloading and processing of external datasets from:
    - Kaggle: Developer activity patterns, code repositories
    - Hugging Face: Code reasoning, debugging patterns
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.datasets_dir = "datasets"
        self.processed_dir = "processed_datasets"

        # Create directories
        os.makedirs(self.datasets_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

        # Dataset configurations
        self.kaggle_datasets = {
            'python_code_500k': {
                'name': 'jtatman/python-code-dataset-500k',
                'use_for': ['code_patterns', 'error_detection']
            },
            'github_repos': {
                'name': 'github/github-repos',
                'use_for': ['commit_patterns', 'development_cycles']
            },
            'stackoverflow_survey': {
                'name': 'stackoverflow/so-survey-2017',
                'use_for': ['developer_behavior', 'productivity_patterns']
            },
            'vscode_usage': {
                'name': 'microsoft/vscode-telemetry-data',
                'use_for': ['ide_patterns', 'workflow_analysis'],
                'fallback': True  # Use synthetic data if not available
            }
        }

        self.hf_datasets = {
            'rstar_coder': {
                'name': 'microsoft/rStar-Coder',
                'use_for': ['code_reasoning', 'debugging_patterns']
            },
            'python_codes_25k': {
                'name': 'flytech/python-codes-25k',
                'use_for': ['code_structure', 'programming_patterns']
            },
            'arxiv_code': {
                'name': 'AlgorithmicResearchGroup/arxiv_research_code',
                'use_for': ['advanced_patterns', 'research_code']
            },
            'github_issues': {
                'name': 'HuggingFaceTB/issues-kaggle-notebooks',
                'use_for': ['issue_patterns', 'problem_solving']
            }
        }

    async def download_all_datasets(self) -> Dict[str, bool]:
        """Download all configured datasets"""
        results = {}

        self.logger.info("Starting external dataset download process...")

        # Download Kaggle datasets
        for dataset_id, config in self.kaggle_datasets.items():
            try:
                success = await self._download_kaggle_dataset(dataset_id, config)
                results[f"kaggle_{dataset_id}"] = success
            except Exception as e:
                self.logger.error(f"Failed to download Kaggle dataset {dataset_id}: {str(e)}")
                results[f"kaggle_{dataset_id}"] = False

        # Download Hugging Face datasets
        for dataset_id, config in self.hf_datasets.items():
            try:
                success = await self._download_hf_dataset(dataset_id, config)
                results[f"hf_{dataset_id}"] = success
            except Exception as e:
                self.logger.error(f"Failed to download HF dataset {dataset_id}: {str(e)}")
                results[f"hf_{dataset_id}"] = False

        self.logger.info(f"Dataset download completed. Results: {results}")
        return results

    async def _download_kaggle_dataset(self, dataset_id: str, config: Dict) -> bool:
        """Download a Kaggle dataset"""
        try:
            # Check if Kaggle is available
            if not KAGGLE_AVAILABLE:
                self.logger.warning(f"Kaggle package not available, creating synthetic data for {dataset_id}")
                if config.get('fallback'):
                    return await self._create_synthetic_data(dataset_id, config)
                else:
                    return False

            # Check if Kaggle API is configured
            if not os.path.exists(os.path.expanduser('~/.kaggle/kaggle.json')):
                if config.get('fallback'):
                    self.logger.warning(f"Kaggle not configured, creating synthetic data for {dataset_id}")
                    return await self._create_synthetic_data(dataset_id, config)
                else:
                    self.logger.error(f"Kaggle API not configured for {dataset_id}")
                    return False

            dataset_name = config['name']
            download_path = os.path.join(self.datasets_dir, dataset_id)

            # Download dataset
            kaggle.api.authenticate()
            kaggle.api.dataset_download_files(dataset_name, path=download_path, unzip=True)

            self.logger.info(f"Downloaded Kaggle dataset: {dataset_name}")
            return True

        except Exception as e:
            self.logger.error(f"Kaggle download failed for {dataset_id}: {str(e)}")

            # Try fallback synthetic data
            if config.get('fallback'):
                return await self._create_synthetic_data(dataset_id, config)
            return False

    async def _download_hf_dataset(self, dataset_id: str, config: Dict) -> bool:
        """Download a Hugging Face dataset"""
        try:
            dataset_name = config['name']

            # Load dataset from Hugging Face
            dataset = load_dataset(dataset_name, split='train', streaming=True)

            # Sample and save a manageable subset
            sample_data = []
            for i, example in enumerate(dataset):
                if i >= 10000:  # Limit to 10k examples
                    break
                sample_data.append(example)

            # Save processed data
            save_path = os.path.join(self.processed_dir, f"{dataset_id}.json")
            with open(save_path, 'w') as f:
                json.dump(sample_data, f, indent=2, default=str)

            self.logger.info(f"Downloaded and processed HF dataset: {dataset_name}")
            return True

        except Exception as e:
            self.logger.error(f"HF download failed for {dataset_id}: {str(e)}")
            return False

    async def _create_synthetic_data(self, dataset_id: str, config: Dict) -> bool:
        """Create synthetic dataset when external data unavailable"""
        try:
            synthetic_data = []

            if dataset_id == 'vscode_usage':
                # Generate synthetic VSCode usage patterns
                for i in range(5000):
                    synthetic_data.append({
                        'timestamp': (datetime.now().timestamp() - i * 300),  # Every 5 minutes
                        'action': np.random.choice(['file_edit', 'debug_start', 'test_run', 'git_commit']),
                        'duration_ms': np.random.randint(1000, 300000),
                        'file_type': np.random.choice(['py', 'js', 'ts', 'json', 'md']),
                        'productivity_score': np.random.uniform(0.3, 1.0),
                        'errors_count': np.random.poisson(0.5),
                        'context_switches': np.random.poisson(2.0)
                    })
            else:
                # Generic synthetic data
                for i in range(1000):
                    synthetic_data.append({
                        'id': i,
                        'pattern_type': np.random.choice(['productive', 'stuck', 'flow', 'distracted']),
                        'activity_score': np.random.uniform(0, 1),
                        'duration': np.random.randint(60, 7200),  # 1min to 2hrs
                        'complexity': np.random.uniform(0, 1)
                    })

            # Save synthetic data
            save_path = os.path.join(self.processed_dir, f"synthetic_{dataset_id}.json")
            with open(save_path, 'w') as f:
                json.dump(synthetic_data, f, indent=2, default=str)

            self.logger.info(f"Created synthetic dataset for: {dataset_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create synthetic data for {dataset_id}: {str(e)}")
            return False

    async def process_datasets_for_training(self) -> Dict[str, Any]:
        """Process all datasets into training-ready format"""
        training_data = {
            'stuck_detection': [],
            'flow_prediction': [],
            'productivity_patterns': [],
            'code_quality': []
        }

        # Process each dataset type
        await self._process_productivity_patterns(training_data)
        await self._process_code_patterns(training_data)
        await self._process_behavior_patterns(training_data)

        return training_data

    async def _process_productivity_patterns(self, training_data: Dict[str, Any]):
        """Extract productivity patterns from datasets"""

        # Process Stack Overflow survey data
        so_path = os.path.join(self.processed_dir, "stackoverflow_survey.json")
        if os.path.exists(so_path):
            try:
                with open(so_path, 'r') as f:
                    so_data = json.load(f)

                for entry in so_data[:1000]:  # Sample
                    # Extract productivity indicators
                    features = self._extract_productivity_features(entry)
                    if features:
                        training_data['productivity_patterns'].append(features)

            except Exception as e:
                self.logger.error(f"Error processing SO data: {str(e)}")

        # Process synthetic VSCode data
        vscode_path = os.path.join(self.processed_dir, "synthetic_vscode_usage.json")
        if os.path.exists(vscode_path):
            try:
                with open(vscode_path, 'r') as f:
                    vscode_data = json.load(f)

                for entry in vscode_data:
                    features = {
                        'session_duration': entry.get('duration_ms', 0) / 1000,
                        'productivity_score': entry.get('productivity_score', 0.5),
                        'errors_count': entry.get('errors_count', 0),
                        'context_switches': entry.get('context_switches', 0),
                        'action_type': entry.get('action', 'unknown'),
                        'is_productive': entry.get('productivity_score', 0.5) > 0.7
                    }
                    training_data['productivity_patterns'].append(features)

            except Exception as e:
                self.logger.error(f"Error processing VSCode synthetic data: {str(e)}")

    async def _process_code_patterns(self, training_data: Dict[str, Any]):
        """Extract code quality and debugging patterns"""

        # Process Hugging Face code datasets
        for dataset_name in ['rstar_coder', 'python_codes_25k']:
            dataset_path = os.path.join(self.processed_dir, f"{dataset_name}.json")
            if os.path.exists(dataset_path):
                try:
                    with open(dataset_path, 'r') as f:
                        code_data = json.load(f)

                    for entry in code_data[:500]:  # Sample
                        features = self._extract_code_features(entry)
                        if features:
                            training_data['code_quality'].append(features)

                except Exception as e:
                    self.logger.error(f"Error processing {dataset_name}: {str(e)}")

    async def _process_behavior_patterns(self, training_data: Dict[str, Any]):
        """Extract stuck state and flow patterns"""

        # Use synthetic data to create behavior patterns
        for i in range(2000):
            # Create flow state patterns
            is_flow = np.random.random() > 0.7  # 30% in flow

            flow_features = {
                'typing_rhythm': np.random.uniform(0.2, 1.0) if is_flow else np.random.uniform(0.0, 0.6),
                'context_switches': np.random.poisson(1.0) if is_flow else np.random.poisson(5.0),
                'error_rate': np.random.uniform(0.0, 0.1) if is_flow else np.random.uniform(0.1, 0.5),
                'session_duration': np.random.uniform(30, 180) if is_flow else np.random.uniform(5, 60),
                'test_frequency': np.random.uniform(0.1, 0.3) if is_flow else np.random.uniform(0.0, 0.1),
                'is_flow': is_flow
            }

            training_data['flow_prediction'].append(flow_features)

            # Create stuck state patterns
            is_stuck = np.random.random() > 0.8  # 20% stuck

            stuck_features = {
                'repeated_edits': np.random.poisson(10.0) if is_stuck else np.random.poisson(2.0),
                'error_frequency': np.random.uniform(0.3, 0.8) if is_stuck else np.random.uniform(0.0, 0.2),
                'idle_time': np.random.uniform(5, 30) if is_stuck else np.random.uniform(0, 5),
                'help_seeking': np.random.poisson(3.0) if is_stuck else np.random.poisson(0.5),
                'progress_rate': np.random.uniform(0.0, 0.2) if is_stuck else np.random.uniform(0.3, 1.0),
                'is_stuck': is_stuck
            }

            training_data['stuck_detection'].append(stuck_features)

    def _extract_productivity_features(self, entry: Dict) -> Optional[Dict]:
        """Extract features from productivity data entry"""
        try:
            # This would be customized based on actual dataset structure
            return {
                'experience_years': entry.get('YearsCodePro', 0),
                'hours_per_week': entry.get('HoursComputer', 40),
                'job_satisfaction': entry.get('JobSatisfaction', 3),
                'productivity_tools': len(entry.get('IDE', '').split(';')),
                'team_size': entry.get('TeamSize', 5)
            }
        except:
            return None

    def _extract_code_features(self, entry: Dict) -> Optional[Dict]:
        """Extract features from code data entry"""
        try:
            code = entry.get('code', '') or entry.get('text', '')

            if not code:
                return None

            return {
                'code_length': len(code),
                'complexity_score': len([c for c in code if c in '(){}[]']) / max(len(code), 1),
                'comment_ratio': code.count('#') / max(len(code.split('\n')), 1),
                'function_count': code.count('def '),
                'class_count': code.count('class '),
                'import_count': code.count('import '),
                'has_errors': 'error' in entry.get('output', '').lower() if 'output' in entry else False,
                'language': entry.get('language', 'python')
            }
        except:
            return None

    async def get_training_data(self, data_type: str) -> List[Dict]:
        """Get processed training data for a specific model type"""

        if not hasattr(self, '_processed_data'):
            self._processed_data = await self.process_datasets_for_training()

        return self._processed_data.get(data_type, [])

    def get_dataset_status(self) -> Dict[str, Dict]:
        """Get status of all datasets"""
        status = {}

        # Check Kaggle datasets
        for dataset_id in self.kaggle_datasets:
            dataset_path = os.path.join(self.datasets_dir, dataset_id)
            synthetic_path = os.path.join(self.processed_dir, f"synthetic_{dataset_id}.json")

            status[f"kaggle_{dataset_id}"] = {
                'downloaded': os.path.exists(dataset_path),
                'synthetic_available': os.path.exists(synthetic_path),
                'last_updated': self._get_last_modified(dataset_path) or self._get_last_modified(synthetic_path)
            }

        # Check Hugging Face datasets
        for dataset_id in self.hf_datasets:
            dataset_path = os.path.join(self.processed_dir, f"{dataset_id}.json")

            status[f"hf_{dataset_id}"] = {
                'downloaded': os.path.exists(dataset_path),
                'synthetic_available': False,
                'last_updated': self._get_last_modified(dataset_path)
            }

        return status

    def _get_last_modified(self, path: str) -> Optional[str]:
        """Get last modified time of file"""
        try:
            if os.path.exists(path):
                timestamp = os.path.getmtime(path)
                return datetime.fromtimestamp(timestamp).isoformat()
        except:
            pass
        return None

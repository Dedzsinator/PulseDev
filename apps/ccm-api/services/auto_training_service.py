import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncpg
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
from config import Config
from models.events import ContextEvent
from .external_dataset_service import ExternalDatasetService

class AutoTrainingService:
    """
    Handles automatic training of AI models during low usage periods.
    Trains models for:
    1. Stuck state detection
    2. Flow state prediction
    3. Code pattern recognition
    4. Productivity optimization
    """

    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.models_dir = "models"
        self.is_training = False
        self.last_training = None

        # Initialize external dataset service
        self.external_datasets = ExternalDatasetService()

        # Initialize improved models
        self.stuck_classifier = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=8,
            random_state=42
        )
        self.flow_predictor = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            n_estimators=100,
            random_state=42
        )
        self.productivity_predictor = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            random_state=42
        )

        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()

        os.makedirs(self.models_dir, exist_ok=True)

    async def should_start_training(self, db: asyncpg.Connection) -> bool:
        """Check if training should start based on usage patterns"""

        # Check if already training
        if self.is_training:
            return False

        # Check last training time (don't train more than once per day)
        if self.last_training and datetime.utcnow() - self.last_training < timedelta(hours=12):
            return False

        # Check current activity level
        recent_events = await db.fetch("""
            SELECT COUNT(*) as count
            FROM context_events
            WHERE timestamp > $1
        """, datetime.utcnow() - timedelta(hours=1))

        current_activity = recent_events[0]['count'] if recent_events else 0

        # Start training if low activity (< 10 events in last hour)
        return current_activity < 10

    async def collect_training_data(self, db: asyncpg.Connection) -> Dict[str, Any]:
        """Collect training data from both internal sources and external datasets"""

        self.logger.info("Collecting comprehensive training data...")

        # Get internal data from last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        events = await db.fetch("""
            SELECT session_id, agent, type, payload, timestamp,
                   EXTRACT(HOUR FROM timestamp) as hour,
                   EXTRACT(DOW FROM timestamp) as day_of_week
            FROM context_events
            WHERE timestamp > $1
            ORDER BY timestamp
        """, cutoff_date)

        # Get flow states and stuck states
        flow_states = await db.fetch("""
            SELECT session_id, state, insights, timestamp
            FROM flow_states
            WHERE timestamp > $1
        """, cutoff_date)

        # Get energy scores
        energy_scores = await db.fetch("""
            SELECT session_id, score, factors, timestamp
            FROM energy_scores
            WHERE timestamp > $1
        """, cutoff_date)

        internal_data = {
            'events': [dict(row) for row in events],
            'flow_states': [dict(row) for row in flow_states],
            'energy_scores': [dict(row) for row in energy_scores]
        }

        # Download and process external datasets if not already available
        self.logger.info("Checking external datasets...")
        dataset_status = self.external_datasets.get_dataset_status()

        # Download datasets if needed (only if not already downloaded)
        needs_download = any(
            not status.get('downloaded', False) and not status.get('synthetic_available', False)
            for status in dataset_status.values()
        )

        if needs_download:
            self.logger.info("Downloading missing external datasets...")
            await self.external_datasets.download_all_datasets()

        # Get processed external training data
        external_data = await self.external_datasets.process_datasets_for_training()

        # Combine internal and external data
        combined_data = {
            **internal_data,
            'external_stuck_patterns': external_data.get('stuck_detection', []),
            'external_flow_patterns': external_data.get('flow_prediction', []),
            'external_productivity_patterns': external_data.get('productivity_patterns', []),
            'external_code_quality': external_data.get('code_quality', [])
        }

        self.logger.info(f"Collected training data: {len(combined_data['events'])} internal events, "
                        f"{len(external_data.get('stuck_detection', []))} external stuck patterns, "
                        f"{len(external_data.get('flow_prediction', []))} external flow patterns")

        return combined_data

    def extract_features(self, events: List[Dict]) -> np.ndarray:
        """Extract features from events for ML training"""

        features = []

        # Group events by session
        sessions = {}
        for event in events:
            session_id = event['session_id']
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(event)

        for session_id, session_events in sessions.items():
            session_features = self._extract_session_features(session_events)
            features.append(session_features)

        return np.array(features)

    def _extract_session_features(self, events: List[Dict]) -> List[float]:
        """Extract features for a single session"""

        if not events:
            return [0] * 20  # Return zero features if no events

        # Basic statistics
        total_events = len(events)
        duration_hours = 0

        if len(events) > 1:
            start_time = min(event['timestamp'] for event in events)
            end_time = max(event['timestamp'] for event in events)
            duration_hours = (end_time - start_time).total_seconds() / 3600

        # Event type counts
        event_types = {}
        agents = {}

        for event in events:
            event_type = event['type']
            agent = event['agent']

            event_types[event_type] = event_types.get(event_type, 0) + 1
            agents[agent] = agents.get(agent, 0) + 1

        # Calculate activity patterns
        file_events = event_types.get('file_modified', 0)
        test_events = event_types.get('test_run', 0)
        git_events = event_types.get('commit_created', 0)
        error_events = event_types.get('error_occurred', 0)

        # Calculate ratios
        test_file_ratio = test_events / max(file_events, 1)
        error_rate = error_events / max(total_events, 1)
        git_activity = git_events / max(duration_hours, 0.1)

        # Time-based features
        hour_distribution = [0] * 24
        for event in events:
            hour = event.get('hour', 0)
            if hour is not None:
                hour_distribution[int(hour)] += 1

        peak_hour_activity = max(hour_distribution) / max(total_events, 1)

        # Productivity indicators
        commits_per_hour = git_events / max(duration_hours, 0.1)
        events_per_hour = total_events / max(duration_hours, 0.1)

        return [
            total_events,
            duration_hours,
            file_events,
            test_events,
            git_events,
            error_events,
            test_file_ratio,
            error_rate,
            git_activity,
            peak_hour_activity,
            commits_per_hour,
            events_per_hour,
            agents.get('file', 0),
            agents.get('editor', 0),
            agents.get('terminal', 0),
            agents.get('git', 0),
            len(set(event['type'] for event in events)),  # event type diversity
            len(hour_distribution) - hour_distribution.count(0),  # active hours
            max(hour_distribution),  # peak activity
            np.std([event_types.get(t, 0) for t in event_types])  # activity variance
        ]

    async def train_stuck_detection_model(self, data: Dict[str, Any]):
        """Train the stuck state detection model with enhanced features"""

        self.logger.info("Training enhanced stuck detection model...")

        # Combine internal and external data
        internal_features = self.extract_features(data['events'])
        external_patterns = data.get('external_stuck_patterns', [])

        all_features = []
        all_labels = []

        # Process internal data
        if len(internal_features) > 0:
            sessions = {}
            for event in data['events']:
                session_id = event['session_id']
                if session_id not in sessions:
                    sessions[session_id] = []
                sessions[session_id].append(event)

            for session_id, events in sessions.items():
                session_features = self._extract_session_features(events)
                all_features.append(session_features)

                # Detect stuck patterns
                is_stuck = self._detect_stuck_patterns(events)
                all_labels.append(1 if is_stuck else 0)

        # Process external patterns
        for pattern in external_patterns:
            if isinstance(pattern, dict) and 'is_stuck' in pattern:
                # Convert external pattern to feature vector
                external_features = self._convert_external_to_features(pattern, 'stuck')
                if external_features:
                    all_features.append(external_features)
                    all_labels.append(1 if pattern['is_stuck'] else 0)

        if len(all_features) == 0 or len(set(all_labels)) < 2:
            self.logger.warning("Insufficient data for stuck detection training")
            return

        # Convert to numpy arrays
        X = np.array(all_features)
        y = np.array(all_labels)

        # Split data for validation
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model with cross-validation
        cv_scores = cross_val_score(self.stuck_classifier, X_train_scaled, y_train, cv=5)
        self.logger.info(f"Cross-validation accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

        # Train final model
        self.stuck_classifier.fit(X_train_scaled, y_train)

        # Evaluate model
        y_pred = self.stuck_classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        self.logger.info(f"Test accuracy: {accuracy:.3f}")

        # Save model with metadata
        model_path = os.path.join(self.models_dir, "stuck_classifier.joblib")
        joblib.dump({
            'classifier': self.stuck_classifier,
            'scaler': self.scaler,
            'accuracy': accuracy,
            'cv_scores': cv_scores.tolist(),
            'training_samples': len(X_train),
            'external_samples': len(external_patterns),
            'trained_at': datetime.utcnow().isoformat()
        }, model_path)

        self.logger.info(f"Enhanced stuck detection model saved to {model_path}")

    def _convert_external_to_features(self, pattern: Dict, model_type: str) -> Optional[List[float]]:
        """Convert external dataset pattern to internal feature format"""

        if model_type == 'stuck':
            try:
                return [
                    pattern.get('repeated_edits', 0),
                    pattern.get('error_frequency', 0) * 100,  # Scale to match internal
                    pattern.get('idle_time', 0) * 60,  # Convert to seconds
                    pattern.get('help_seeking', 0),
                    pattern.get('progress_rate', 0.5) * 100,
                    1.0 - pattern.get('progress_rate', 0.5),  # Inverse progress
                    pattern.get('repeated_edits', 0) / 10.0,  # Normalized
                    float(pattern.get('error_frequency', 0) > 0.3),  # High error indicator
                    float(pattern.get('progress_rate', 0.5) < 0.3),  # Low progress indicator
                    pattern.get('help_seeking', 0) / 5.0,  # Normalized help seeking
                    # Pad remaining features with defaults to match expected length
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0  # 10 additional features
                ]
            except Exception as e:
                self.logger.error(f"Error converting stuck pattern: {e}")
                return None

        elif model_type == 'flow':
            try:
                return [
                    pattern.get('typing_rhythm', 0.5) * 100,
                    pattern.get('context_switches', 2),
                    pattern.get('error_rate', 0.1) * 100,
                    pattern.get('session_duration', 30),
                    pattern.get('test_frequency', 0.1) * 100,
                    100.0 - (pattern.get('context_switches', 2) * 10),  # Focus score
                    pattern.get('typing_rhythm', 0.5) * pattern.get('session_duration', 30),  # Momentum
                    float(pattern.get('error_rate', 0.1) < 0.1),  # Low error indicator
                    float(pattern.get('typing_rhythm', 0.5) > 0.7),  # High rhythm
                    float(pattern.get('session_duration', 30) > 60),  # Long session
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0  # Additional features
                ]
            except Exception as e:
                self.logger.error(f"Error converting flow pattern: {e}")
                return None

        return None

    def _detect_stuck_patterns(self, events: List[Dict]) -> bool:
        """Detect if a session shows stuck patterns"""

        # Pattern 1: High error rate
        error_events = sum(1 for e in events if 'error' in str(e.get('payload', '')).lower())
        error_rate = error_events / max(len(events), 1)

        if error_rate > 0.3:  # More than 30% errors
            return True

        # Pattern 2: Repetitive file edits without progress
        file_edits = {}
        for event in events:
            if event['type'] == 'file_modified':
                file_path = event.get('payload', {}).get('file_path')
                if file_path:
                    file_edits[file_path] = file_edits.get(file_path, 0) + 1

        # Check for files edited many times
        for file_path, edit_count in file_edits.items():
            if edit_count > 10:  # Same file edited 10+ times
                return True

        # Pattern 3: Long session with no commits
        duration_hours = 0
        if len(events) > 1:
            start_time = min(event['timestamp'] for event in events)
            end_time = max(event['timestamp'] for event in events)
            duration_hours = (end_time - start_time).total_seconds() / 3600

        git_events = sum(1 for e in events if e['agent'] == 'git')

        if duration_hours > 2 and git_events == 0:  # 2+ hours with no commits
            return True

        return False

    async def train_flow_prediction_model(self, data: Dict[str, Any]):
        """Train the flow state prediction model with external data"""

        self.logger.info("Training enhanced flow prediction model...")

        # Combine internal flow states with external patterns
        all_features = []
        all_labels = []

        # Process internal flow states
        if data.get('flow_states'):
            for flow_state in data['flow_states']:
                # Get events leading up to this flow state
                session_events = [
                    e for e in data['events']
                    if e['session_id'] == flow_state['session_id']
                    and e['timestamp'] <= flow_state['timestamp']
                ]

                if session_events:
                    session_features = self._extract_session_features(session_events)
                    all_features.append(session_features)

                    # Label based on flow state
                    state = flow_state['state']
                    flow_label = 1 if state in ['deep_focus', 'flow'] else 0
                    all_labels.append(flow_label)

        # Process external flow patterns
        external_patterns = data.get('external_flow_patterns', [])
        for pattern in external_patterns:
            if isinstance(pattern, dict) and 'is_flow' in pattern:
                external_features = self._convert_external_to_features(pattern, 'flow')
                if external_features:
                    all_features.append(external_features)
                    all_labels.append(1 if pattern['is_flow'] else 0)

        if len(all_features) == 0 or len(set(all_labels)) < 2:
            self.logger.warning("Insufficient data for flow prediction training")
            return

        # Convert to numpy arrays
        X = np.array(all_features)
        y = np.array(all_labels)

        # Split and scale data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train with cross-validation
        cv_scores = cross_val_score(self.flow_predictor, X_train_scaled, y_train, cv=5)
        self.logger.info(f"Flow prediction CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

        # Train final model
        self.flow_predictor.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.flow_predictor.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        self.logger.info(f"Flow prediction test accuracy: {accuracy:.3f}")

        # Save enhanced model
        model_path = os.path.join(self.models_dir, "flow_predictor.joblib")
        joblib.dump({
            'predictor': self.flow_predictor,
            'scaler': self.scaler,
            'accuracy': accuracy,
            'cv_scores': cv_scores.tolist(),
            'training_samples': len(X_train),
            'external_samples': len(external_patterns),
            'trained_at': datetime.utcnow().isoformat()
        }, model_path)

        self.logger.info(f"Enhanced flow prediction model saved to {model_path}")

    async def train_productivity_model(self, data: Dict[str, Any]):
        """Train productivity prediction model using external productivity patterns"""

        self.logger.info("Training productivity prediction model...")

        # Get external productivity patterns
        productivity_patterns = data.get('external_productivity_patterns', [])

        if len(productivity_patterns) < 10:
            self.logger.warning("Insufficient productivity data for training")
            return

        features = []
        labels = []

        for pattern in productivity_patterns:
            try:
                # Extract features from productivity pattern
                feature_vector = [
                    pattern.get('experience_years', 0),
                    pattern.get('hours_per_week', 40) / 40.0,  # Normalize
                    pattern.get('job_satisfaction', 3) / 5.0,  # Normalize to 0-1
                    pattern.get('productivity_tools', 1),
                    pattern.get('team_size', 5) / 10.0,  # Normalize
                    pattern.get('session_duration', 0) / 3600.0,  # Hours
                    pattern.get('productivity_score', 0.5),
                    pattern.get('errors_count', 0) / 10.0,  # Normalize
                    pattern.get('context_switches', 0) / 10.0,  # Normalize
                    float(pattern.get('productivity_score', 0.5) > 0.7)  # High productivity flag
                ]

                # Label: high productivity (>0.7) vs normal/low productivity
                is_productive = pattern.get('is_productive', pattern.get('productivity_score', 0.5) > 0.7)

                features.append(feature_vector)
                labels.append(1 if is_productive else 0)

            except Exception as e:
                self.logger.error(f"Error processing productivity pattern: {e}")
                continue

        if len(features) == 0 or len(set(labels)) < 2:
            self.logger.warning("Insufficient valid productivity data")
            return

        # Train productivity model
        X = np.array(features)
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train with cross-validation
        cv_scores = cross_val_score(self.productivity_predictor, X_train_scaled, y_train, cv=5)
        self.logger.info(f"Productivity CV accuracy: {cv_scores.mean():.3f}")

        self.productivity_predictor.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.productivity_predictor.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        self.logger.info(f"Productivity test accuracy: {accuracy:.3f}")

        # Save model
        model_path = os.path.join(self.models_dir, "productivity_predictor.joblib")
        joblib.dump({
            'predictor': self.productivity_predictor,
            'scaler': self.scaler,
            'accuracy': accuracy,
            'cv_scores': cv_scores.tolist(),
            'training_samples': len(X_train),
            'trained_at': datetime.utcnow().isoformat()
        }, model_path)

        self.logger.info(f"Productivity prediction model saved to {model_path}")

    async def train_anomaly_detection_model(self, data: Dict[str, Any]):
        """Train enhanced anomaly detection for unusual coding patterns"""

        self.logger.info("Training enhanced anomaly detection model...")

        # Combine internal and external features
        all_features = []

        # Internal features
        internal_features = self.extract_features(data['events'])
        if len(internal_features) > 0:
            all_features.extend(internal_features.tolist())

        # External features from various patterns
        for pattern_type in ['external_stuck_patterns', 'external_flow_patterns', 'external_productivity_patterns']:
            patterns = data.get(pattern_type, [])
            for pattern in patterns:
                if isinstance(pattern, dict):
                    # Convert pattern to feature vector for anomaly detection
                    feature_vector = self._extract_anomaly_features(pattern, pattern_type)
                    if feature_vector:
                        all_features.append(feature_vector)

        if len(all_features) < 10:  # Need minimum samples for anomaly detection
            self.logger.warning("Insufficient data for anomaly detection training")
            return

        X = np.array(all_features)

        # Pad features to consistent length
        max_features = max(len(f) for f in X)
        X_padded = []
        for feature_vec in X:
            padded = list(feature_vec) + [0] * (max_features - len(feature_vec))
            X_padded.append(padded[:max_features])  # Truncate if too long

        X_final = np.array(X_padded)

        # Scale features
        X_scaled = self.scaler.fit_transform(X_final)

        # Train anomaly detector
        self.anomaly_detector.fit(X_scaled)

        # Evaluate by checking some samples
        anomaly_scores = self.anomaly_detector.decision_function(X_scaled)
        anomaly_threshold = np.percentile(anomaly_scores, 10)  # Bottom 10% are anomalies

        # Save model with metadata
        model_path = os.path.join(self.models_dir, "anomaly_detector.joblib")
        joblib.dump({
            'detector': self.anomaly_detector,
            'scaler': self.scaler,
            'anomaly_threshold': anomaly_threshold,
            'training_samples': len(X_final),
            'feature_dimensions': max_features,
            'trained_at': datetime.utcnow().isoformat()
        }, model_path)

        self.logger.info(f"Enhanced anomaly detection model saved to {model_path}")

    def _extract_anomaly_features(self, pattern: Dict, pattern_type: str) -> Optional[List[float]]:
        """Extract features for anomaly detection from different pattern types"""

        try:
            if 'stuck' in pattern_type:
                return [
                    pattern.get('repeated_edits', 0),
                    pattern.get('error_frequency', 0),
                    pattern.get('idle_time', 0),
                    pattern.get('help_seeking', 0),
                    pattern.get('progress_rate', 0.5)
                ]
            elif 'flow' in pattern_type:
                return [
                    pattern.get('typing_rhythm', 0.5),
                    pattern.get('context_switches', 2),
                    pattern.get('error_rate', 0.1),
                    pattern.get('session_duration', 30),
                    pattern.get('test_frequency', 0.1)
                ]
            elif 'productivity' in pattern_type:
                return [
                    pattern.get('productivity_score', 0.5),
                    pattern.get('session_duration', 0) / 3600.0,
                    pattern.get('errors_count', 0),
                    pattern.get('context_switches', 0),
                    pattern.get('experience_years', 0) / 10.0  # Normalize
                ]
        except Exception as e:
            self.logger.error(f"Error extracting anomaly features: {e}")

        return None

    async def auto_train(self, db: asyncpg.Connection):
        """Main auto-training function"""

        if not await self.should_start_training(db):
            return

        self.logger.info("Starting auto-training process...")
        self.is_training = True

        try:
            # Collect training data
            data = await self.collect_training_data(db)

            if not data['events']:
                self.logger.warning("No training data available")
                return

            # Train models with external data
            await self.train_stuck_detection_model(data)
            await self.train_flow_prediction_model(data)
            await self.train_anomaly_detection_model(data)
            await self.train_productivity_model(data)  # New model

            # Update training timestamp
            self.last_training = datetime.utcnow()

            # Log training completion
            await db.execute("""
                INSERT INTO ai_training_logs (timestamp, models_trained, data_points, success)
                VALUES ($1, $2, $3, $4)
            """,
                datetime.utcnow(),
                json.dumps(['stuck_classifier', 'flow_predictor', 'anomaly_detector', 'productivity_predictor']),
                len(data['events']),
                True
            )

            self.logger.info("Auto-training completed successfully")

        except Exception as e:
            self.logger.error(f"Auto-training failed: {str(e)}")

            # Log training failure
            await db.execute("""
                INSERT INTO ai_training_logs (timestamp, models_trained, data_points, success, error_message)
                VALUES ($1, $2, $3, $4, $5)
            """,
                datetime.utcnow(),
                json.dumps([]),
                0,
                False,
                str(e)
            )

        finally:
            self.is_training = False

    def load_trained_models(self):
        """Load previously trained models"""

        models = ['stuck_classifier', 'flow_predictor', 'anomaly_detector', 'productivity_predictor']

        for model_name in models:
            model_path = os.path.join(self.models_dir, f"{model_name}.joblib")

            if os.path.exists(model_path):
                try:
                    loaded = joblib.load(model_path)

                    if model_name == 'stuck_classifier':
                        self.stuck_classifier = loaded['classifier']
                    elif model_name == 'flow_predictor':
                        self.flow_predictor = loaded['predictor']
                    elif model_name == 'anomaly_detector':
                        self.anomaly_detector = loaded['detector']
                    elif model_name == 'productivity_predictor':
                        self.productivity_predictor = loaded['predictor']

                    self.scaler = loaded['scaler']

                    # Log model metadata if available
                    accuracy = loaded.get('accuracy', 'unknown')
                    training_samples = loaded.get('training_samples', 'unknown')
                    self.logger.info(f"Loaded {model_name}: accuracy={accuracy}, samples={training_samples}")

                except Exception as e:
                    self.logger.error(f"Failed to load {model_name}: {str(e)}")
            else:
                self.logger.warning(f"Model file not found: {model_path}")

    async def predict_productivity(self, session_events: List[Dict]) -> float:
        """Predict productivity level for current session"""

        if not session_events:
            return 0.5

        try:
            # Extract productivity-related features
            features = [
                len(session_events) / 100.0,  # Activity level
                len([e for e in session_events if e.get('type') == 'test_run']) / max(len(session_events), 1),
                len([e for e in session_events if 'error' in str(e.get('payload', ''))]) / max(len(session_events), 1),
                len(set(e.get('type') for e in session_events)) / 10.0,  # Variety of activities
                0.5,  # Placeholder for session duration ratio
                0.0,  # Placeholder for experience years (not available)
                0.7,  # Default job satisfaction
                5.0 / 10.0,  # Default team size
                1.0,  # Default productivity tools
                0.0   # High productivity flag (will be predicted)
            ]

            features_scaled = self.scaler.transform([features])
            prob = self.productivity_predictor.predict_proba(features_scaled)[0][1]
            return float(prob)

        except Exception as e:
            self.logger.error(f"Productivity prediction failed: {str(e)}")
            return 0.5

    async def predict_stuck_state(self, session_events: List[Dict]) -> float:
        """Predict probability of stuck state for current session"""

        if not session_events:
            return 0.0

        try:
            features = np.array([self._extract_session_features(session_events)])
            features_scaled = self.scaler.transform(features)

            # Get probability of stuck state (class 1)
            prob = self.stuck_classifier.predict_proba(features_scaled)[0][1]
            return float(prob)

        except Exception as e:
            self.logger.error(f"Stuck state prediction failed: {str(e)}")
            return 0.0

    async def predict_flow_state(self, session_events: List[Dict]) -> float:
        """Predict probability of entering flow state"""

        if not session_events:
            return 0.0

        try:
            features = np.array([self._extract_session_features(session_events)])
            features_scaled = self.scaler.transform(features)

            # Get probability of flow state (class 1)
            prob = self.flow_predictor.predict_proba(features_scaled)[0][1]
            return float(prob)

        except Exception as e:
            self.logger.error(f"Flow state prediction failed: {str(e)}")
            return 0.0

    async def detect_anomaly(self, session_events: List[Dict]) -> float:
        """Detect anomalous coding patterns"""

        if not session_events:
            return 0.0

        try:
            features = np.array([self._extract_session_features(session_events)])
            features_scaled = self.scaler.transform(features)

            # Get anomaly score (lower is more anomalous)
            score = self.anomaly_detector.decision_function(features_scaled)[0]

            # Convert to probability (0 = normal, 1 = anomalous)
            anomaly_prob = max(0, min(1, (0.5 - score) * 2))
            return float(anomaly_prob)

        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {str(e)}")
            return 0.0

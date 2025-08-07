import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncpg
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import joblib
import os
from ..config import Config
from ..models.events import ContextEvent

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
        
        # Initialize models
        self.stuck_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.flow_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        
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
        """Collect training data from the database"""
        
        self.logger.info("Collecting training data...")
        
        # Get events from last 30 days
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
        
        return {
            'events': [dict(row) for row in events],
            'flow_states': [dict(row) for row in flow_states],
            'energy_scores': [dict(row) for row in energy_scores]
        }
        
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
        """Train the stuck state detection model"""
        
        self.logger.info("Training stuck detection model...")
        
        features = self.extract_features(data['events'])
        
        if len(features) == 0:
            self.logger.warning("No features extracted for stuck detection training")
            return
            
        # Create labels based on patterns
        labels = []
        sessions = {}
        
        for event in data['events']:
            session_id = event['session_id']
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(event)
            
        for session_id, events in sessions.items():
            # Detect stuck patterns
            is_stuck = self._detect_stuck_patterns(events)
            labels.append(1 if is_stuck else 0)
            
        if len(set(labels)) < 2:
            self.logger.warning("Not enough label diversity for training")
            return
            
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.stuck_classifier.fit(features_scaled, labels)
        
        # Save model
        model_path = os.path.join(self.models_dir, "stuck_classifier.joblib")
        joblib.dump({
            'classifier': self.stuck_classifier,
            'scaler': self.scaler
        }, model_path)
        
        self.logger.info(f"Stuck detection model saved to {model_path}")
        
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
        """Train the flow state prediction model"""
        
        self.logger.info("Training flow prediction model...")
        
        if not data['flow_states']:
            self.logger.warning("No flow state data available for training")
            return
            
        # Create features and labels from flow states
        features = []
        labels = []
        
        for flow_state in data['flow_states']:
            # Get events leading up to this flow state
            session_events = [
                e for e in data['events'] 
                if e['session_id'] == flow_state['session_id'] 
                and e['timestamp'] <= flow_state['timestamp']
            ]
            
            if session_events:
                session_features = self._extract_session_features(session_events)
                features.append(session_features)
                
                # Label based on flow state
                state = flow_state['state']
                flow_label = 1 if state in ['deep_focus', 'flow'] else 0
                labels.append(flow_label)
                
        if len(features) == 0 or len(set(labels)) < 2:
            self.logger.warning("Insufficient data for flow prediction training")
            return
            
        features = np.array(features)
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.flow_predictor.fit(features_scaled, labels)
        
        # Save model
        model_path = os.path.join(self.models_dir, "flow_predictor.joblib")
        joblib.dump({
            'predictor': self.flow_predictor,
            'scaler': self.scaler
        }, model_path)
        
        self.logger.info(f"Flow prediction model saved to {model_path}")
        
    async def train_anomaly_detection_model(self, data: Dict[str, Any]):
        """Train anomaly detection for unusual coding patterns"""
        
        self.logger.info("Training anomaly detection model...")
        
        features = self.extract_features(data['events'])
        
        if len(features) < 10:  # Need minimum samples for anomaly detection
            self.logger.warning("Insufficient data for anomaly detection training")
            return
            
        features_scaled = self.scaler.fit_transform(features)
        
        # Train anomaly detector
        self.anomaly_detector.fit(features_scaled)
        
        # Save model
        model_path = os.path.join(self.models_dir, "anomaly_detector.joblib")
        joblib.dump({
            'detector': self.anomaly_detector,
            'scaler': self.scaler
        }, model_path)
        
        self.logger.info(f"Anomaly detection model saved to {model_path}")
        
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
                
            # Train models
            await self.train_stuck_detection_model(data)
            await self.train_flow_prediction_model(data)
            await self.train_anomaly_detection_model(data)
            
            # Update training timestamp
            self.last_training = datetime.utcnow()
            
            # Log training completion
            await db.execute("""
                INSERT INTO ai_training_logs (timestamp, models_trained, data_points, success)
                VALUES ($1, $2, $3, $4)
            """, 
                datetime.utcnow(),
                json.dumps(['stuck_classifier', 'flow_predictor', 'anomaly_detector']),
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
        
        models = ['stuck_classifier', 'flow_predictor', 'anomaly_detector']
        
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
                        
                    self.scaler = loaded['scaler']
                    self.logger.info(f"Loaded {model_name} from {model_path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load {model_name}: {str(e)}")
                    
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
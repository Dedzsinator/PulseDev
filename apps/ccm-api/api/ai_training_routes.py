"""
AI Training Management Routes for PulseDev+

These routes handle AI model training, dataset management, and model performance monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncpg
from datetime import datetime
import json

from services.auto_training_service import AutoTrainingService
from services.external_dataset_service import ExternalDatasetService
from database import get_db_connection

router = APIRouter(prefix="/api/v1/ai", tags=["AI Training"])

class TrainingRequest(BaseModel):
    force_retrain: bool = False
    include_external_data: bool = True
    dataset_types: Optional[List[str]] = None

class TrainingStatus(BaseModel):
    is_training: bool
    last_training: Optional[str]
    models_trained: List[str]
    training_progress: str

class DatasetStatus(BaseModel):
    kaggle_datasets: Dict[str, Dict]
    hf_datasets: Dict[str, Dict]
    total_datasets: int
    available_datasets: int
    last_updated: Optional[str]

class ModelMetrics(BaseModel):
    model_name: str
    accuracy: float
    training_samples: int
    external_samples: int
    last_trained: str
    cv_scores: List[float]

# Global services
auto_training_service = AutoTrainingService()
external_dataset_service = ExternalDatasetService()

@router.get("/training/status")
async def get_training_status() -> TrainingStatus:
    """Get current training status"""

    return TrainingStatus(
        is_training=auto_training_service.is_training,
        last_training=auto_training_service.last_training.isoformat() if auto_training_service.last_training else None,
        models_trained=['stuck_classifier', 'flow_predictor', 'anomaly_detector', 'productivity_predictor'],
        training_progress="idle" if not auto_training_service.is_training else "training"
    )

@router.post("/training/start")
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """Start AI model training process"""

    if auto_training_service.is_training:
        raise HTTPException(status_code=409, detail="Training already in progress")

    # Start training in background
    background_tasks.add_task(
        _execute_training,
        db,
        request.force_retrain,
        request.include_external_data,
        request.dataset_types or []
    )

    return {
        "status": "started",
        "message": "AI training started in background",
        "include_external_data": request.include_external_data,
        "force_retrain": request.force_retrain
    }

@router.get("/datasets/status")
async def get_datasets_status() -> DatasetStatus:
    """Get status of all external datasets"""

    status = external_dataset_service.get_dataset_status()

    kaggle_datasets = {k: v for k, v in status.items() if k.startswith('kaggle_')}
    hf_datasets = {k: v for k, v in status.items() if k.startswith('hf_')}

    total_datasets = len(status)
    available_datasets = sum(1 for s in status.values() if s.get('downloaded') or s.get('synthetic_available'))

    # Get most recent update
    last_updated = None
    for dataset_status in status.values():
        if dataset_status.get('last_updated'):
            if not last_updated or dataset_status['last_updated'] > last_updated:
                last_updated = dataset_status['last_updated']

    return DatasetStatus(
        kaggle_datasets=kaggle_datasets,
        hf_datasets=hf_datasets,
        total_datasets=total_datasets,
        available_datasets=available_datasets,
        last_updated=last_updated
    )

@router.post("/datasets/download")
async def download_datasets(background_tasks: BackgroundTasks):
    """Download all external datasets"""

    background_tasks.add_task(_download_datasets)

    return {
        "status": "started",
        "message": "Dataset download started in background"
    }

@router.get("/models/metrics")
async def get_model_metrics() -> List[ModelMetrics]:
    """Get performance metrics for all trained models"""

    metrics = []

    model_names = ['stuck_classifier', 'flow_predictor', 'anomaly_detector', 'productivity_predictor']

    for model_name in model_names:
        try:
            import joblib
            import os

            model_path = os.path.join(auto_training_service.models_dir, f"{model_name}.joblib")

            if os.path.exists(model_path):
                loaded = joblib.load(model_path)

                metrics.append(ModelMetrics(
                    model_name=model_name,
                    accuracy=loaded.get('accuracy', 0.0),
                    training_samples=loaded.get('training_samples', 0),
                    external_samples=loaded.get('external_samples', 0),
                    last_trained=loaded.get('trained_at', 'unknown'),
                    cv_scores=loaded.get('cv_scores', [])
                ))
        except Exception as e:
            # Model not found or couldn't load
            metrics.append(ModelMetrics(
                model_name=model_name,
                accuracy=0.0,
                training_samples=0,
                external_samples=0,
                last_trained='never',
                cv_scores=[]
            ))

    return metrics

@router.get("/models/{model_name}/predict")
async def predict_with_model(
    model_name: str,
    session_id: str,
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """Get prediction from specific model"""

    # Get recent session events
    recent_events = await db.fetch("""
        SELECT session_id, agent, type, payload, timestamp
        FROM context_events
        WHERE session_id = $1
        AND timestamp >= NOW() - INTERVAL '1 hour'
        ORDER BY timestamp DESC
        LIMIT 100
    """, session_id)

    session_events = [dict(row) for row in recent_events]

    if model_name == 'stuck_classifier':
        prediction = await auto_training_service.predict_stuck_state(session_events)
        return {
            "model": model_name,
            "session_id": session_id,
            "prediction": prediction,
            "interpretation": "high" if prediction > 0.7 else "medium" if prediction > 0.3 else "low"
        }
    elif model_name == 'flow_predictor':
        prediction = await auto_training_service.predict_flow_state(session_events)
        return {
            "model": model_name,
            "session_id": session_id,
            "prediction": prediction,
            "interpretation": "likely" if prediction > 0.7 else "possible" if prediction > 0.3 else "unlikely"
        }
    elif model_name == 'anomaly_detector':
        prediction = await auto_training_service.detect_anomaly(session_events)
        return {
            "model": model_name,
            "session_id": session_id,
            "prediction": prediction,
            "interpretation": "anomalous" if prediction > 0.7 else "unusual" if prediction > 0.3 else "normal"
        }
    elif model_name == 'productivity_predictor':
        prediction = await auto_training_service.predict_productivity(session_events)
        return {
            "model": model_name,
            "session_id": session_id,
            "prediction": prediction,
            "interpretation": "high" if prediction > 0.7 else "medium" if prediction > 0.3 else "low"
        }
    else:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

@router.get("/training/logs")
async def get_training_logs(
    limit: int = 20,
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """Get recent training logs"""

    try:
        logs = await db.fetch("""
            SELECT timestamp, models_trained, data_points, success,
                   training_duration_seconds, error_message
            FROM ai_training_logs
            ORDER BY timestamp DESC
            LIMIT $1
        """, limit)

        return {
            "logs": [dict(row) for row in logs],
            "total_logs": len(logs)
        }
    except Exception as e:
        # Table might not exist yet
        return {
            "logs": [],
            "total_logs": 0,
            "note": "Training logs table not initialized"
        }

async def _execute_training(
    db: asyncpg.Connection,
    force_retrain: bool,
    include_external_data: bool,
    dataset_types: List[str]
):
    """Execute training in background"""

    if force_retrain or not auto_training_service.last_training:
        await auto_training_service.auto_train(db)

async def _download_datasets():
    """Download datasets in background"""

    await external_dataset_service.download_all_datasets()

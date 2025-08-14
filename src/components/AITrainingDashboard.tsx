import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import {
    Brain,
    Database,
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    Clock,
    Download,
    Play,
    BarChart3,
    Zap,
    Target,
    Activity
} from "lucide-react";

interface TrainingStatus {
    is_training: boolean;
    last_training: string | null;
    models_trained: string[];
    training_progress: string;
}

interface DatasetInfo {
    downloaded: boolean;
    synthetic_available?: boolean;
    last_updated: string | null;
}

interface DatasetStatus {
    kaggle_datasets: Record<string, DatasetInfo>;
    hf_datasets: Record<string, DatasetInfo>;
    total_datasets: number;
    available_datasets: number;
    last_updated: string | null;
}

interface ModelMetrics {
    model_name: string;
    accuracy: number;
    training_samples: number;
    external_samples: number;
    last_trained: string;
    cv_scores: number[];
}

interface TrainingLog {
    timestamp: string;
    models_trained: string[];
    data_points: number;
    success: boolean;
    error_message?: string;
}

const AITrainingDashboard: React.FC = () => {
    const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
    const [datasetStatus, setDatasetStatus] = useState<DatasetStatus | null>(null);
    const [modelMetrics, setModelMetrics] = useState<ModelMetrics[]>([]);
    const [trainingLogs, setTrainingLogs] = useState<TrainingLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [isStartingTraining, setIsStartingTraining] = useState(false);
    const [isDownloadingDatasets, setIsDownloadingDatasets] = useState(false);

    const { toast } = useToast();

    useEffect(() => {
        loadDashboardData();
        const interval = setInterval(loadDashboardData, 30000); // Update every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const loadDashboardData = async () => {
        try {
            const [statusRes, datasetsRes, metricsRes, logsRes] = await Promise.all([
                fetch('/api/v1/ai/training/status'),
                fetch('/api/v1/ai/datasets/status'),
                fetch('/api/v1/ai/models/metrics'),
                fetch('/api/v1/ai/training/logs?limit=10')
            ]);

            if (statusRes.ok) setTrainingStatus(await statusRes.json());
            if (datasetsRes.ok) setDatasetStatus(await datasetsRes.json());
            if (metricsRes.ok) setModelMetrics(await metricsRes.json());
            if (logsRes.ok) {
                const logsData = await logsRes.json();
                setTrainingLogs(logsData.logs || []);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const startTraining = async () => {
        setIsStartingTraining(true);
        try {
            const response = await fetch('/api/v1/ai/training/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    force_retrain: false,
                    include_external_data: true
                })
            });

            if (response.ok) {
                toast({
                    title: "Training Started",
                    description: "AI model training has been started in the background",
                });
                loadDashboardData(); // Refresh status
            } else {
                const error = await response.json();
                toast({
                    title: "Training Failed",
                    description: error.detail || "Failed to start training",
                    variant: "destructive"
                });
            }
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to start training",
                variant: "destructive"
            });
        } finally {
            setIsStartingTraining(false);
        }
    };

    const downloadDatasets = async () => {
        setIsDownloadingDatasets(true);
        try {
            const response = await fetch('/api/v1/ai/datasets/download', {
                method: 'POST'
            });

            if (response.ok) {
                toast({
                    title: "Download Started",
                    description: "External datasets download started in background",
                });
                setTimeout(loadDashboardData, 2000); // Refresh after a moment
            } else {
                toast({
                    title: "Download Failed",
                    description: "Failed to start dataset download",
                    variant: "destructive"
                });
            }
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to start download",
                variant: "destructive"
            });
        } finally {
            setIsDownloadingDatasets(false);
        }
    };

    const getModelIcon = (modelName: string) => {
        switch (modelName) {
            case 'stuck_classifier': return <AlertTriangle className="h-4 w-4" />;
            case 'flow_predictor': return <Zap className="h-4 w-4" />;
            case 'productivity_predictor': return <Target className="h-4 w-4" />;
            case 'anomaly_detector': return <Activity className="h-4 w-4" />;
            default: return <Brain className="h-4 w-4" />;
        }
    };

    const getModelDisplayName = (modelName: string) => {
        switch (modelName) {
            case 'stuck_classifier': return 'Stuck Detection';
            case 'flow_predictor': return 'Flow Prediction';
            case 'productivity_predictor': return 'Productivity Prediction';
            case 'anomaly_detector': return 'Anomaly Detection';
            default: return modelName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-background to-secondary/20 p-6">
                <div className="max-w-7xl mx-auto">
                    <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                            <Brain className="h-12 w-12 animate-pulse mx-auto mb-4 text-primary" />
                            <p className="text-lg text-muted-foreground">Loading AI Training Dashboard...</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const datasetAvailability = datasetStatus
        ? (datasetStatus.available_datasets / datasetStatus.total_datasets) * 100
        : 0;

    return (
        <div className="min-h-screen bg-gradient-to-br from-background to-secondary/20 p-6">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-4xl font-bold flex items-center gap-3">
                            <Brain className="h-10 w-10 text-primary" />
                            AI Training Dashboard
                        </h1>
                        <p className="text-lg text-muted-foreground mt-2">
                            Manage AI model training and external dataset integration
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <Button
                            onClick={downloadDatasets}
                            disabled={isDownloadingDatasets}
                            variant="outline"
                        >
                            <Download className="h-4 w-4 mr-2" />
                            {isDownloadingDatasets ? 'Downloading...' : 'Download Datasets'}
                        </Button>
                        <Button
                            onClick={startTraining}
                            disabled={isStartingTraining || trainingStatus?.is_training}
                        >
                            <Play className="h-4 w-4 mr-2" />
                            {isStartingTraining ? 'Starting...' : 'Start Training'}
                        </Button>
                    </div>
                </div>

                <Tabs defaultValue="overview" className="space-y-6">
                    <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="models">Models</TabsTrigger>
                        <TabsTrigger value="datasets">Datasets</TabsTrigger>
                        <TabsTrigger value="logs">Logs</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-6">
                        {/* Training Status */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Training Status</CardTitle>
                                    {trainingStatus?.is_training ?
                                        <Activity className="h-4 w-4 text-orange-600 animate-pulse" /> :
                                        <CheckCircle className="h-4 w-4 text-green-600" />
                                    }
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">
                                        {trainingStatus?.is_training ? 'Training' : 'Idle'}
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        {trainingStatus?.last_training
                                            ? `Last: ${new Date(trainingStatus.last_training).toLocaleDateString()}`
                                            : 'Never trained'
                                        }
                                    </p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Models Trained</CardTitle>
                                    <Brain className="h-4 w-4 text-blue-600" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">
                                        {modelMetrics.filter(m => m.last_trained !== 'never').length}
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        of {modelMetrics.length} models
                                    </p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Dataset Availability</CardTitle>
                                    <Database className="h-4 w-4 text-purple-600" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{Math.round(datasetAvailability)}%</div>
                                    <Progress value={datasetAvailability} className="mt-2" />
                                    <p className="text-xs text-muted-foreground mt-1">
                                        {datasetStatus?.available_datasets} of {datasetStatus?.total_datasets} available
                                    </p>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Average Accuracy</CardTitle>
                                    <TrendingUp className="h-4 w-4 text-green-600" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">
                                        {modelMetrics.length > 0
                                            ? Math.round((modelMetrics.reduce((sum, m) => sum + m.accuracy, 0) / modelMetrics.length) * 100)
                                            : 0
                                        }%
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        across all models
                                    </p>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Recent Activity */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Recent Training Activity</CardTitle>
                                <CardDescription>Latest training sessions and results</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {trainingLogs.length > 0 ? (
                                    <div className="space-y-3">
                                        {trainingLogs.slice(0, 5).map((log, index) => (
                                            <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                                                <div className="flex items-center gap-3">
                                                    {log.success ?
                                                        <CheckCircle className="h-5 w-5 text-green-600" /> :
                                                        <AlertTriangle className="h-5 w-5 text-red-600" />
                                                    }
                                                    <div>
                                                        <p className="font-medium">
                                                            {log.success ? 'Training Completed' : 'Training Failed'}
                                                        </p>
                                                        <p className="text-sm text-muted-foreground">
                                                            {log.data_points} data points • {log.models_trained.length} models
                                                            {log.error_message && ` • ${log.error_message}`}
                                                        </p>
                                                    </div>
                                                </div>
                                                <Badge variant={log.success ? 'default' : 'destructive'}>
                                                    {new Date(log.timestamp).toLocaleTimeString()}
                                                </Badge>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-center text-muted-foreground py-8">
                                        No training history available
                                    </p>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="models" className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {modelMetrics.map((model) => (
                                <Card key={model.model_name}>
                                    <CardHeader className="flex flex-row items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            {getModelIcon(model.model_name)}
                                            <CardTitle className="text-lg">
                                                {getModelDisplayName(model.model_name)}
                                            </CardTitle>
                                        </div>
                                        <Badge variant={model.last_trained === 'never' ? 'secondary' : 'default'}>
                                            {model.last_trained === 'never' ? 'Not Trained' : 'Trained'}
                                        </Badge>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                            <div>
                                                <p className="text-muted-foreground">Accuracy</p>
                                                <p className="font-mono text-lg">
                                                    {model.accuracy > 0 ? `${Math.round(model.accuracy * 100)}%` : 'N/A'}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Training Samples</p>
                                                <p className="font-mono text-lg">{model.training_samples.toLocaleString()}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">External Samples</p>
                                                <p className="font-mono text-lg">{model.external_samples.toLocaleString()}</p>
                                            </div>
                                            <div>
                                                <p className="text-muted-foreground">Last Trained</p>
                                                <p className="text-sm">
                                                    {model.last_trained === 'never' ? 'Never' :
                                                        new Date(model.last_trained).toLocaleDateString()}
                                                </p>
                                            </div>
                                        </div>

                                        {model.cv_scores.length > 0 && (
                                            <div>
                                                <p className="text-sm text-muted-foreground mb-2">Cross-Validation Scores</p>
                                                <div className="flex gap-1">
                                                    {model.cv_scores.map((score, index) => (
                                                        <div
                                                            key={index}
                                                            className="h-2 bg-primary rounded-sm flex-1"
                                                            style={{ opacity: score }}
                                                            title={`Fold ${index + 1}: ${Math.round(score * 100)}%`}
                                                        />
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </TabsContent>

                    <TabsContent value="datasets" className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Database className="h-5 w-5" />
                                        Kaggle Datasets
                                    </CardTitle>
                                    <CardDescription>External datasets from Kaggle platform</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {datasetStatus?.kaggle_datasets && Object.keys(datasetStatus.kaggle_datasets).length > 0 ? (
                                        <div className="space-y-3">
                                            {Object.entries(datasetStatus.kaggle_datasets).map(([name, status]: [string, DatasetInfo]) => (
                                                <div key={name} className="flex items-center justify-between p-2 border rounded">
                                                    <div>
                                                        <p className="font-medium">{name.replace('kaggle_', '')}</p>
                                                        <p className="text-sm text-muted-foreground">
                                                            {status.last_updated ?
                                                                `Updated: ${new Date(status.last_updated).toLocaleDateString()}` :
                                                                'Not downloaded'
                                                            }
                                                        </p>
                                                    </div>
                                                    <Badge variant={
                                                        status.downloaded ? 'default' :
                                                            status.synthetic_available ? 'secondary' :
                                                                'destructive'
                                                    }>
                                                        {status.downloaded ? 'Downloaded' :
                                                            status.synthetic_available ? 'Synthetic' :
                                                                'Missing'}
                                                    </Badge>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-center text-muted-foreground py-4">No Kaggle datasets configured</p>
                                    )}
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Database className="h-5 w-5" />
                                        Hugging Face Datasets
                                    </CardTitle>
                                    <CardDescription>Datasets from Hugging Face Hub</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {datasetStatus?.hf_datasets && Object.keys(datasetStatus.hf_datasets).length > 0 ? (
                                        <div className="space-y-3">
                                            {Object.entries(datasetStatus.hf_datasets).map(([name, status]: [string, DatasetInfo]) => (
                                                <div key={name} className="flex items-center justify-between p-2 border rounded">
                                                    <div>
                                                        <p className="font-medium">{name.replace('hf_', '')}</p>
                                                        <p className="text-sm text-muted-foreground">
                                                            {status.last_updated ?
                                                                `Updated: ${new Date(status.last_updated).toLocaleDateString()}` :
                                                                'Not downloaded'
                                                            }
                                                        </p>
                                                    </div>
                                                    <Badge variant={status.downloaded ? 'default' : 'destructive'}>
                                                        {status.downloaded ? 'Downloaded' : 'Missing'}
                                                    </Badge>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-center text-muted-foreground py-4">No Hugging Face datasets configured</p>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>

                    <TabsContent value="logs" className="space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Clock className="h-5 w-5" />
                                    Training Logs
                                </CardTitle>
                                <CardDescription>Detailed training session history</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {trainingLogs.length > 0 ? (
                                    <div className="space-y-4">
                                        {trainingLogs.map((log, index) => (
                                            <div key={index} className="border rounded-lg p-4">
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-2">
                                                        {log.success ?
                                                            <CheckCircle className="h-4 w-4 text-green-600" /> :
                                                            <AlertTriangle className="h-4 w-4 text-red-600" />
                                                        }
                                                        <span className="font-medium">
                                                            {new Date(log.timestamp).toLocaleString()}
                                                        </span>
                                                    </div>
                                                    <Badge variant={log.success ? 'default' : 'destructive'}>
                                                        {log.success ? 'Success' : 'Failed'}
                                                    </Badge>
                                                </div>
                                                <div className="text-sm text-muted-foreground space-y-1">
                                                    <p>Models: {log.models_trained.join(', ') || 'None'}</p>
                                                    <p>Data Points: {log.data_points.toLocaleString()}</p>
                                                    {log.error_message && (
                                                        <p className="text-red-600">Error: {log.error_message}</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12">
                                        <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                                        <p className="text-lg text-muted-foreground">No training logs available</p>
                                        <p className="text-sm text-muted-foreground">Start your first training session to see logs here</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
};

export default AITrainingDashboard;

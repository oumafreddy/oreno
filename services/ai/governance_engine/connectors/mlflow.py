"""
MLflow connector for AI governance.
Handles model discovery, metadata extraction, and lineage tracking.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Model information from MLflow registry."""
    name: str
    version: str
    uri: str
    signature: Dict[str, Any]
    metadata: Dict[str, Any]
    tags: Dict[str, str]
    stage: str
    created_at: str
    last_updated: str


class MLflowConnector:
    """Connector for MLflow model registry."""
    
    def __init__(self, tracking_uri: str, registry_uri: Optional[str] = None):
        """
        Initialize MLflow connector.
        
        Args:
            tracking_uri: MLflow tracking server URI
            registry_uri: MLflow model registry URI (optional)
        """
        self.tracking_uri = tracking_uri
        self.registry_uri = registry_uri or tracking_uri
        self._client = None
    
    @property
    def client(self):
        """Lazy load MLflow client."""
        if self._client is None:
            try:
                import mlflow
                mlflow.set_tracking_uri(self.tracking_uri)
                self._client = mlflow.tracking.MlflowClient()
            except ImportError:
                logger.error("MLflow not installed. Install with: pip install mlflow")
                raise
        return self._client
    
    def list_models(self, max_results: int = 100) -> List[ModelInfo]:
        """
        List all models from MLflow registry.
        
        Args:
            max_results: Maximum number of models to return
            
        Returns:
            List of ModelInfo objects
        """
        try:
            models = self.client.search_registered_models(max_results=max_results)
            model_infos = []
            
            for model in models:
                # Get latest version
                latest_version = model.latest_versions[0] if model.latest_versions else None
                if latest_version:
                    model_info = ModelInfo(
                        name=model.name,
                        version=latest_version.version,
                        uri=latest_version.source,
                        signature=self._get_model_signature(model.name, latest_version.version),
                        metadata=model.tags or {},
                        tags=latest_version.tags or {},
                        stage=latest_version.current_stage,
                        created_at=str(model.creation_timestamp),
                        last_updated=str(model.last_updated_timestamp)
                    )
                    model_infos.append(model_info)
            
            return model_infos
            
        except Exception as exc:
            logger.error(f"Failed to list models from MLflow: {exc}")
            raise
    
    def get_model_info(self, name: str, version: Optional[str] = None) -> Optional[ModelInfo]:
        """
        Get specific model information.
        
        Args:
            name: Model name
            version: Model version (latest if None)
            
        Returns:
            ModelInfo object or None if not found
        """
        try:
            if version is None:
                # Get latest version
                model = self.client.get_latest_versions(name, stages=["None"])[0]
                version = model.version
            else:
                model = self.client.get_model_version(name, version)
            
            return ModelInfo(
                name=name,
                version=version,
                uri=model.source,
                signature=self._get_model_signature(name, version),
                metadata=model.tags or {},
                tags=model.tags or {},
                stage=model.current_stage,
                created_at=str(model.creation_timestamp),
                last_updated=str(model.last_updated_timestamp)
            )
            
        except Exception as exc:
            logger.error(f"Failed to get model info for {name}:{version}: {exc}")
            return None
    
    def _get_model_signature(self, name: str, version: str) -> Dict[str, Any]:
        """Get model signature information."""
        try:
            model_uri = f"models:/{name}/{version}"
            import mlflow
            model = mlflow.pyfunc.load_model(model_uri)
            
            signature = {}
            if hasattr(model, 'signature') and model.signature:
                signature = {
                    'inputs': model.signature.inputs.to_dict() if model.signature.inputs else None,
                    'outputs': model.signature.outputs.to_dict() if model.signature.outputs else None
                }
            
            return signature
            
        except Exception as exc:
            logger.warning(f"Failed to get signature for {name}:{version}: {exc}")
            return {}
    
    def get_model_lineage(self, name: str, version: str) -> Dict[str, Any]:
        """
        Get model lineage information.
        
        Args:
            name: Model name
            version: Model version
            
        Returns:
            Lineage information including training runs, datasets, etc.
        """
        try:
            model = self.client.get_model_version(name, version)
            run_id = model.run_id
            
            # Get run information
            run = self.client.get_run(run_id)
            
            lineage = {
                'run_id': run_id,
                'experiment_id': run.info.experiment_id,
                'status': run.info.status,
                'start_time': run.info.start_time,
                'end_time': run.info.end_time,
                'user_id': run.info.user_id,
                'params': run.data.params,
                'metrics': run.data.metrics,
                'tags': run.data.tags,
                'artifacts': []
            }
            
            # Get artifacts
            try:
                artifacts = self.client.list_artifacts(run_id)
                lineage['artifacts'] = [artifact.path for artifact in artifacts]
            except Exception as exc:
                logger.warning(f"Failed to get artifacts for run {run_id}: {exc}")
            
            return lineage
            
        except Exception as exc:
            logger.error(f"Failed to get lineage for {name}:{version}: {exc}")
            return {}
    
    def download_model(self, name: str, version: str, local_path: str) -> bool:
        """
        Download model to local path.
        
        Args:
            name: Model name
            version: Model version
            local_path: Local directory to download to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import mlflow
            model_uri = f"models:/{name}/{version}"
            mlflow.pyfunc.save_model(model_uri, local_path)
            return True
            
        except Exception as exc:
            logger.error(f"Failed to download model {name}:{version}: {exc}")
            return False


def sync_models_from_mlflow(connector_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Sync models from MLflow registry.
    
    Args:
        connector_config: Connector configuration
        
    Returns:
        List of model information dictionaries
    """
    try:
        connector = MLflowConnector(
            tracking_uri=connector_config['tracking_uri'],
            registry_uri=connector_config.get('registry_uri')
        )
        
        models = connector.list_models()
        model_data = []
        
        for model in models:
            model_data.append({
                'name': model.name,
                'version': model.version,
                'uri': model.uri,
                'signature': model.signature,
                'metadata': model.metadata,
                'tags': model.tags,
                'stage': model.stage,
                'created_at': model.created_at,
                'last_updated': model.last_updated,
                'lineage': connector.get_model_lineage(model.name, model.version)
            })
        
        return model_data
        
    except Exception as exc:
        logger.error(f"Failed to sync models from MLflow: {exc}")
        raise

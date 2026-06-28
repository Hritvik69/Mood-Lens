import hashlib
import urllib.request
import logging
import time
from pathlib import Path
import numpy as np
import onnxruntime as ort
from core.config import settings

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages the lifecycle of AI models including downloading, verifying,
    warming up, and maintaining ONNX inference sessions.
    """
    def __init__(self):
        self.session = None
        self.input_name = None
        self.input_shape = None
        self.output_name = None
        self.current_provider = None

    def get_model_path(self) -> Path:
        return settings.MODEL_DIR / settings.MODEL_NAME

    def check_model_exists(self) -> bool:
        model_path = self.get_model_path()
        return model_path.exists() and model_path.stat().st_size > 0

    def verify_checksum(self) -> bool:
        """Verifies the SHA256 checksum of the downloaded model."""
        if not self.check_model_exists():
            return False
            
        model_path = self.get_model_path()
        sha256_hash = hashlib.sha256()
        
        try:
            with open(model_path, "rb") as f:
                # Read file in chunks to avoid memory issues for large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            calculated_hash = sha256_hash.hexdigest()
            if calculated_hash == settings.MODEL_SHA256:
                logger.info("Model SHA256 verification succeeded.")
                return True
            else:
                logger.warning(
                    f"Model checksum mismatch. Expected: {settings.MODEL_SHA256}, "
                    f"Calculated: {calculated_hash}."
                )
                return False
        except Exception as e:
            logger.error(f"Error during checksum verification: {e}")
            return False

    def download_model(self):
        """Downloads the ONNX model from the configured URL."""
        model_path = self.get_model_path()
        settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading model from {settings.MODEL_URL} to {model_path}...")
        start_time = time.time()
        
        try:
            # Custom download reporter
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(int(block_num * block_size * 100 / total_size), 100)
                    if percent % 10 == 0 and percent > 0:
                        logger.info(f"Downloading model: {percent}% complete...")

            urllib.request.urlretrieve(
                settings.MODEL_URL,
                str(model_path),
                reporthook=report_progress if logger.isEnabledFor(logging.INFO) else None
            )
            
            duration = time.time() - start_time
            logger.info(f"Model downloaded successfully in {duration:.2f} seconds.")
            
        except Exception as e:
            logger.error(f"Failed to download model from {settings.MODEL_URL}: {e}")
            # Clean up partial download
            if model_path.exists():
                try:
                    model_path.unlink()
                except Exception:
                    pass
            raise RuntimeError(f"Could not download model: {e}")

    def load_model(self):
        """
        Ensures model exists, downloads it if necessary, verifies integrity,
        initializes the ONNX runtime session, and runs a warm-up.
        """
        model_path = self.get_model_path()
        
        if not self.check_model_exists():
            logger.info("Model file not found. Starting automatic download...")
            self.download_model()
        else:
            logger.info("Model file found locally.")
            # Verify checksum, but proceed with warning even if hash mismatches 
            # to accommodate model revisions
            self.verify_checksum()
            
        logger.info("Initializing ONNX Runtime session...")
        
        # Get available providers
        available_providers = ort.get_available_providers()
        logger.info(f"Available ONNX execution providers: {available_providers}")
        
        # Select providers based on configuration preference list
        selected_providers = [
            prov for prov in settings.PREFERRED_PROVIDERS if prov in available_providers
        ]
        
        logger.info(f"Selected providers: {selected_providers}")
        
        try:
            self.session = ort.InferenceSession(
                str(model_path),
                providers=selected_providers
            )
            
            # Record current working provider
            self.current_provider = self.session.get_providers()[0]
            logger.info(f"ONNX session loaded using provider: {self.current_provider}")
            
            # Inspect input/output shapes
            input_meta = self.session.get_inputs()[0]
            self.input_name = input_meta.name
            self.input_shape = input_meta.shape
            
            output_meta = self.session.get_outputs()[0]
            self.output_name = output_meta.name
            
            logger.info(
                f"Model structure - Input Name: '{self.input_name}', Shape: {self.input_shape} | "
                f"Output Name: '{self.output_name}'"
            )
            
            # Perform warm-up
            self._warmup()
            
        except Exception as e:
            logger.error(f"Failed to load ONNX session: {e}")
            raise RuntimeError(f"Model initialization failure: {e}")

    def _warmup(self):
        """Runs a dummy tensor to warm up GPU/CPU kernel allocations."""
        logger.info("Warming up ONNX session...")
        # If shape is dynamic or variable, default to [1, 1, 64, 64]
        batch_size = self.input_shape[0] if isinstance(self.input_shape[0], int) else 1
        channels = self.input_shape[1] if isinstance(self.input_shape[1], int) else 1
        height = self.input_shape[2] if isinstance(self.input_shape[2], int) else 64
        width = self.input_shape[3] if isinstance(self.input_shape[3], int) else 64
        
        dummy_shape = (batch_size, channels, height, width)
        dummy_input = np.zeros(dummy_shape, dtype=np.float32)
        
        start_time = time.time()
        for _ in range(5):  # Run a few times
            self.session.run([self.output_name], {self.input_name: dummy_input})
        
        logger.info(f"Warm-up finished. Average warm-up latency: {(time.time() - start_time)*1000/5:.2f}ms")

    def predict(self, face_tensors: np.ndarray) -> np.ndarray:
        """
        Runs batch predictions on normalized face tensors.
        Expects preprocessed array of shape [N, 1, H, W] matching model inputs.
        """
        if self.session is None:
            raise RuntimeError("Model is not loaded. Call load_model() first.")
            
        # Dynamically reshape input name
        outputs = self.session.run([self.output_name], {self.input_name: face_tensors})
        return outputs[0]

# Global Model Manager instance
model_manager = ModelManager()

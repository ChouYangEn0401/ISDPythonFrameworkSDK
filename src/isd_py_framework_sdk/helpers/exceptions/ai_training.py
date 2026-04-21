"""
AI / ML training exceptions — errors that occur during dataset preparation,
model training, evaluation, checkpointing, and inference.
"""


class ModelNotFittedError(Exception):
    """Raised when a model is asked to predict/evaluate before being fitted/trained."""

    def __init__(self, model: str = "", message: str | None = None):
        if message is None:
            if model:
                message = f"Model '{model}' has not been fitted yet. Call fit() before predict()."
            else:
                message = "The model has not been fitted yet. Call fit() before predict()."
        super().__init__(message)
        self.model = model


class CheckpointNotFoundError(Exception):
    """Raised when a requested model checkpoint file or entry does not exist."""

    def __init__(self, path: str = "", message: str | None = None):
        if message is None:
            if path:
                message = f"Checkpoint not found at '{path}'."
            else:
                message = "The requested checkpoint could not be found."
        super().__init__(message)
        self.path = path


class TrainingInterruptedError(Exception):
    """Raised when a training run is stopped before completion (e.g. by signal, OOM, or manual stop)."""

    def __init__(self, epoch: int | None = None, reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Training interrupted at epoch {epoch}"] if epoch is not None else ["Training interrupted"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.epoch = epoch
        self.reason = reason


class HyperparameterError(Exception):
    """Raised when a hyperparameter value is invalid or outside its acceptable range."""

    def __init__(self, param: str = "", value=None, message: str | None = None):
        if message is None:
            if param and value is not None:
                message = f"Invalid hyperparameter '{param}' = {value!r}."
            elif param:
                message = f"Invalid value for hyperparameter '{param}'."
            else:
                message = "A hyperparameter has an invalid value."
        super().__init__(message)
        self.param = param
        self.value = value


class DatasetSplitError(Exception):
    """Raised when a dataset cannot be split correctly (invalid ratios, too few samples, …)."""

    def __init__(self, reason: str = "", message: str | None = None):
        if message is None:
            message = f"Dataset split failed: {reason}." if reason else "Dataset split failed."
        super().__init__(message)
        self.reason = reason


class GradientExplosionError(Exception):
    """Raised when gradient values exceed a safe threshold (NaN/Inf detected during training)."""

    def __init__(self, layer: str = "", norm: float | None = None, message: str | None = None):
        if message is None:
            if layer and norm is not None:
                message = f"Gradient explosion detected in layer '{layer}' (norm={norm:.4e})."
            elif layer:
                message = f"Gradient explosion detected in layer '{layer}'."
            else:
                message = "Gradient explosion detected during training."
        super().__init__(message)
        self.layer = layer
        self.norm = norm


class GradientVanishingError(Exception):
    """Raised when gradients become vanishingly small and training stalls."""

    def __init__(self, layer: str = "", norm: float | None = None, message: str | None = None):
        if message is None:
            if layer and norm is not None:
                message = f"Gradient vanishing detected in layer '{layer}' (norm={norm:.4e})."
            elif layer:
                message = f"Gradient vanishing detected in layer '{layer}'."
            else:
                message = "Gradient vanishing detected during training."
        super().__init__(message)
        self.layer = layer
        self.norm = norm


class InferenceError(Exception):
    """Raised when model inference fails (shape mismatch, unsupported input, runtime error, …)."""

    def __init__(self, model: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Inference failed for model '{model}'"] if model else ["Inference failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.model = model
        self.reason = reason


class EpochLimitReachedError(Exception):
    """Raised when the maximum number of training epochs is reached without convergence."""

    def __init__(self, max_epochs: int | None = None, message: str | None = None):
        if message is None:
            if max_epochs is not None:
                message = f"Maximum epoch limit of {max_epochs} was reached without convergence."
            else:
                message = "Maximum epoch limit reached without convergence."
        super().__init__(message)
        self.max_epochs = max_epochs


class ModelArchitectureError(Exception):
    """Raised when the defined model architecture is structurally invalid or incompatible."""

    def __init__(self, detail: str = "", message: str | None = None):
        if message is None:
            message = f"Model architecture error: {detail}." if detail else "Model architecture is invalid."
        super().__init__(message)
        self.detail = detail

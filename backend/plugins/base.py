from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np

class BasePlugin(ABC):
    """
    Abstract Base Class that defines the interface for all AI plugins.
    Allows independent development and registration of new modules.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique identifier/name of the plugin."""
        pass

    @abstractmethod
    def process(
        self, 
        frame: np.ndarray, 
        faces: List[Dict[str, Any]], 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Processes a raw frame and the extracted face objects.
        Modifies the list of dictionaries representing face metadata in-place 
        and returns the updated list.
        
        Args:
            frame: Raw numpy array (BGR representation of current frame).
            faces: List of dictionaries containing face bounding boxes, 
                  landmarks, and metadata.
            **kwargs: Extra runtime configurations.
        """
        pass

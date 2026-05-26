
from collections import defaultdict

import json
import pickle

from pathlib import Path
from typing import Any, Optional

class Memoizer(defaultdict):
    _instance: Optional['Memoizer'] = None
    _cache: dict = {}
    _filepath: Optional[Path] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize only once"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
    
    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache"""
        self._cache[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the cache"""
        return self._cache.get(key, default)
    
    def save(self, filepath: str, format: str = "json") -> None:
        """Persist cache to disk (json or pickle)"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(path, 'w') as f:
                json.dump(self._cache, f, indent=2)
        elif format == "pickle":
            with open(path, 'wb') as f:
                pickle.dump(self._cache, f)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def load(self, filepath: str, format: str = "json") -> None:
        """Load cache from disk"""
        path = Path(filepath)
        
        if not path.exists():
            return
        
        if format == "json":
            with open(path, 'r') as f:
                self._cache = json.load(f)
        elif format == "pickle":
            with open(path, 'rb') as f:
                self._cache = pickle.load(f)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def clear(self) -> None:
        """Clear all cached data"""
        self._cache.clear()



## Create singleton instance
# memo = Memoizer()
# memo.set("user_data", {"name": "Alice"})

# memo2 = Memoizer()

# print(memo2.get("user_data"))  # {'name': 'Alice'}
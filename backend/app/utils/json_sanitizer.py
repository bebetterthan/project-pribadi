"""
Comprehensive JSON sanitization utilities
Handles protobuf objects, malformed keys, and non-serializable types
"""
import json
from typing import Any, Dict, List
from app.utils.logger import logger


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize object for JSON serialization
    
    Handles:
    - Dictionary keys with newlines/special characters
    - Protobuf objects (MessageMapContainer, etc.)
    - Non-serializable types
    - Nested structures
    
    Args:
        obj: Any Python object
        
    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, dict):
        sanitized = {}
        for key, value in obj.items():
            try:
                # Sanitize key - remove newlines, tabs, special chars
                clean_key = str(key).strip().replace('\n', '').replace('\r', '').replace('\t', '')
                if not clean_key:
                    # Generate safe fallback key
                    clean_key = f"field_{len(sanitized)}"
                    logger.warning(f"Empty key after sanitization, using: {clean_key}")
                
                # Recursively sanitize value
                sanitized[clean_key] = sanitize_for_json(value)
            except Exception as e:
                logger.error(f"Error sanitizing dict entry key={repr(key)}: {e}")
                # Skip this entry rather than crash
                continue
        return sanitized
    
    elif isinstance(obj, list):
        try:
            return [sanitize_for_json(item) for item in obj]
        except Exception as e:
            logger.error(f"Error sanitizing list: {e}")
            return []
    
    elif isinstance(obj, tuple):
        try:
            return [sanitize_for_json(item) for item in obj]
        except Exception as e:
            logger.error(f"Error sanitizing tuple: {e}")
            return []
    
    elif isinstance(obj, (str, int, float, bool, type(None))):
        # Already JSON-serializable primitives
        return obj
    
    else:
        # Unknown type - try to convert to string
        try:
            # First check if it's actually JSON serializable
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # Not serializable - convert to string representation
            try:
                return str(obj)
            except Exception as e:
                logger.error(f"Cannot convert object to string: {type(obj).__name__}: {e}")
                return f"<{type(obj).__name__} object>"


def sanitize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a complete SSE event dictionary
    
    Args:
        event: Event dict with 'type', 'content', 'metadata'
        
    Returns:
        Sanitized event dict safe for JSON serialization
    """
    try:
        return {
            "type": str(event.get("type", "unknown")),
            "content": str(event.get("content", "")),
            "metadata": sanitize_for_json(event.get("metadata", {})),
            **{k: sanitize_for_json(v) for k, v in event.items() 
               if k not in ["type", "content", "metadata"]}
        }
    except Exception as e:
        logger.error(f"Error sanitizing event: {e}", exc_info=True)
        # Return minimal safe event
        return {
            "type": "system",
            "content": "Error: Event sanitization failed",
            "metadata": {"error": True, "error_type": type(e).__name__}
        }


def test_json_serialization(obj: Any) -> bool:
    """
    Test if an object is JSON serializable
    
    Args:
        obj: Object to test
        
    Returns:
        True if serializable, False otherwise
    """
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    JSON dumps with automatic sanitization fallback
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(obj, **kwargs)
    except (TypeError, ValueError) as e:
        logger.warning(f"JSON serialization failed, applying sanitization: {e}")
        sanitized = sanitize_for_json(obj)
        return json.dumps(sanitized, **kwargs)


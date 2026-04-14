"""
Backward compatibility layer - redirects to backend package.
This allows old imports like 'from src.core import ...' to still work.
"""
# Re-export everything from backend
import sys
from pathlib import Path

# Add backend to path if not already there
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

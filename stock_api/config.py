"""
Configuration for the Stock Analysis API.

Re-exports the root-level config (Azure OpenAI endpoint, Entra ID credential,
deployment name, get_client).  Uses importlib to load the root config.py by
file path to avoid a circular import caused by both files sharing the name
'config' when stock_api/ is on sys.path.
"""

import importlib.util
import os

_root_config_path = os.path.join(os.path.dirname(__file__), "..", "config.py")
_spec = importlib.util.spec_from_file_location("root_config", _root_config_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Re-export the symbols callers within stock_api/ need
DEPLOYMENT: str = _mod.DEPLOYMENT  # noqa: F401
get_client = _mod.get_client        # noqa: F401

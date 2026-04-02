"""
FOMC project configuration — imports shared Azure OpenAI settings
from the root config and adds FOMC-specific constants.
"""

import importlib.util
import os
import sys

# Import the *root* config explicitly by file path to avoid circular import
# with this local config.py
_parent_config_path = os.path.join(os.path.dirname(__file__), "..", "config.py")
_spec = importlib.util.spec_from_file_location("root_config", _parent_config_path)
_root_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root_config)

DEPLOYMENT = _root_config.DEPLOYMENT
get_client = _root_config.get_client
MODEL = _root_config.MODEL

# ── FOMC-specific settings ────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 1024          # cost-efficient slice of the full 3072

CHUNK_SIZE = 500                     # target tokens per chunk
CHUNK_OVERLAP = 50                   # overlap tokens between chunks

FOMC_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
FOMC_BASE_URL = "https://www.federalreserve.gov"

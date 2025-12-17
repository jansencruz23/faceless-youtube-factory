"""
LangGraph state definition.
Defines the data that flows through the pipeline.
"""
from typing import TypedDict, List, Dict, Any, Optional


class GraphState(TypedDict):
    """State that flows through the LangGraph pipeline.

    Each node can read and modify this state.
    All fields are optional to allow partial initialization.
    """
    # Core identifiers
    project_id: str
    user_id: str

    # Input from user
    script_prompt: str
    auto_upload: bool

    # Generated data (populated by nodes)
    script_json: Optional[Dict[str, Any]]
    cast_list: Optional[Dict[str, Any]]
    audio_files: List[str]
    video_path: Optional[str]

    # YouTube-specific
    youtube_metadata: Optional[Dict[str, Any]]
    youtube_video_id: Optional[str]

    # Error handling
    errors: List[str]
    retry_count: int
    current_step: str

    # Progress tracking (0.0 to 1.0)
    progress: float
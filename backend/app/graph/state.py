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
    image_mode: str  # per_scene, single, upload, or none
    scenes_per_image: (
        int  # Number of scenes per generated image (only for per_scene mode)
    )
    background_image_url: Optional[str]  # Custom image URL (only for upload mode)

    # Generated data (populated by nodes)
    script_json: Optional[Dict[str, Any]]
    cast_list: Optional[Dict[str, Any]]
    audio_files: List[str]
    audio_scene_indices: List[int]
    image_files: List[str]
    image_scene_indices: List[int]
    image_prompts: List[str]
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

    # Additional states for vertical video
    video_format: str  # "horizontal" or "vertical"
    background_video_url: Optional[str]
    background_music_url: Optional[str]
    music_volume: float
    enable_captions: bool
    voice_preference: Optional[Dict[str, str]]  # User voice preference if specified

    # TTS provider selection
    tts_provider: str  # "edge_tts" or "chatterbox"

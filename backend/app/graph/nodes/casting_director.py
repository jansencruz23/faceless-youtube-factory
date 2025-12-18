"""
CastingDirector Node - Assigns voices to characters.
"""
from typing import Dict, Any, List
from uuid import uuid4

from app.graph.state import GraphState
from app.models import Cast, ProjectStatus
from app.database import get_session_context
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Default voice mappings based on character archetypes
DEFAULT_VOICE_MAP = {
    "narrator": {"voice_id": "en-US-AriaNeural", "pitch": "+0Hz", "rate": "+0%"},
    "host": {"voice_id": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+5%"},
    "expert": {"voice_id": "en-US-JennyNeural", "pitch": "-2Hz", "rate": "+0%"},
    "teacher": {"voice_id": "en-US-SaraNeural", "pitch": "+0Hz", "rate": "-5%"},
    "student": {"voice_id": "en-US-AnaNeural", "pitch": "+3Hz", "rate": "+0%"},
    "default_male": {"voice_id": "en-US-ChristopherNeural", "pitch": "+0Hz", "rate": "+0%"},
    "default_female": {"voice_id": "en-US-MichelleNeural", "pitch": "+0Hz", "rate": "+0%"},
}

async def casting_director_node(state: GraphState) -> GraphState:
    """
    Analyze script and assign appropriate voices to each character.
    
    Uses keyword matching to determine character personality
    and assigns fitting edge-tts voices.
    
    Updates:
    - cast_list: Dictionary mapping character names to voice settings
    - progress: Updated to 0.3 on success
    """
    logger.info("CastingDirector node started", project_id=state["project_id"])
    
    state["current_step"] = "casting"
    
    try:
        script_json = state["script_json"]
        scenes = script_json.get("scenes", [])

        # Extract unique speakers
        speakers = list(set(scene["speaker"] for scene in scenes))

         # Assign voices based on character analysis
        cast_assignments = {}
        used_voices = set()

        for speaker in speakers:
            voice_settings = _analyze_and_assign_voice(
                speaker, 
                scenes, 
                used_voices
            )
            cast_assignments[speaker] = voice_settings
            used_voices.add(voice_settings["voice_id"])

        # Save to database
        async with get_session_context() as session:
            from app.models import Project

            # Update project status
            from uuid import UUID as UUIDType
            project = await session.get(Project, UUIDType(state["project_id"]))
            if project:
                project.status = ProjectStatus.GENERATING_AUDIO
                session.add(project)

            # Create cast record
            cast = Cast(
                id=uuid4(),
                project_id=state["project_id"],
                assignments=cast_assignments
            )
            session.add(cast)
            await session.commit()

        state["cast_list"] = cast_assignments
        state["progress"] = 0.3

        logger.info(
            "Casting completed",
            project_id=state["project_id"],
            characters=list(cast_assignments.keys())
        )

    except Exception as e:
        error_msg = f"Casting failed: {str(e)}"
        logger.error(error_msg, project_id=state["project_id"])
        state["errors"].append(error_msg)

        # Use fallback casting
        speakers = list(set(
            scene["speaker"] 
            for scene in state["script_json"].get("scenes", [])
        ))
        state["cast_list"] = {
            speaker: DEFAULT_VOICE_MAP["default_male" if i % 2 == 0 else "default_female"]
            for i, speaker in enumerate(speakers)
        }

    return state

def _analyze_and_assign_voice(
    speaker: str, 
    scenes: List[Dict], 
    used_voices: set
) -> Dict[str, str]:
    """
    Analyze speaker's dialogue and assign an appropriate voice.
    
    Uses keyword matching on speaker name and dialogue content.
    """
    speaker_lower = speaker.lower()

    # Check for known archetypes in speaker name
    for archetype, settings in DEFAULT_VOICE_MAP.items():
        if archetype in speaker_lower:
            if settings["voice_id"] not in used_voices:
                return settings.copy()

    # Analyze dialogue content
    speaker_lines = [
        scene["line"] for scene in scenes 
        if scene["speaker"] == speaker
    ]
    combined_text = " ".join(speaker_lines).lower()

    # Simple keyword-based personality detection
    if any(word in combined_text for word in ["welcome", "hello", "today"]):
        # Sounds like a host
        voice = DEFAULT_VOICE_MAP["host"]
    elif any(word in combined_text for word in ["research", "study", "data"]):
        # Sounds like an expert
        voice = DEFAULT_VOICE_MAP["expert"]
    elif any(word in combined_text for word in ["learn", "understand", "explain"]):
        # Sounds like a teacher
        voice = DEFAULT_VOICE_MAP["teacher"]
    else:
        # Default alternating
        voice = DEFAULT_VOICE_MAP["default_male"]

    # If voice already used, try alternate
    if voice["voice_id"] in used_voices:
        for alt_voice in DEFAULT_VOICE_MAP.values():
            if alt_voice["voice_id"] not in used_voices:
                return alt_voice.copy()
    
    return voice.copy()
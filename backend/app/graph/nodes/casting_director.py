"""
CastingDirector Node - Uses LLM to intelligently assign voices to characters.
"""

import json
from typing import Dict, Any, List
from uuid import uuid4

from app.graph.state import GraphState
from app.models import Cast, ProjectStatus
from app.database import get_session_context
from app.services.groq_service import groq_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Comprehensive list of available edge-tts voices for casting
# VERIFIED against edge-tts on 2024-12-19
AVAILABLE_VOICES = [
    # ==================== ENGLISH - US ====================
    {
        "voice_id": "en-US-AriaNeural",
        "name": "Aria",
        "gender": "Female",
        "locale": "en-US",
        "style": "warm, friendly narrator",
    },
    {
        "voice_id": "en-US-GuyNeural",
        "name": "Guy",
        "gender": "Male",
        "locale": "en-US",
        "style": "casual, conversational host",
    },
    {
        "voice_id": "en-US-JennyNeural",
        "name": "Jenny",
        "gender": "Female",
        "locale": "en-US",
        "style": "professional, clear expert",
    },
    {
        "voice_id": "en-US-AnaNeural",
        "name": "Ana",
        "gender": "Female",
        "locale": "en-US",
        "style": "young, curious student",
    },
    {
        "voice_id": "en-US-AndrewNeural",
        "name": "Andrew",
        "gender": "Male",
        "locale": "en-US",
        "style": "mature, trustworthy",
    },
    {
        "voice_id": "en-US-BrianNeural",
        "name": "Brian",
        "gender": "Male",
        "locale": "en-US",
        "style": "friendly, approachable",
    },
    {
        "voice_id": "en-US-ChristopherNeural",
        "name": "Christopher",
        "gender": "Male",
        "locale": "en-US",
        "style": "professional newscaster",
    },
    {
        "voice_id": "en-US-EricNeural",
        "name": "Eric",
        "gender": "Male",
        "locale": "en-US",
        "style": "youthful, dynamic",
    },
    # ==================== ENGLISH - UK ====================
    {
        "voice_id": "en-GB-RyanNeural",
        "name": "Ryan",
        "gender": "Male",
        "locale": "en-GB",
        "style": "British, professional",
    },
    {
        "voice_id": "en-GB-SoniaNeural",
        "name": "Sonia",
        "gender": "Female",
        "locale": "en-GB",
        "style": "British, elegant",
    },
    {
        "voice_id": "en-GB-ThomasNeural",
        "name": "Thomas",
        "gender": "Male",
        "locale": "en-GB",
        "style": "British, authoritative",
    },
    {
        "voice_id": "en-GB-LibbyNeural",
        "name": "Libby",
        "gender": "Female",
        "locale": "en-GB",
        "style": "British, warm narrator",
    },
    {
        "voice_id": "en-GB-MaisieNeural",
        "name": "Maisie",
        "gender": "Female",
        "locale": "en-GB",
        "style": "British, young cheerful",
    },
    # ==================== ENGLISH - OTHER ====================
    {
        "voice_id": "en-AU-NatashaNeural",
        "name": "Natasha",
        "gender": "Female",
        "locale": "en-AU",
        "style": "Australian, friendly",
    },
    {
        "voice_id": "en-IN-NeerjaNeural",
        "name": "Neerja",
        "gender": "Female",
        "locale": "en-IN",
        "style": "Indian English, clear",
    },
    {
        "voice_id": "en-IN-PrabhatNeural",
        "name": "Prabhat",
        "gender": "Male",
        "locale": "en-IN",
        "style": "Indian English, professional",
    },
    {
        "voice_id": "en-IE-ConnorNeural",
        "name": "Connor",
        "gender": "Male",
        "locale": "en-IE",
        "style": "Irish, friendly",
    },
    {
        "voice_id": "en-IE-EmilyNeural",
        "name": "Emily",
        "gender": "Female",
        "locale": "en-IE",
        "style": "Irish, warm",
    },
    {
        "voice_id": "en-CA-ClaraNeural",
        "name": "Clara",
        "gender": "Female",
        "locale": "en-CA",
        "style": "Canadian, friendly",
    },
    {
        "voice_id": "en-CA-LiamNeural",
        "name": "Liam",
        "gender": "Male",
        "locale": "en-CA",
        "style": "Canadian, professional",
    },
    {
        "voice_id": "en-NZ-MitchellNeural",
        "name": "Mitchell",
        "gender": "Male",
        "locale": "en-NZ",
        "style": "New Zealand, casual",
    },
    {
        "voice_id": "en-NZ-MollyNeural",
        "name": "Molly",
        "gender": "Female",
        "locale": "en-NZ",
        "style": "New Zealand, friendly",
    },
    {
        "voice_id": "en-SG-LunaNeural",
        "name": "Luna",
        "gender": "Female",
        "locale": "en-SG",
        "style": "Singaporean, clear",
    },
    {
        "voice_id": "en-SG-WayneNeural",
        "name": "Wayne",
        "gender": "Male",
        "locale": "en-SG",
        "style": "Singaporean, professional",
    },
    {
        "voice_id": "en-ZA-LeahNeural",
        "name": "Leah",
        "gender": "Female",
        "locale": "en-ZA",
        "style": "South African, warm",
    },
    {
        "voice_id": "en-ZA-LukeNeural",
        "name": "Luke",
        "gender": "Male",
        "locale": "en-ZA",
        "style": "South African, friendly",
    },
    # ==================== FILIPINO / TAGALOG ====================
    {
        "voice_id": "fil-PH-AngeloNeural",
        "name": "Angelo",
        "gender": "Male",
        "locale": "fil-PH",
        "style": "Filipino, friendly host",
    },
    {
        "voice_id": "fil-PH-BlessicaNeural",
        "name": "Blessica",
        "gender": "Female",
        "locale": "fil-PH",
        "style": "Filipino, warm and expressive",
    },
]


# Fallback voices if LLM fails (verified to exist)
FALLBACK_VOICES = [
    {"voice_id": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+0%"},
    {"voice_id": "en-US-AriaNeural", "pitch": "+0Hz", "rate": "+0%"},
    {"voice_id": "en-US-BrianNeural", "pitch": "+0Hz", "rate": "+0%"},
    {"voice_id": "en-US-JennyNeural", "pitch": "+0Hz", "rate": "+0%"},
]


async def casting_director_node(state: GraphState) -> GraphState:
    """
    Use LLM to intelligently assign voices to each character.

    Analyzes character names, dialogue content, and personality to select
    the most appropriate voice from available options.
    """
    logger.info("CastingDirector node started", project_id=state["project_id"])

    state["current_step"] = "casting"

    script_json = state["script_json"]
    scenes = script_json.get("scenes", [])

    # Extract unique speakers with their dialogue
    speaker_data = {}
    for scene in scenes:
        speaker = scene.get("speaker", "Unknown")
        if speaker not in speaker_data:
            speaker_data[speaker] = []
        speaker_data[speaker].append(scene.get("line", ""))

    speakers = list(speaker_data.keys())
    cast_assignments = None

    # Check if user specified a voice preference (single-narrator mode)
    voice_preference = state.get("voice_preference")
    if voice_preference:
        # Apply user's voice preference to all speakers
        cast_assignments = {
            speaker: {
                "voice_id": voice_preference["voice_id"],
                "pitch": voice_preference.get("pitch", "+0Hz"),
                "rate": voice_preference.get("rate", "+0%"),
            }
            for speaker in speakers
        }
        logger.info(
            "Using user-specified voice preference",
            project_id=state["project_id"],
            voice_id=voice_preference["voice_id"],
            speaker_count=len(speakers),
        )
    else:
        # Use LLM to select voices for multi-character scripts
        try:
            cast_assignments = await _llm_select_voices(speaker_data)

            if cast_assignments:
                logger.info(
                    "LLM casting completed",
                    project_id=state["project_id"],
                    characters=list(cast_assignments.keys()),
                )

        except Exception as e:
            error_msg = f"LLM casting failed: {str(e)}"
            logger.warning(error_msg, project_id=state["project_id"])
            state["errors"].append(error_msg)

        # If LLM failed or returned empty, use fallback
        if not cast_assignments:
            logger.info("Using fallback casting", project_id=state["project_id"])
            cast_assignments = _fallback_casting(speakers)

    # Ensure all speakers have an assignment
    for speaker in speakers:
        if speaker not in cast_assignments:
            # Assign a default voice if missing
            cast_assignments[speaker] = {
                "voice_id": "en-US-GuyNeural",
                "pitch": "+0Hz",
                "rate": "+0%",
            }

    # Save to database (always runs)
    try:
        async with get_session_context() as session:
            from app.models import Project
            from uuid import UUID as UUIDType

            project = await session.get(Project, UUIDType(state["project_id"]))
            if project:
                project.status = ProjectStatus.GENERATING_AUDIO
                session.add(project)

            cast = Cast(
                id=uuid4(), project_id=state["project_id"], assignments=cast_assignments
            )
            session.add(cast)
            await session.commit()

            logger.info(
                "Cast saved to database",
                project_id=state["project_id"],
                assignments=cast_assignments,
            )

    except Exception as e:
        error_msg = f"Failed to save cast: {str(e)}"
        logger.error(error_msg, project_id=state["project_id"])
        state["errors"].append(error_msg)

    state["cast_list"] = cast_assignments
    state["progress"] = 0.3

    return state


async def _llm_select_voices(
    speaker_data: Dict[str, List[str]],
) -> Dict[str, Dict[str, str]]:
    """
    Use Groq LLM to intelligently select voices for each character.
    """
    # Build voice options summary for the prompt
    voice_options = "\n".join(
        [
            f"- {v['voice_id']}: {v['name']} ({v['gender']}, {v['locale']}) - {v['style']}"
            for v in AVAILABLE_VOICES
        ]
    )

    # Build character summary
    character_summaries = []
    for speaker, lines in speaker_data.items():
        sample_lines = lines[:3]  # First 3 lines as sample
        character_summaries.append(
            f"Character: {speaker}\nSample dialogue:\n"
            + "\n".join(f'  "{line}"' for line in sample_lines)
        )

    prompt = f"""You are a professional voice casting director. Analyze these characters and their dialogue, then assign the most appropriate voice from the available options.

AVAILABLE VOICES:
{voice_options}

CHARACTERS TO CAST:
{chr(10).join(character_summaries)}

For each character, select a voice that matches:
1. The character's name and apparent personality based on their name and dialogue
2. The tone and style of their speech
3. Ensure voice variety - don't assign the same voice to multiple characters
4. If the user specified a voice and pitch, use it directly

Also suggest pitch and rate adjustments:
- pitch: from -10Hz to +10Hz (negative = deeper, positive = higher)
- rate: from -20% to +30% (negative = slower, positive = faster)

Respond with ONLY a valid JSON object in this exact format (no markdown):
{{
  "CharacterName": {{
    "voice_id": "exact-voice-id-from-list",
    "pitch": "+0Hz",
    "rate": "+0%",
    "reasoning": "brief explanation"
  }}
}}
"""

    try:
        logger.info("Calling LLM for voice casting", speakers=list(speaker_data.keys()))
        response = await groq_service.generate_raw(prompt)

        logger.debug("LLM response received", response_length=len(response))

        # Clean response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            parts = response.split("```")
            if len(parts) >= 2:
                response = parts[1]
                if response.startswith("json"):
                    response = response[4:]
        response = response.strip()

        # Try to find JSON in the response
        if not response.startswith("{"):
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                response = response[start_idx:end_idx]

        casting_data = json.loads(response)

        logger.info("LLM casting parsed successfully", cast_count=len(casting_data))

        # Validate and extract assignments
        assignments = {}
        used_voices = set()
        valid_ids = [v["voice_id"] for v in AVAILABLE_VOICES]

        for character, data in casting_data.items():
            voice_id = data.get("voice_id", "")

            # Validate voice exists
            if voice_id not in valid_ids:
                logger.warning(f"Invalid voice_id from LLM: {voice_id}, using fallback")
                voice_id = FALLBACK_VOICES[len(assignments) % len(FALLBACK_VOICES)][
                    "voice_id"
                ]

            # Ensure no duplicate voices
            if voice_id in used_voices:
                for fallback in AVAILABLE_VOICES:
                    if fallback["voice_id"] not in used_voices:
                        voice_id = fallback["voice_id"]
                        break

            used_voices.add(voice_id)

            assignments[character] = {
                "voice_id": voice_id,
                "pitch": data.get("pitch", "+0Hz"),
                "rate": data.get("rate", "+0%"),
            }

        return assignments

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse LLM JSON response",
            error=str(e),
            response_preview=response[:200] if response else "empty",
        )
        return {}
    except Exception as e:
        logger.error("LLM voice selection failed", error=str(e))
        return {}


def _fallback_casting(speakers: List[str]) -> Dict[str, Dict[str, str]]:
    """Fallback casting when LLM fails."""
    assignments = {}
    for i, speaker in enumerate(speakers):
        voice = FALLBACK_VOICES[i % len(FALLBACK_VOICES)]
        assignments[speaker] = voice.copy()
    return assignments

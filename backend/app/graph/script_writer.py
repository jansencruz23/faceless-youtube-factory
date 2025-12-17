"""
ScriptWriter Node - Generates video script using Groq LLM.
"""
from typing import Dict, Any
from uuid import uuid4

from app.graph.state import GraphState
from app.services.groq_service import groq_service
from app.models import Script, ProjectStatus
from app.database import get_session_context
from app.utils.logging import get_logger
from sqlmodel import select

logger = get_logger(__name__)

MAX_RETRIES = 3


async def script_writer_node(state: GraphState) -> GraphState:
    """
    Generate a video script from the user's prompt.

    Updates:
    - script_json: The generated script structure
    - errors: Any errors encountered
    - retry_count: Increment on failure
    - progress: Updated to 0.2 on success
    """
    logger.info(
        "ScriptWriter node started",
        project_id=state["project_id"],
        prompt_preview=state["script_prompt"][:50]
    )

    state["current_step"] = "generating_script"

    try:
        # Generate script using Groq
        script_json = await groq_service.generate_script(state["script_prompt"])

        # Validate structure
        if not script_json.get("scenes"):
            raise ValueError("Generated script missing 'scenes' field")
        
        # Validate each scene
        for i, scene in enumerate(script_json["scenes"]):
            if "speaker" not in scene or "line" not in scene:
                raise ValueError(f"Scene {i} missing required fields")
            # Set default duration if missing
            if "duration" not in scene:
                scene["duration"] = 3.0

        # Save to database
        async with get_session_context() as session:
            # Check for existing script (versioning)
            from app.models import Script, Project

            # Update project status
            project = await session.get(Projec, state["project_id"])
            if project:
                project.status = ProjectStatus.CASTING
                session.add(project)

            # Create new script record
            script = Script(
                id=uuid4(),
                project_id=state["project_id"],
                content=script_json,
                version=1
            )
            session.add(script)
            await session.commit()

        state["script_json"] = script_json
        state["progress"] = 0.2

        logger.info(
            "Script generated successfully",
            project_id=state["project_id"],
            scene_count=len(script_json["scenes"])
        )

    except Exception as e:
        error_msg = f"Script generation failed: {str(e)}"
        logger.error(error_msg, project_id=state["project_id"])

        state["errors"].append(error_msg)
        state["retry_count"] = state.get("retry_count", 0) + 1

        # Update project status on final failure
        if state["retry_count"] >= MAX_RETRIES:
            async with get_session_context() as session:
                from app.models import Project
                project = await session.get(Project, state["project_id"])
                if project:
                    project.status = ProjectStatus.FAILED
                    project.error_message = error_msg
                    session.add(project)
                    await session.commit()

    return state

    def should_continue_after_script(state: GraphState) -> str:
        """
        Conditional edge: Decide next step after script generation.
        
        Returns:
        - "casting_director" if script was generated successfully
        - "end" if max retries exceeded
        - "script_writer" to retry on failure
        """
        if state.get("script_json") and state["script_json"].get("scenes"):
            return "casting_director" 

        if state.get("retry_count", 0) >= MAX_RETRIES:
            logger.warning("Max retries exceeded", project_id=state["project_id"])
            return "end"

        # Retry
        return "script_writer"
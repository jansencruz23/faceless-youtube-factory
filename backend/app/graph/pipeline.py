"""
LangGraph pipeline assembly.
Defines the complete workflow graph.
"""
from langgraph.graph import StateGraph, END

from app.graph.state import GraphState
from app.graph.nodes.script_writer import (
    script_writer_node, 
    should_continue_after_script
)
from app.graph.nodes.casting_director import casting_director_node
from app.graph.nodes.audio_generator import (
    audio_generator_node, 
    should_continue_after_audio
)
from app.graph.nodes.video_composer import (
    video_composer_node, 
    should_upload_to_youtube
)
from app.graph.nodes.youtube_uploader import youtube_uploader_node
from app.utils.logging import get_logger

logger = get_logger(__name__)


def create_pipeline() -> StateGraph:
    """
    Create and return the video generation pipeline.
    
    Flow:
    1. ScriptWriter -> (success) -> CastingDirector
                    -> (max retries) -> END
                    -> (error) -> ScriptWriter (retry)
    
    2. CastingDirector -> AudioGenerator
    
    3. AudioGenerator -> (has audio) -> VideoComposer
                      -> (no audio) -> END
    
    4. VideoComposer -> (auto_upload + metadata) -> YouTubeUploader
                     -> (no upload) -> END
    
    5. YouTubeUploader -> END
    """
    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("script_writer", script_writer_node)
    workflow.add_node("casting_director", casting_director_node)
    workflow.add_node("audio_generator", audio_generator_node)
    workflow.add_node("video_composer", video_composer_node)
    workflow.add_node("youtube_uploader", youtube_uploader_node)

    # Set entry point
    workflow.set_entry_point("script_writer")

    # Add conditional edges
    workflow.add_conditional_edges(
        "script_writer",
        should_continue_after_script,
        {
            "casting_director": "casting_director",
            "script_writer": "script_writer",  # Retry
            "end": END
        }
    )

    # CastingDirector always goes to AudioGenerator
    workflow.add_edge("casting_director", "audio_generator")

    # AudioGenerator conditional
    workflow.add_conditional_edges(
        "audio_generator",
        should_continue_after_audio,
        {
            "video_composer": "video_composer",
            "end": END
        }
    )

    # VideoComposer conditional (YouTube upload)
    workflow.add_conditional_edges(
        "video_composer",
        should_upload_to_youtube,
        {
            "youtube_uploader": "youtube_uploader",
            "end": END
        }
    )

    # YouTubeUploader always ends
    workflow.add_edge("youtube_uploader", END)

    return workflow


# Compile the graph for execution
video_pipeline = create_pipeline().compile()

async def run_pipeline(
    project_id: str,
    user_id: str,
    script_prompt: str,
    auto_upload: bool = False,
    youtube_metadata: dict = None
) -> GraphState:
    """
    Execute the video generation pipeline.
    
    Args:
        project_id: UUID of the project
        user_id: UUID of the user
        script_prompt: User's prompt for script generation
        auto_upload: Whether to auto-upload to YouTube
        youtube_metadata: YouTube video metadata (if auto_upload is True)
    
    Returns:
        Final GraphState with all generated data
    """
    logger.info(
        "Starting pipeline",
        project_id=project_id,
        auto_upload=auto_upload
    )

    # Initialize state
    initial_state: GraphState = {
        "project_id": project_id,
        "user_id": user_id,
        "script_prompt": script_prompt,
        "auto_upload": auto_upload,
        "script_json": None,
        "cast_list": None,
        "audio_files": [],
        "video_path": None,
        "youtube_metadata": youtube_metadata,
        "youtube_video_id": None,
        "errors": [],
        "retry_count": 0,
        "current_step": "initializing",
        "progress": 0.0
    }

    # Run the pipeline
    final_state = await video_pipeline.ainvoke(initial_state)

    logger.info(
        "Pipeline completed",
        project_id=project_id,
        final_step=final_state.get("current_step"),
        errors=len(final_state.get("errors", []))
    )

    return final_state
"""
Image generation service using Flux Schnell.
"""
import asyncio
import gc
import torch
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from PIL import UnidentifiedImageError

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Limit concurrent image generation
image_executor = ThreadPoolExecutor(max_workers=1)


class ImageService:
    """Service for generating images using Flux Schnell."""

    def __init__(self):
        self.output_dir = Path(settings.static_dir) / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pipe = None
        self._model_loaded = False

    def _load_model(self):
        """Lazy load the Flux model to save VRAM when not in use."""
        if self._model_loaded:
            return

        try:
            from diffusers import FluxPipeline

            logger.info("Loading Flux Schnell model...")

            self.pipe = FluxPipeline.from_pretrained(
                settings.flux_model,
                torch_dtype=torch.bfloat16
            )

            # Enable memory optimizations
            self.pipe.enable_model_cpu_offload()

            # Optional: Enable attention slicing for lower VRAM
            # self.pipe.enable_attention_slicing()

            self._model_loaded = True
            logger.info("Flux Schnell model loaded successfully")

        except Exception as e:
            logger.error("Failed to load Flux Schnell model", error=str(e))
            raise

    def _unload_model(self):
        """Unload model to free VRAM."""
        if self.pipe is not None:
            del self.pipe
            self._model_loaded = False
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Flux model unloaded")

    def _generate_sync(
        self,
        prompt: str,
        output_path: Path,
        width: int=1280,
        height: int=720,
        num_steps: int=4
    ) -> str:
        """Synchronous image generation (runs in thread pool)."""
        self._load_model()

        try:
            logger.info(f"Generating image: {prompt[:50]}...")
            
            image = self.pipe(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=num_steps,
                guidance_scale=0.0
            ).images[0]

            # Save image
            image.save(str(output_path), quality=95)

            logger.info(f"Image saved: {output_path}")

            # Return relative path
            relative_path = output_path.relative_to(Path(settings.static_dir))
            return str(relative_path).replace("\\", "/")

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise

    async def generate_scene_image(
        self,
        project_id: str,
        scene_id: str,
        prompt: str
    ) -> str:
        """
        Generate an image for a scene.

        Args:
            project_id: Project UUID
            scene_id: Scene index
            prompt: Image generation prompt

        Returns:
            str: Relative path to generated image
        """
        # Create project directory
        project_dir = self.output_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = project_dir / f"{scene_id}.png"

        loop = asyncio.get_running_loop()

        result = await loop.run_in_executor(
            image_executor,
            self._generate_sync,
            prompt,
            output_path,
            settings.image_width,
            settings.image_height,
            settings.image_num_steps
        )

        return result

    async def generate_batch(
        self,
        project_id: str,
        prompts: list[str]
    ) -> list[str]:
        """Generate multiple images for a project."""
        paths = []
        for i, prompt in enumerate(prompts):
            try:
                path = await self.generate_scene_image(
                    project_id=project_id,
                    scene_id=str(i),
                    prompt=prompt
                )
                paths.append(path)
            except Exception as e:
                logger.error(f"Failed to generate image for scene {i}: {e}")
                paths.append(None)
        
        # Unload model after batch to free VRAM
        self._unload_model()
        
        return paths

# Singleton instance
image_service = ImageService()
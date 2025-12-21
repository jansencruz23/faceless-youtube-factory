"""
Image generation service using Stable Diffusion XL.
"""

import asyncio
import gc
import torch
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Limit concurrent image generation
image_executor = ThreadPoolExecutor(max_workers=1)


class ImageService:
    """Service for generating images using Stable Diffusion XL."""

    def __init__(self):
        self.output_dir = Path(settings.static_dir) / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pipe = None
        self._model_loaded = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Log GPU status on initialization
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"GPU available: {gpu_name} ({gpu_memory:.1f} GB VRAM)")
        else:
            logger.warning(
                "No GPU available! Image generation will be VERY slow on CPU."
            )

    def _load_model(self):
        """Lazy load the SDXL model to save VRAM when not in use."""
        if self._model_loaded:
            return

        import time

        try:
            from diffusers import StableDiffusionXLPipeline

            logger.info(
                f"Loading Stable Diffusion XL model on {self.device.upper()}..."
            )
            logger.info(
                "This may take 10-30 minutes on first run (downloading ~6.5GB model)..."
            )

            start_time = time.time()

            if self.device == "cuda":
                self.pipe = StableDiffusionXLPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-xl-base-1.0",
                    torch_dtype=torch.float16,
                    use_safetensors=True,
                    variant="fp16",
                )

                download_time = time.time() - start_time
                logger.info(
                    f"Model downloaded/loaded from cache in {download_time:.1f}s"
                )

                logger.info("Moving model to GPU...")
                self.pipe = self.pipe.to("cuda")
                self.pipe.enable_attention_slicing()

                # Log VRAM usage after loading
                allocated = torch.cuda.memory_allocated(0) / (1024**3)
                logger.info(f"Model on GPU. VRAM used: {allocated:.2f} GB")
            else:
                # CPU fallback (very slow)
                self.pipe = StableDiffusionXLPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-xl-base-1.0",
                    torch_dtype=torch.float32,
                    use_safetensors=True,
                )

            total_time = time.time() - start_time
            self._model_loaded = True
            logger.info(f"SDXL model ready! Total load time: {total_time:.1f}s")

        except Exception as e:
            logger.error("Failed to load SDXL model", error=str(e))
            raise

    def _unload_model(self):
        """Unload model to free VRAM."""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
            self._model_loaded = False
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("SDXL model unloaded")

    def _generate_sync(
        self,
        prompt: str,
        output_path: Path,
        width: int = 1280,
        height: int = 720,
        num_steps: int = 20,
    ) -> str:
        """Synchronous image generation (runs in thread pool)."""
        self._load_model()

        import time

        try:
            logger.info(f"Generating image: {prompt[:50]}...")
            start_time = time.time()

            image = self.pipe(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=num_steps,
                guidance_scale=7.5,
            ).images[0]

            gen_time = time.time() - start_time
            logger.info(f"Image generated in {gen_time:.1f}s")

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
        self, project_id: str, scene_id: str, prompt: str
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
            settings.image_num_steps,
        )

        return result

    async def generate_batch(self, project_id: str, prompts: list[str]) -> list[str]:
        """Generate multiple images for a project."""
        paths = []
        for i, prompt in enumerate(prompts):
            try:
                path = await self.generate_scene_image(
                    project_id=project_id, scene_id=str(i), prompt=prompt
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

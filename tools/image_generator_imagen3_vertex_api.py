"""
Image Generator for Google Vertex AI Imagen 3
Adapter for ViMax pipeline to use Vertex AI Imagen 3 API
"""

import logging
import asyncio
from typing import List, Optional
from PIL import Image
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel, Image as VertexImage
from interfaces.image_output import ImageOutput
from utils.rate_limiter import RateLimiter


class ImageGeneratorImagen3VertexAPI:
    """
    Image generator using Google Vertex AI Imagen 3.

    Setup:
        1. Install: pip install google-cloud-aiplatform
        2. Authenticate: gcloud auth application-default login
        3. Set project: gcloud config set project YOUR_PROJECT_ID

    Args:
        project_id: Your Google Cloud project ID
        location: Vertex AI location (default: "us-central1")
        rate_limiter: Optional rate limiter instance
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "imagen-3.0-generate-001",
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.rate_limiter = rate_limiter

        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = ImageGenerationModel.from_pretrained(model_name)

        logging.info(f"Initialized Vertex AI Imagen 3: {model_name}")

    async def generate_single_image(
        self,
        prompt: str,
        reference_image_paths: List[str] = [],
        aspect_ratio: Optional[str] = "16:9",
        size: Optional[str] = None,  # For compatibility
        **kwargs,
    ) -> ImageOutput:
        """
        Generate a single image using Vertex AI Imagen 3.

        Args:
            prompt: Text prompt for image generation
            reference_image_paths: List of reference image paths (Imagen 3 supports multiple references)
            aspect_ratio: Aspect ratio (16:9, 4:3, 1:1, etc.)
            size: Ignored - kept for compatibility with other generators

        Returns:
            ImageOutput object containing the generated image
        """
        logging.info(f"Calling Vertex AI Imagen 3 to generate image...")

        # Apply rate limiting if configured
        if self.rate_limiter:
            await self.rate_limiter.acquire()

        # Load reference images if provided
        reference_images = []
        if reference_image_paths:
            for path in reference_image_paths:
                ref_image = VertexImage.load_from_file(path)
                reference_images.append(ref_image)
            logging.info(f"Using {len(reference_images)} reference images")

        # Prepare generation parameters
        generation_params = {
            "prompt": prompt,
            "number_of_images": 1,
            "aspect_ratio": aspect_ratio,
            "safety_filter_level": "block_some",
            "person_generation": "allow_adult",
        }

        # Add reference images if available
        if reference_images:
            # For Imagen 3, use edit mode with reference image
            generation_params["base_image"] = reference_images[0]
            generation_params["edit_mode"] = "inpaint-insert"  # or "outpaint" depending on use case

        # Retry logic for transient errors
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                # Run synchronous Vertex AI call in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_images(**generation_params)
                )
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logging.warning(f"Error generating image: {e}. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logging.error(f"Failed to generate image after {max_retries} attempts: {e}")
                    raise

        # Extract the generated image
        if not response or not response.images:
            raise ValueError("No image generated from Vertex AI Imagen 3")

        generated_image = response.images[0]

        # Convert to PIL Image
        pil_image = generated_image._pil_image

        logging.info(f"Successfully generated image with Vertex AI Imagen 3")

        return ImageOutput(fmt="pil", ext="png", data=pil_image)

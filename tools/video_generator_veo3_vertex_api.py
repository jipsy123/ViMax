"""
Video Generator for Google Vertex AI Veo 3
Adapter for ViMax pipeline to use Vertex AI Veo 3 API
"""

import logging
import asyncio
import time
from typing import List, Optional, Literal
import vertexai
from vertexai.preview.vision_models import VideoGenerationModel, Image as VertexImage
from interfaces.video_output import VideoOutput
from utils.rate_limiter import RateLimiter


class VideoGeneratorVeo3VertexAPI:
    """
    Video generator using Google Vertex AI Veo 3.

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
        t2v_model: str = "veo-3-001",
        ff2v_model: str = "veo-3-001",
        flf2v_model: str = "veo-3-001",
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.project_id = project_id
        self.location = location
        self.t2v_model = t2v_model
        self.ff2v_model = ff2v_model
        self.flf2v_model = flf2v_model
        self.rate_limiter = rate_limiter

        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        self.model = VideoGenerationModel.from_pretrained(t2v_model)

        logging.info(f"Initialized Vertex AI Veo 3: {t2v_model}")

    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: List[str],
        resolution: str = "1080p",
        aspect_ratio: str = "16:9",
        duration: int = 8,
    ) -> VideoOutput:
        """
        Generate a single video using Vertex AI Veo 3.

        Args:
            prompt: Text prompt for video generation
            reference_image_paths: List of 0, 1, or 2 reference images
                - 0 images: Text-to-video
                - 1 image: First frame to video
                - 2 images: First + last frame to video (keyframe interpolation)
            resolution: Video resolution (1080p, 720p, 480p)
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1, etc.)
            duration: Video duration in seconds (max depends on model)

        Returns:
            VideoOutput object containing the generated video bytes
        """
        # Determine generation mode based on reference images
        num_refs = len(reference_image_paths)

        if num_refs == 0:
            model_name = self.t2v_model
            mode = "text-to-video"
        elif num_refs == 1:
            model_name = self.ff2v_model
            mode = "image-to-video"
        elif num_refs == 2:
            model_name = self.flf2v_model
            mode = "keyframe-to-video"
        else:
            raise ValueError(f"Invalid number of reference images: {num_refs}. Must be 0, 1, or 2.")

        logging.info(f"Calling Vertex AI Veo 3 ({mode}) to generate video...")

        # Apply rate limiting if configured
        if self.rate_limiter:
            await self.rate_limiter.acquire()

        # Load reference images if provided
        reference_images = []
        if num_refs > 0:
            for path in reference_image_paths:
                ref_image = VertexImage.load_from_file(path)
                reference_images.append(ref_image)
            logging.info(f"Using {len(reference_images)} reference images for {mode}")

        # Prepare generation parameters
        generation_params = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        }

        # Add reference images based on mode
        if num_refs == 1:
            generation_params["reference_image"] = reference_images[0]
        elif num_refs == 2:
            generation_params["start_image"] = reference_images[0]
            generation_params["end_image"] = reference_images[1]

        # Retry logic for transient errors and rate limits
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                # Run synchronous Vertex AI call in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_videos(**generation_params)
                )
                break
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logging.warning(f"Rate limit hit, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
                else:
                    logging.error(f"Error generating video: {e}")
                    raise

        # Wait for video generation to complete (Vertex AI uses async operations)
        if not response:
            raise RuntimeError("No response received from Vertex AI Veo 3")

        # Check if we need to poll for completion
        if hasattr(response, 'operation'):
            operation = response.operation
            logging.info("Video generation started, polling for completion...")

            while not operation.done():
                await asyncio.sleep(2)
                loop = asyncio.get_event_loop()
                operation = await loop.run_in_executor(
                    None,
                    lambda: operation
                )
                logging.info(f"Video generation in progress...")

            # Check for errors
            if operation.error:
                error_msg = f"Video generation failed: {operation.error}"
                logging.error(error_msg)
                raise RuntimeError(error_msg)

            # Get the result
            result = operation.result()
        else:
            result = response

        # Extract video data
        if not result or not hasattr(result, 'generated_videos') or not result.generated_videos:
            raise RuntimeError("Video generation completed but no videos were generated")

        generated_video = result.generated_videos[0]

        # Get video bytes
        # Vertex AI returns video data, extract bytes
        if hasattr(generated_video, 'video_bytes'):
            video_bytes = generated_video.video_bytes
        elif hasattr(generated_video, 'gcs_uri'):
            # If stored in GCS, download it
            from google.cloud import storage
            logging.info(f"Downloading video from GCS: {generated_video.gcs_uri}")

            # Parse GCS URI
            gcs_uri = generated_video.gcs_uri
            bucket_name = gcs_uri.split('/')[2]
            blob_name = '/'.join(gcs_uri.split('/')[3:])

            # Download
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            loop = asyncio.get_event_loop()
            video_bytes = await loop.run_in_executor(
                None,
                blob.download_as_bytes
            )
        else:
            raise RuntimeError("Unable to extract video data from Vertex AI response")

        logging.info(f"Successfully generated video with Vertex AI Veo 3 ({mode})")

        return VideoOutput(
            fmt="bytes",
            ext="mp4",
            data=video_bytes,
        )

"""
ViMax Idea-to-Video with Google Vertex AI
Uses Vertex AI Veo 3 + Imagen 3 for long video generation
"""

import asyncio
from pipelines.idea2video_pipeline import Idea2VideoPipeline


# SET YOUR OWN IDEA, USER REQUIREMENT, AND STYLE HERE
idea = \
    """
A detective cat discovers a mysterious glowing toy in an abandoned Victorian mansion.
She cautiously investigates room by room, her silhouette moving through moonlit corridors.
Each room reveals more clues about the toy's origin.
The tension builds as she approaches the final room where the truth awaits.
"""

user_requirement = \
    """
For adults, create exactly 3 scenes with cinematic pacing.
Each scene should have 5-7 shots to build suspense.
Use varied camera angles and movements.
"""

style = "Film noir, moody lighting, dramatic shadows, cinematic composition"


async def main():
    # Load Vertex AI configuration
    pipeline = Idea2VideoPipeline.init_from_config(
        config_path="configs/idea2video_vertex.yaml"
    )

    # Generate video using ViMax's multi-agent architecture + Vertex AI APIs
    await pipeline(
        idea=idea,
        user_requirement=user_requirement,
        style=style
    )

    print("\n" + "="*60)
    print("✅ Video generation complete!")
    print("Check the output in: .working_dir/idea2video_vertex/")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

"""
Example: Using Custom Character Images (Your Own Photos/Portraits)

ViMax supports providing your own reference images instead of AI-generating them.
This is perfect for:
- Using real people's photos
- Brand mascots/characters
- Consistent character designs from existing artwork
"""

import asyncio
from pipelines.script2video_pipeline import Script2VideoPipeline
from interfaces import CharacterInScene


# ==========================================
# Option 1: Provide Your Own Character Portraits
# ==========================================

async def main():
    # Initialize pipeline
    pipeline = Script2VideoPipeline.init_from_config(
        config_path="configs/script2video_vertex.yaml"
    )

    # Your script
    script = """
    EXT. SPACEX OFFICE - NIGHT

    ELON MUSK stands on a balcony, gazing at Mars in the night sky.
    He holds a rolled-up rocket sketch, dreaming of making humanity multi-planetary.

    ELON: (to himself) We're going to make it happen.
    """

    # Define characters (same as script)
    characters = [
        CharacterInScene(
            idx=0,
            identifier_in_scene="ELON MUSK",
            description="Male, 40s, determined expression, casual business attire"
        )
    ]

    # ===== KEY PART: Provide your own images =====
    character_portraits_registry = {
        "ELON MUSK": {
            "front": {
                "path": "/path/to/your/elon_front.jpg",  # Your actual photo
                "description": "Front view of Elon Musk"
            },
            "side": {
                "path": "/path/to/your/elon_side.jpg",   # Your actual photo
                "description": "Side profile of Elon Musk"
            },
            "back": {
                "path": "/path/to/your/elon_back.jpg",   # Your actual photo
                "description": "Back view of Elon Musk"
            }
        }
    }
    # =============================================

    # Generate video using YOUR images for character consistency
    await pipeline(
        script=script,
        user_requirement="Cinematic, 5-7 shots",
        style="Documentary style",
        characters=characters,  # Pass characters
        character_portraits_registry=character_portraits_registry  # Pass YOUR images!
    )

    print("✅ Video generated using your custom character images!")


if __name__ == "__main__":
    asyncio.run(main())

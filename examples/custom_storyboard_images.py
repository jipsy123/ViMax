"""
Example: Using Storyboard Images as References

This advanced example shows how to use your own storyboard sketches/images
to guide the frame generation process.

Perfect for:
- Converting hand-drawn storyboards to video
- Using concept art as reference
- Matching specific visual styles from reference images
"""

import asyncio
import json
import os
from pipelines.script2video_pipeline import Script2VideoPipeline
from interfaces import CharacterInScene


# ==========================================
# Option 2: Use Storyboard Images as References
# ==========================================

async def main():
    """
    Use your own storyboard panels/sketches to guide video generation.

    How it works:
    1. You provide storyboard panel images (your sketches, mockups, or reference art)
    2. ViMax uses these as reference images when generating frames
    3. The AI tries to match the composition/style of your references
    """

    # Initialize pipeline
    pipeline = Script2VideoPipeline.init_from_config(
        config_path="configs/script2video_vertex.yaml"
    )

    # Your storyboard images (paths to your actual files)
    storyboard_references = {
        "panel_1_vision": "/path/to/your/storyboard_panel_1.jpg",      # Elon gazing at Mars
        "panel_2_garage": "/path/to/your/storyboard_panel_2.jpg",      # Team around whiteboard
        "panel_3_explosion": "/path/to/your/storyboard_panel_3.jpg",   # Rocket exploding
        # ... etc for all your panels
    }

    # Define characters with YOUR reference photos
    characters = [
        CharacterInScene(
            idx=0,
            identifier_in_scene="ELON MUSK",
            description="Male, 40s, based on provided reference images"
        ),
        CharacterInScene(
            idx=1,
            identifier_in_scene="ENGINEERS",
            description="Team of engineers, based on provided reference images"
        )
    ]

    # Character portraits (your actual photos/drawings)
    character_portraits_registry = {
        "ELON MUSK": {
            "front": {
                "path": "/path/to/character_refs/elon_front.jpg",
                "description": "Front view reference of Elon character design"
            },
            "side": {
                "path": "/path/to/character_refs/elon_side.jpg",
                "description": "Side view reference of Elon character design"
            },
            "back": {
                "path": "/path/to/character_refs/elon_back.jpg",
                "description": "Back view reference of Elon character design"
            }
        },
        "ENGINEERS": {
            "front": {
                "path": "/path/to/character_refs/engineers_front.jpg",
                "description": "Engineer team reference image"
            },
            "side": {
                "path": "/path/to/character_refs/engineers_side.jpg",
                "description": "Engineer team side reference"
            },
            "back": {
                "path": "/path/to/character_refs/engineers_back.jpg",
                "description": "Engineer team back reference"
            }
        }
    }

    # Advanced: Manually inject storyboard images as first frames
    # This requires saving them to the working directory structure

    pipeline.working_dir = ".working_dir/custom_storyboard_refs"
    os.makedirs(pipeline.working_dir, exist_ok=True)

    # Save character portraits registry
    portraits_path = os.path.join(pipeline.working_dir, "character_portraits_registry.json")
    with open(portraits_path, 'w') as f:
        json.dump(character_portraits_registry, f, indent=2)

    # For each shot, you can pre-place storyboard images as references
    # The pipeline will use them when generating frames
    shots_dir = os.path.join(pipeline.working_dir, "shots")
    os.makedirs(shots_dir, exist_ok=True)

    # Example: Pre-place your storyboard sketch as shot 0's reference
    shot_0_dir = os.path.join(shots_dir, "0")
    os.makedirs(shot_0_dir, exist_ok=True)

    # Copy your storyboard panel to be used as reference
    import shutil
    if os.path.exists(storyboard_references["panel_1_vision"]):
        shutil.copy(
            storyboard_references["panel_1_vision"],
            os.path.join(shot_0_dir, "storyboard_reference.png")
        )

    # Your script describing the storyboard
    script = """
    EXT. OFFICE BALCONY - NIGHT

    ELON MUSK stands on balcony gazing at Mars.
    [Shot composition should match storyboard panel 1]

    INT. WAREHOUSE - DAY

    ELON MUSK and ENGINEERS huddle around whiteboard.
    [Shot composition should match storyboard panel 2]

    EXT. LAUNCHPAD - DAY

    Falcon 1 rocket EXPLODES after liftoff.
    [Shot composition should match storyboard panel 3]
    """

    user_requirement = """
    Use the provided storyboard reference images to guide composition.
    Match the camera angles and framing from the reference panels.
    Maintain consistency with the character reference images.
    """

    # Generate video using YOUR storyboard images as reference
    await pipeline(
        script=script,
        user_requirement=user_requirement,
        style="Match the visual style of the provided storyboard references",
        characters=characters,
        character_portraits_registry=character_portraits_registry
    )

    print("✅ Video generated using your storyboard images as reference!")
    print(f"Output in: {pipeline.working_dir}")


if __name__ == "__main__":
    asyncio.run(main())

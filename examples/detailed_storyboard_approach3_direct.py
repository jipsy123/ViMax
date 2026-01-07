"""
Example: Direct storyboard injection (Advanced)

This shows how to bypass ViMax's StoryboardArtist agent entirely and provide
your own pre-planned storyboard structure directly to the pipeline.

WARNING: This is an advanced approach that requires understanding ViMax's
internal data structures. Use this when you have a VERY detailed storyboard
and want pixel-perfect control.
"""

import asyncio
import json
import os
from pipelines.script2video_pipeline import Script2VideoPipeline
from interfaces import ShotBriefDescription, CharacterInScene


# ==========================================
# APPROACH 3: Direct Storyboard Injection
# ==========================================
# Manually create the storyboard data structure
# This bypasses the StoryboardArtist agent completely


def create_spacex_storyboard():
    """
    Manually construct the storyboard matching your exact 3x3 panel layout.
    Each panel becomes a ShotBriefDescription.
    """

    storyboard = [
        # Row 1: The Dream and The Falls

        # Panel 1: The Vision
        ShotBriefDescription(
            idx=0,
            is_last=False,
            cam_idx=0,  # Wide/establishing camera
            visual_desc="""
            A medium close-up shot of a contemplative <ELON MUSK> (30s, determined expression,
            rolled-up sketch in hand) standing on an office balcony at night, gazing thoughtfully
            at a reddish-orange Mars visible in the night sky. The balcony overlooks a city below
            with ambient lights. Soft city light mixed with starlight illuminates his face.
            His expression shows determination and dreams of the future.
            """,
            audio_desc="[Text Overlay] 2002: The Goal is Mars. [Sound] Ambient city night sounds, distant traffic."
        ),

        # Panel 2: The Garage Days
        ShotBriefDescription(
            idx=1,
            is_last=False,
            cam_idx=1,  # Interior workspace camera
            visual_desc="""
            An eye-level shot inside a messy, cramped warehouse converted into a workspace.
            <ELON MUSK> and a group of <ENGINEERS> (5-6 people, diverse, passionate, in casual work clothes)
            huddle around a whiteboard covered in complex rocket equations and diagrams. They argue
            passionately, gesturing at the equations, voices overlapping. The warehouse is cluttered
            with equipment and papers. Functional fluorescent lighting casts harsh shadows.
            """,
            audio_desc="[Sound Effect] Muffled, intense technical chatter and debate."
        ),

        # Panel 3: Failure to Launch
        ShotBriefDescription(
            idx=2,
            is_last=False,
            cam_idx=2,  # Wide exterior launchpad camera
            visual_desc="""
            A wide-angle shot of a Falcon 1 rocket on a tropical launchpad surrounded by palm trees
            and vegetation. The rocket has just lifted off but suddenly EXPLODES violently in mid-air,
            scattering debris across the sky in a fireball. Harsh daylight. Catastrophic moment.
            """,
            audio_desc="[Sound Effect] Massive explosion, debris falling. [Text Overlay] Three consecutive failures. Near bankruptcy."
        ),

        ShotBriefDescription(
            idx=3,
            is_last=False,
            cam_idx=3,  # Control bunker interior camera
            visual_desc="""
            A close-up shot of <ELON MUSK>'s face in a dimly lit control bunker, watching monitors
            displaying the explosion. His expression is devastated, crushed. The glow from the monitors
            illuminates his face with an orange-red tint. Other engineers visible in background, also shocked.
            """,
            audio_desc="[Sound Effect] Alarm sounds, shocked murmurs."
        ),

        # Row 2: The Turning Point

        # Panel 4: The Last Stand
        ShotBriefDescription(
            idx=4,
            is_last=False,
            cam_idx=4,  # Intimate office camera
            visual_desc="""
            A close-up shot of <ELON MUSK> sitting alone at a desk late at night in a dimly lit office.
            The desk is piled high with papers and financial reports. He rubs his temples with both hands,
            head down, exhausted but with a resolved look in his eyes. A single desk lamp casts long shadows
            across the room. The room is otherwise dark.
            """,
            audio_desc="[Sound Effect] A ticking clock in a silent room, emphasizing the pressure."
        ),

        # Panel 5: Orbit Achieved - Launch
        ShotBriefDescription(
            idx=5,
            is_last=False,
            cam_idx=5,  # Low angle exterior launch camera
            visual_desc="""
            A low-angle shot looking up at a Falcon 1 rocket successfully soaring into a crystal clear
            blue sky, leaving a perfect white contrail behind it. The rocket is ascending smoothly.
            Bright sunlight. Triumph in the air. The launch is flawless.
            """,
            audio_desc="[Sound Effect] Roar of rocket engines, successful launch sounds."
        ),

        # Panel 5 continued: Orbit Achieved - Celebration
        ShotBriefDescription(
            idx=6,
            is_last=False,
            cam_idx=6,  # Control room celebration camera
            visual_desc="""
            A medium shot inside the SpaceX control room. <ENGINEERS> are cheering wildly, jumping up,
            hugging each other, some crying with relief. <ELON MUSK> stands among them, smiling genuinely
            for the first time, relief and joy on his face. Monitors in background show successful orbit data.
            Bright interior lighting.
            """,
            audio_desc="[Sound Effect] Cheering, celebratory shouts. [Text Overlay] 2008: Flight 4 reaches orbit. SpaceX is saved."
        ),

        # Panel 6: The Reusable Idea
        ShotBriefDescription(
            idx=7,
            is_last=False,
            cam_idx=7,  # Hangar presentation camera
            visual_desc="""
            A medium-wide shot in a large, modern hangar. <ELON MUSK> stands confidently before a large,
            focused team of <STAFF> (10+ people, attentive, taking notes). Behind him is a giant blueprint
            render of a Falcon 9 rocket with prominent landing legs clearly visible. He gestures energetically
            at the blueprint, explaining the reusability concept. Industrial hangar lighting. The team listens
            intently, focused and inspired by his vision.
            """,
            audio_desc="[Text Overlay] The Next Challenge: Reusability."
        ),

        # Row 3: The Revolution

        # Panel 7: Liftoff
        ShotBriefDescription(
            idx=8,
            is_last=False,
            cam_idx=8,  # Epic launch wide camera
            visual_desc="""
            A majestic wide shot of a massive Falcon 9 rocket lifting off from a launch pad in a powerful,
            fiery display. Huge plumes of smoke and fire billow beneath it. The ground shakes. The rocket
            rises majestically toward space, carrying a commercial payload. Golden hour sunlight creates epic
            backlighting, making the scene awe-inspiring. Scale is emphasized.
            """,
            audio_desc="[Sound Effect] Thunderous roar of rocket engines, ground rumbling."
        ),

        # Panel 8: The Descent
        ShotBriefDescription(
            idx=9,
            is_last=False,
            cam_idx=9,  # Aerial descent camera
            visual_desc="""
            An aerial view looking down from above. The first-stage booster of the Falcon 9 rocket falls back
            through clouds toward Earth, grid fins deployed and steering the massive cylinder precisely.
            Below in the ocean, a tiny droneship with 'Of Course I Still Love You' painted on it waits.
            The booster approaches, engines visible firing for controlled descent. Tense moment.
            Diffused daylight through clouds.
            """,
            audio_desc="[Sound Effect] Intense atmospheric wind noise, engine re-ignition."
        ),

        # Panel 9: Landing the Impossible
        ShotBriefDescription(
            idx=10,
            is_last=True,  # Last shot!
            cam_idx=10,  # Grand finale wide camera
            visual_desc="""
            A grand wide shot of the Falcon 9 booster standing perfectly upright and stable on the deck
            of the droneship 'Of Course I Still Love You' in the middle of the ocean. Smoke rises from
            its base. The sunset creates a heroic silhouette. The ocean stretches to the horizon.
            A historic, triumphant moment captured in golden light. This is history being made.
            """,
            audio_desc="[Text Overlay] 2016: History made. The future is reusable. [Sound Effect] Ocean waves, residual hissing from engines."
        ),
    ]

    return storyboard


def create_spacex_characters():
    """
    Define the characters that appear in the storyboard.
    """
    return [
        CharacterInScene(
            idx=0,
            identifier_in_scene="ELON MUSK",
            description="Male, 30s-40s, determined and visionary expression, casual business attire in early scenes, more professional in later scenes. Intense eyes, focused demeanor."
        ),
        CharacterInScene(
            idx=1,
            identifier_in_scene="ENGINEERS",
            description="Group of diverse engineers, 5-10 people, various ages (20s-40s), casual work clothes (jeans, t-shirts, hoodies), passionate and dedicated, technical mindset."
        ),
        CharacterInScene(
            idx=2,
            identifier_in_scene="STAFF",
            description="SpaceX staff members, professional attire, attentive and focused, taking notes, inspired by the vision."
        ),
    ]


async def main():
    """
    Run the pipeline with pre-defined storyboard, bypassing the StoryboardArtist agent.
    """

    # Initialize pipeline
    pipeline = Script2VideoPipeline.init_from_config(
        config_path="configs/script2video_vertex.yaml"
    )

    # Override working directory for this custom approach
    pipeline.working_dir = ".working_dir/spacex_custom_storyboard"
    os.makedirs(pipeline.working_dir, exist_ok=True)

    # Create your custom storyboard and characters
    storyboard = create_spacex_storyboard()
    characters = create_spacex_characters()

    # Save them to the working directory (so the pipeline can skip generation)
    storyboard_path = os.path.join(pipeline.working_dir, "storyboard.json")
    with open(storyboard_path, 'w', encoding='utf-8') as f:
        json.dump([shot.model_dump() for shot in storyboard], f, ensure_ascii=False, indent=4)
    print(f"✓ Saved custom storyboard to {storyboard_path}")

    characters_path = os.path.join(pipeline.working_dir, "characters.json")
    with open(characters_path, 'w', encoding='utf-8') as f:
        json.dump([char.model_dump() for char in characters], f, ensure_ascii=False, indent=4)
    print(f"✓ Saved custom characters to {characters_path}")

    # Dummy script (required but won't be used for storyboard generation since we pre-created it)
    script = "SpaceX Story - Custom Storyboard (see storyboard.json for details)"

    # User requirement (still affects shot decomposition and video generation)
    user_requirement = \
    """
    IMPORTANT: Use the pre-defined storyboard structure exactly as provided.

    Shot decomposition:
    - Preserve the exact visual descriptions
    - Each shot should capture the dramatic moment described
    - Use variation_type "medium" for most shots (some character/scene changes)
    - Use variation_type "large" for the explosion and landing shots

    Cinematography:
    - Early scenes: Documentary, gritty, tense
    - Middle scenes: Emotional, intimate
    - Final scenes: Epic, heroic, grand
    """

    # Style
    style = "Cinematic, photorealistic, documentary-style evolving to epic space footage"

    # Run the pipeline with pre-defined data
    print("\n" + "="*60)
    print("Starting video generation with custom storyboard...")
    print("="*60 + "\n")

    await pipeline(
        script=script,
        user_requirement=user_requirement,
        style=style,
        # The pipeline will automatically load the pre-saved storyboard and characters
    )

    print("\n" + "="*60)
    print("✅ SpaceX custom storyboard video generation complete!")
    print("Check output in: .working_dir/spacex_custom_storyboard/")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

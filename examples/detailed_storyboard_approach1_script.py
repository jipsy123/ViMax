"""
Example: Converting a detailed storyboard prompt into ViMax-compatible format

This shows how to preserve your detailed planning while working with ViMax's agents.
"""

import asyncio
from pipelines.script2video_pipeline import Script2VideoPipeline


# ==========================================
# APPROACH 1: Script Format with Rich Details
# ==========================================
# Convert each storyboard panel into a scene description
# Let ViMax's agents handle shot planning, but guide them with rich details

script = \
"""
EXT. OFFICE BALCONY - NIGHT (2002)

A younger ELON MUSK (30s, contemplative, determined) stands alone on an office balcony gazing up at the night sky. He holds a rolled-up sketch. Above him, a small reddish dot of Mars glows faintly among the stars. The city lights below cast a soft ambient glow. He looks determined, dreaming of the future.

TEXT OVERLAY: "2002: The Goal is Mars."


INT. CONVERTED WAREHOUSE - DAY

Inside a messy, cramped warehouse cluttered with equipment and papers, ELON MUSK and a small team of ENGINEERS (5-6 people, diverse, passionate) huddle around a whiteboard covered in complex rocket equations. They argue passionately, gesturing at diagrams, voices overlapping in intense technical debate. Fluorescent lights cast harsh shadows.

SOUND: Muffled, intense technical chatter.


EXT. TROPICAL LAUNCHPAD - DAY

A Falcon 1 rocket stands tall on a launch pad surrounded by tropical vegetation. The rocket ignites, begins to lift off—then suddenly EXPLODES violently, scattering debris across the sky.

INTERCUT: Control bunker - Elon Musk watches monitors, his face devastated as the explosion unfolds on screen.

TEXT OVERLAY: "Three consecutive failures. Near bankruptcy."


INT. OFFICE - LATE NIGHT

ELON MUSK sits alone at a desk piled high with papers and financial reports. A single desk lamp casts long shadows across the room. He rubs his temples, exhausted but resolute. A clock ticks loudly in the silence. He's at the breaking point but won't give up.

SOUND: A ticking clock in a silent room.


EXT. LAUNCHPAD - DAY (2008)

A Falcon 1 rocket successfully soars into a crystal clear blue sky, leaving a clean white contrail. The launch is perfect.

INTERCUT: Control room - Engineers CHEER wildly, hugging each other, crying with relief. Musk stands among them, smiling for the first time.

TEXT OVERLAY: "2008: Flight 4 reaches orbit. SpaceX is saved."


INT. MODERN HANGAR - DAY

ELON MUSK stands before a large, focused team in a spacious modern hangar. Behind him, a giant render of a Falcon 9 rocket with prominent landing legs. He gestures energetically, explaining his vision for reusability. The team listens intently, some taking notes.

TEXT OVERLAY: "The Next Challenge: Reusability."


EXT. LAUNCH PAD - GOLDEN HOUR

A massive Falcon 9 rocket begins its ascent from the launch pad in a powerful, fiery display. The ground shakes. Smoke and fire billow beneath it. The rocket rises majestically toward space carrying a commercial payload. The golden hour sun creates epic backlighting.

SOUND: Thunderous roar of rocket engines.


EXT. SKY/OCEAN - DAY

The first-stage booster of the Falcon 9 falls back through clouds toward Earth. Grid fins deploy, steering the massive cylinder precisely. Below, a tiny droneship waits in the middle of the ocean. The booster approaches, engines firing for controlled descent.

SOUND: Intense atmospheric wind noise.


EXT. DRONESHIP "OF COURSE I STILL LOVE YOU" - SUNSET (2016)

The Falcon 9 booster stands perfectly upright on the deck of the droneship in the middle of the ocean. Smoke rises from its base. The sunset creates a heroic silhouette. A historic moment captured in golden light.

TEXT OVERLAY: "2016: History made. The future is reusable."
"""


user_requirement = \
"""
CRITICAL: Preserve the exact narrative structure - 9 distinct scenes/moments.

Cinematography style:
- Early scenes (failures): Gritty, tense, documentary-style, harsh lighting
- Middle scenes (turning point): Intimate, emotional, shadowy
- Final scenes (triumph): Epic, grand, awe-inspiring, golden light

Shot requirements:
- Each scene should have 2-4 shots maximum (we have 9 scenes total)
- Use the camera angles suggested in the scene descriptions
- Prioritize emotional impact over quantity of shots
- Final video should be approximately 2-3 minutes

Technical:
- Wide shots for rocket launches to show scale
- Close-ups for Elon's emotional moments
- Intercutting for parallel action (explosion/reaction)
"""


style = \
"""
Cinematic, photorealistic with a gritty documentary feel in early scenes
evolving into epic, grand visuals. Think SpaceX documentary meets
prestige drama. Realistic lighting, practical effects aesthetic.
"""


async def main():
    pipeline = Script2VideoPipeline.init_from_config(
        config_path="configs/script2video_vertex.yaml"
    )

    await pipeline(
        script=script,
        user_requirement=user_requirement,
        style=style
    )


if __name__ == "__main__":
    asyncio.run(main())

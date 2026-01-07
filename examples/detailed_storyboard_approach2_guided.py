"""
Example: Using detailed requirements to guide ViMax's planning agents

This shows how to provide your vision through the user_requirement parameter
while letting ViMax's agents do the detailed shot planning.
"""

import asyncio
from pipelines.idea2video_pipeline import Idea2VideoPipeline


# ==========================================
# APPROACH 2: Guided Planning via Requirements
# ==========================================
# Provide a clean narrative, then use user_requirement to guide the agents

idea = \
"""
The SpaceX Story: From Dream to Revolution

Act 1 - The Dream and The Falls:
In 2002, a young Elon Musk gazes at Mars from an office balcony, dreaming of making humanity multi-planetary. He and a small team work tirelessly in a converted warehouse, building rockets from scratch. But disaster strikes—three Falcon 1 rockets explode in succession, bringing SpaceX to the brink of bankruptcy.

Act 2 - The Turning Point:
Late at night, Musk sits alone with financial reports, exhausted but determined to try one last time. In 2008, the fourth Falcon 1 successfully reaches orbit. SpaceX is saved. Energized, Musk presents his next impossible challenge to the team: making rockets reusable.

Act 3 - The Revolution:
A massive Falcon 9 lifts off carrying a commercial payload. Its first-stage booster separates, falls back through the atmosphere, and—against all odds—lands perfectly upright on a droneship in the middle of the ocean. In 2016, history is made. The future is reusable.
"""


user_requirement = \
"""
STRUCTURE: Create exactly 3 scenes matching the 3 acts described.

Scene 1 - The Dream and The Falls (3 panels/moments):
1. Panel "The Vision":
   - Location: Office balcony at night
   - Subject: Young Elon Musk gazing at Mars
   - Shot type: Medium close-up
   - Mood: Contemplative, determined
   - Lighting: Soft ambient city light mixed with starlight
   - Include text overlay: "2002: The Goal is Mars."

2. Panel "The Garage Days":
   - Location: Messy converted warehouse
   - Subject: Musk and small engineering team around whiteboard with equations
   - Shot type: Eye-level group shot
   - Mood: Passionate, intense
   - Lighting: Harsh fluorescent
   - Audio: Muffled technical debates

3. Panel "Failure to Launch":
   - Location: Tropical launchpad
   - Action: Falcon 1 rocket exploding after liftoff
   - Shot type: Wide angle establishing shot, then cut to close-up of Musk's devastated reaction in control bunker
   - Mood: Catastrophic, desperate
   - Lighting: Harsh daylight
   - Include text overlay: "Three consecutive failures. Near bankruptcy."

Scene 2 - The Turning Point (3 panels/moments):
4. Panel "The Last Stand":
   - Location: Dark office, late night
   - Subject: Musk alone at desk covered in papers
   - Shot type: Close-up, head in hands
   - Mood: Exhausted but resolved
   - Lighting: Single desk lamp casting long shadows
   - Audio: Ticking clock in silence

5. Panel "Orbit Achieved":
   - Location: Launchpad and control room
   - Action: Falcon 1 successfully launching, engineers celebrating
   - Shot type: Low angle looking up at rocket, then cut to control room celebration
   - Mood: Triumphant, relief
   - Lighting: Bright sunlight
   - Include text overlay: "2008: Flight 4 reaches orbit. SpaceX is saved."

6. Panel "The Reusable Idea":
   - Location: Large modern hangar
   - Subject: Musk presenting Falcon 9 blueprint with landing legs to team
   - Shot type: Medium-wide shot showing both Musk and the blueprint
   - Mood: Focused, visionary
   - Lighting: Industrial hangar lighting
   - Include text overlay: "The Next Challenge: Reusability."

Scene 3 - The Revolution (3 panels/moments):
7. Panel "Liftoff":
   - Location: Launch pad
   - Action: Massive Falcon 9 launching with fiery plume
   - Shot type: Majestic wide shot
   - Mood: Awe-inspiring, powerful
   - Lighting: Golden hour
   - Audio: Roar of rocket engines

8. Panel "The Descent":
   - Location: Sky above ocean
   - Action: First-stage booster falling through clouds with grid fins steering toward droneship
   - Shot type: Aerial view looking down
   - Mood: Tense, focused
   - Lighting: Diffused daylight through clouds
   - Audio: Intense atmospheric wind

9. Panel "Landing the Impossible":
   - Location: Droneship "Of Course I Still Love You" in ocean
   - Subject: Falcon 9 booster standing upright after successful landing
   - Shot type: Grand wide shot showing scale
   - Mood: Triumphant, historic
   - Lighting: Sunset creating heroic silhouette
   - Include text overlay: "2016: History made. The future is reusable."

CINEMATOGRAPHY REQUIREMENTS:
- Total shots: Approximately 20-25 shots across all 3 scenes
- Each panel/moment should be 2-3 shots
- Use varied camera angles as specified above
- Emphasize emotional transitions between scenes
- Early scenes: gritty, tense, documentary style
- Late scenes: epic, grand, cinematic

PACING:
- Scene 1: Build tension through failures
- Scene 2: Emotional low to triumphant high
- Scene 3: Pure epic spectacle
- Target length: 2-3 minutes total
"""


style = \
"""
Cinematic, photorealistic.

Visual evolution:
- Early footage: Gritty documentary feel, handheld aesthetic, harsh lighting
- Middle footage: Intimate drama, emotional close-ups, moody shadows
- Late footage: Epic space documentary, IMAX-quality, heroic framing

Reference style: Think "The Social Network" meets "Apollo 13" meets SpaceX official footage.
Realistic lighting, practical effects aesthetic, no CGI look.
"""


async def main():
    pipeline = Idea2VideoPipeline.init_from_config(
        config_path="configs/idea2video_vertex.yaml"
    )

    await pipeline(
        idea=idea,
        user_requirement=user_requirement,
        style=style
    )

    print("\n" + "="*60)
    print("✅ SpaceX story video generation complete!")
    print("Check output in: .working_dir/idea2video_vertex/")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

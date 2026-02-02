from pydantic import BaseModel, Field
from typing import List


class StoryboardMeta(BaseModel):
    """Holistic analysis of the entire storyboard image."""
    narrative_summary: str = Field(
        description="A 3-5 sentence summary of the overall narrative depicted across all panels.",
    )
    tone: str = Field(
        description="The overall emotional tone of the storyboard (e.g., 'dark and suspenseful', 'lighthearted and comedic', 'melancholic and reflective').",
    )
    visual_style: str = Field(
        description="The visual/artistic style of the storyboard drawings (e.g., 'realistic pencil sketch', 'manga-style', 'loose watercolor', 'detailed ink drawings').",
    )
    genre: str = Field(
        description="The genre of the story depicted (e.g., 'fantasy adventure', 'sci-fi thriller', 'romantic drama').",
    )
    narrative_arc: str = Field(
        description="Description of the narrative arc: setup, rising action, climax, resolution as depicted in the panels.",
    )
    setting_description: str = Field(
        description="Overall description of the primary settings/locations shown across all panels.",
    )
    total_panels: int = Field(
        description="The total number of panels in the storyboard.",
    )
    themes: List[str] = Field(
        description="Key thematic elements identified across the storyboard.",
    )


class PanelAnalysis(BaseModel):
    """Detailed analysis of a single storyboard panel."""
    panel_idx: int = Field(
        description="The index of the panel in reading order (left-to-right, top-to-bottom), starting from 0.",
    )
    scene_description: str = Field(
        description="A detailed description of what is happening in this panel, written as a screenplay action line.",
    )
    environment: str = Field(
        description="Description of the environment/setting in slugline format followed by detail. E.g. 'INT. OFFICE - DAY. A modern open-plan office with glass walls and city skyline views.'",
    )
    characters_present: List[str] = Field(
        description="List of visual character descriptors visible in this panel. Use distinctive appearance traits as identifiers (e.g. 'man_in_white_shirt', 'woman_with_red_scarf'). Return empty list if no characters.",
    )
    camera_angle: str = Field(
        description="The implied camera angle and shot type depicted in the panel drawing (e.g. 'Wide shot, slightly low angle', 'Close-up, eye level').",
    )
    mood: str = Field(
        description="The emotional mood conveyed by this specific panel.",
    )
    implied_action: str = Field(
        description="The action or movement implied by the panel.",
    )
    implied_audio: str = Field(
        description="Implied sound effects, dialogue, or ambient audio. Use format: [Sound Effect] description. [Speaker] Character (emotion): 'dialogue'.",
    )
    narrative_continuity: str = Field(
        description="How this panel connects to the previous and next panels in the narrative flow.",
    )


class VisualCharacter(BaseModel):
    """A character identified and tracked across multiple storyboard panels."""
    identifier: str = Field(
        description="A unique human-readable identifier derived from visual appearance (e.g., 'Man in White Shirt', 'Woman with Red Scarf').",
    )
    static_features: str = Field(
        description="The character's static physical features: gender, age, build, hair, facial features, skin tone. These remain constant across panels.",
    )
    dynamic_features: str = Field(
        description="The character's clothing, accessories, and carried items as they appear in the storyboard.",
    )
    panel_appearances: List[int] = Field(
        description="List of panel indices (0-based) where this character appears.",
    )
    role_assessment: str = Field(
        description="Assessment of the character's role: protagonist, antagonist, supporting, or background.",
    )

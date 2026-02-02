import logging
from typing import List
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from interfaces import StoryboardMeta, PanelAnalysis, VisualCharacter
from utils.image import image_path_to_b64
from utils.retry import after_func


system_prompt_template = \
"""
[Role]
You are a professional character designer and visual continuity specialist for film and animation production. You excel at identifying recurring characters across sequential art panels based on visual appearance alone.

[Task]
Identify and track all unique characters across the provided storyboard panels. Characters may appear in multiple panels with different poses, angles, or expressions, but they are the same character if their core visual features match.

[Input]
- Overall storyboard context within <STORYBOARD_CONTEXT> tags.
- All panels provided as images, each labeled "Panel N:".
- Per-panel character notes within <PANEL_CHARACTER_NOTES> tags.

[Output]
{format_instructions}

[Guidelines]
- Two characters in different panels are the SAME person if they share: similar body type, hair style/color, clothing style, and distinguishing features.
- Assign a descriptive identifier based on the most distinctive visual trait (e.g., "Man in White Shirt", "Woman with Red Scarf", "Bald Elderly Man").
- static_features must describe ONLY physical traits: gender, approximate age, build, hair style and color, facial features, skin tone. These are traits that do not change.
- dynamic_features must describe clothing, accessories, and carried items as they appear in the storyboard.
- Do NOT include personality, emotions, actions, or relationships in feature descriptions.
- If a character's appearance changes across panels (e.g., costume change), note this in dynamic_features (e.g., "Wears white shirt in panels 0-5, switches to suit jacket in panels 6-10").
- Assign role_assessment based on number of panel appearances and narrative centrality (protagonist appears in most panels, supporting in a few, background in one or two).
- Exclude background crowds, indistinct silhouettes, or figures too small to identify features.
- Each identifier MUST be unique across all characters.
- Err on the side of merging when characters look very similar across panels. Split into separate characters only when features clearly differ.
"""


class ExtractVisualCharactersResponse(BaseModel):
    characters: List[VisualCharacter] = Field(
        ..., description="List of unique characters identified across all panels."
    )


class VisualCharacterExtractor:
    def __init__(self, chat_model):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def extract_characters(
        self,
        panel_image_paths: List[str],
        panel_analyses: List[PanelAnalysis],
        storyboard_meta: StoryboardMeta,
    ) -> List[VisualCharacter]:
        """
        Identify and track all unique characters across all storyboard panels.

        Args:
            panel_image_paths: Ordered list of all panel image paths.
            panel_analyses: Per-panel analysis results with character notes.
            storyboard_meta: Holistic storyboard analysis for context.

        Returns:
            List of VisualCharacter with unique IDs and panel appearance tracking.
        """
        parser = PydanticOutputParser(pydantic_object=ExtractVisualCharactersResponse)

        # Build storyboard context
        context_text = (
            f"Narrative: {storyboard_meta.narrative_summary}\n"
            f"Genre: {storyboard_meta.genre}\n"
            f"Total Panels: {storyboard_meta.total_panels}"
        )

        # Build per-panel character notes
        panel_notes = ""
        for pa in panel_analyses:
            chars = ", ".join(pa.characters_present) if pa.characters_present else "no characters"
            panel_notes += f"Panel {pa.panel_idx}: [{chars}] - {pa.scene_description[:100]}...\n"

        # Build multimodal human message
        human_content = [
            {"type": "text", "text": f"<STORYBOARD_CONTEXT>\n{context_text}\n</STORYBOARD_CONTEXT>"},
            {"type": "text", "text": f"<PANEL_CHARACTER_NOTES>\n{panel_notes}\n</PANEL_CHARACTER_NOTES>"},
        ]

        # Add all panel images
        for idx, panel_path in enumerate(panel_image_paths):
            human_content.append({"type": "text", "text": f"Panel {idx}:"})
            human_content.append({
                "type": "image_url",
                "image_url": {"url": image_path_to_b64(panel_path, mime=True)}
            })

        messages = [
            SystemMessage(content=system_prompt_template.format(
                format_instructions=parser.get_format_instructions()
            )),
            HumanMessage(content=human_content),
        ]

        chain = self.chat_model | parser
        response: ExtractVisualCharactersResponse = await chain.ainvoke(messages)

        characters = response.characters
        logging.info(f"Extracted {len(characters)} unique characters across {len(panel_image_paths)} panels.")
        for char in characters:
            logging.info(f"  - {char.identifier}: appears in panels {char.panel_appearances} ({char.role_assessment})")

        return characters

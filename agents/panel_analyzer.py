import logging
from typing import List
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from interfaces import StoryboardMeta, PanelAnalysis
from utils.image import image_path_to_b64
from utils.retry import after_func


system_prompt_template = \
"""
[Role]
You are a professional scene analyst for film production, skilled in interpreting storyboard panels and translating them into detailed scene descriptions suitable for screenplay writing.

[Task]
Analyze the provided storyboard panel in the context of the overall narrative and produce a detailed scene analysis. You are given the overall storyboard context and optionally adjacent panels for continuity reference.

[Input]
- Overall storyboard context is provided within <STORYBOARD_CONTEXT> tags.
- The target panel image is labeled "Target Panel:".
- Adjacent panels (previous and/or next) may be provided for continuity reference.

[Output]
{format_instructions}

[Guidelines]
- The scene_description should be written as a screenplay action line — vivid, present tense, describing what the audience sees.
- The environment should begin with a slugline format (INT/EXT. LOCATION - TIME) followed by a detailed description. E.g. "INT. MODERN OFFICE - DAY. A bright open-plan office with floor-to-ceiling windows overlooking a city skyline."
- For characters_present, use descriptive visual identifiers based on appearance traits (e.g. "man_in_white_shirt", "woman_with_glasses"). Use consistent identifiers if the same character appeared in context panels.
- If text, numbering, or labels are visible on the panel, ignore them entirely.
- The implied_audio should use the format: [Sound Effect] description and/or [Speaker] Character (emotion): "dialogue".
- narrative_continuity must explain how this panel connects to the previous and next panels. If this is the first or last panel, state that.
- camera_angle should describe both the shot type (wide, medium, close-up, extreme close-up) and the camera angle (eye level, low angle, high angle, bird's eye).
"""


class PanelAnalyzer:
    def __init__(self, chat_model):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def analyze_panel(
        self,
        panel_idx: int,
        panel_image_path: str,
        storyboard_meta: StoryboardMeta,
        adjacent_panel_paths: List[str],
    ) -> PanelAnalysis:
        """
        Analyze a single panel with holistic context and adjacent panels for continuity.

        Args:
            panel_idx: 0-based index of this panel in reading order.
            panel_image_path: Path to this panel's image.
            storyboard_meta: Holistic analysis of the entire storyboard.
            adjacent_panel_paths: Paths to previous and/or next panel images for context.

        Returns:
            PanelAnalysis with detailed scene information.
        """
        parser = PydanticOutputParser(pydantic_object=PanelAnalysis)

        # Build storyboard context text
        context_text = (
            f"Narrative: {storyboard_meta.narrative_summary}\n"
            f"Tone: {storyboard_meta.tone}\n"
            f"Visual Style: {storyboard_meta.visual_style}\n"
            f"Genre: {storyboard_meta.genre}\n"
            f"Narrative Arc: {storyboard_meta.narrative_arc}\n"
            f"Settings: {storyboard_meta.setting_description}\n"
            f"Total Panels: {storyboard_meta.total_panels}\n"
            f"Current Panel Index: {panel_idx}"
        )

        # Build multimodal human message
        human_content = [
            {"type": "text", "text": f"<STORYBOARD_CONTEXT>\n{context_text}\n</STORYBOARD_CONTEXT>"},
        ]

        # Add adjacent panels for continuity context
        for adj_idx, adj_path in enumerate(adjacent_panel_paths):
            label = "Previous Panel" if adj_idx == 0 and len(adjacent_panel_paths) > 1 else (
                "Next Panel" if adj_idx == 1 else "Adjacent Panel"
            )
            # If only one adjacent panel, determine if it's previous or next
            if len(adjacent_panel_paths) == 1:
                label = "Previous Panel" if panel_idx > 0 else "Next Panel"

            human_content.append({"type": "text", "text": f"{label}:"})
            human_content.append({
                "type": "image_url",
                "image_url": {"url": image_path_to_b64(adj_path, mime=True)}
            })

        # Add the target panel
        human_content.append({"type": "text", "text": "Target Panel:"})
        human_content.append({
            "type": "image_url",
            "image_url": {"url": image_path_to_b64(panel_image_path, mime=True)}
        })

        messages = [
            SystemMessage(content=system_prompt_template.format(
                format_instructions=parser.get_format_instructions()
            )),
            HumanMessage(content=human_content),
        ]

        chain = self.chat_model | parser
        response: PanelAnalysis = await chain.ainvoke(messages)

        # Ensure panel_idx is correct in the response
        response.panel_idx = panel_idx

        logging.info(f"Panel {panel_idx} analysis complete: {len(response.characters_present)} characters detected.")
        return response

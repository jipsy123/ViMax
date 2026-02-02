import logging
from typing import List
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from interfaces import StoryboardMeta
from utils.image import image_path_to_b64
from utils.retry import after_func


system_prompt_template = \
"""
[Role]
You are a professional storyboard analyst and narrative designer, skilled in interpreting visual storytelling across sequential art panels.

[Task]
Analyze the complete storyboard (all panels provided in reading order, left-to-right then top-to-bottom) and produce a holistic analysis covering the overall narrative, tone, visual style, genre, narrative arc, settings, and themes.

[Input]
You will receive all panels of a storyboard in reading order. Each panel is labeled "Panel N:" followed by the image.

[Output]
{format_instructions}

[Guidelines]
- Treat the storyboard as purely visual input. The image is the sole source of information.
- If panels contain text overlays, numbering, labels, or annotations, ignore them for narrative analysis. Focus on the drawn content.
- The visual_style field should describe the artistic rendering style of the drawings themselves (e.g., "grayscale ink illustration with clean lines and moderate detail").
- The narrative_arc should reference specific panel index ranges (e.g., "Panels 0-2 establish...").
- Count the total number of panels accurately based on what you receive.
- Identify themes based on visual motifs, character actions, and setting changes across panels.
"""


class StoryboardAnalyzer:
    def __init__(self, chat_model):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def analyze_storyboard(
        self,
        panel_image_paths: List[str],
    ) -> StoryboardMeta:
        """
        Send all panel images to a multimodal LLM for holistic storyboard analysis.

        Args:
            panel_image_paths: Ordered list of panel image file paths.

        Returns:
            StoryboardMeta with narrative, tone, style, genre, arc, settings, themes.
        """
        parser = PydanticOutputParser(pydantic_object=StoryboardMeta)

        # Build multimodal human message with all panels
        human_content = []
        for idx, panel_path in enumerate(panel_image_paths):
            human_content.append({
                "type": "text",
                "text": f"Panel {idx}:"
            })
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
        response: StoryboardMeta = await chain.ainvoke(messages)

        logging.info(
            f"Storyboard analysis complete: {response.total_panels} panels, "
            f"genre={response.genre}, tone={response.tone}"
        )
        return response

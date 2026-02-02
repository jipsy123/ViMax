import logging
from typing import List
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from interfaces import StoryboardMeta, PanelAnalysis, VisualCharacter
from utils.retry import after_func


system_prompt_template = \
"""
[Role]
You are a professional screenwriter specializing in visual-to-script adaptation. You excel at translating storyboard panel analyses into vivid, filmable screenplay scripts.

[Task]
Convert the provided panel analyses into screenplay-format scene scripts. Each panel becomes exactly one scene. Write a complete screenplay script for each panel/scene.

[Input]
- Storyboard context within <STORYBOARD_CONTEXT> tags (narrative summary, tone, style, genre).
- Character list within <CHARACTERS> tags (with identifiers, static features, and dynamic features).
- Panel analyses within <PANEL_ANALYSES> tags (ordered by panel_idx, each containing scene description, environment, characters, camera angle, mood, implied action, implied audio, and narrative continuity).

[Output]
{format_instructions}

[Guidelines]
- Each scene script MUST begin with a slugline in standard format (e.g., "EXT. CITY STREET - DAY" or "INT. OFFICE - NIGHT").
- Character names in action descriptions MUST be enclosed in angle brackets (e.g., <Man in White Shirt> sits at the desk).
- Dialogue lines should use the format: <Character Name>: "dialogue text"
- Infer reasonable dialogue from the implied_audio field in panel analyses. If implied_audio contains [Speaker] tags, use those. Otherwise, infer dialogue that fits the scene naturally.
- Action descriptions should be vivid, present tense, and "filmable" — describe what the camera sees, not abstract emotions.
- Maintain narrative continuity between scenes. Reference the narrative_continuity field from panel analyses.
- Keep character identifiers consistent with the provided character list. Use the exact identifier strings from the character list.
- Each scene script should be substantial enough to generate multiple shots from (typically 3-8 sentences of action and dialogue).
- Include environmental details (lighting, atmosphere, props) to enrich the visual description.
- The output should contain exactly one script per panel, in the same order as the panels.
"""

human_prompt_template = \
"""
<STORYBOARD_CONTEXT>
Narrative: {narrative_summary}
Tone: {tone}
Visual Style: {visual_style}
Genre: {genre}
Narrative Arc: {narrative_arc}
Settings: {setting_description}
</STORYBOARD_CONTEXT>

<CHARACTERS>
{characters_text}
</CHARACTERS>

<PANEL_ANALYSES>
{panel_analyses_text}
</PANEL_ANALYSES>
"""


class WriteSceneScriptsResponse(BaseModel):
    scene_scripts: List[str] = Field(
        ...,
        description="List of screenplay-format scene scripts, one per panel. Each script begins with a slugline and contains action descriptions with character names in <> brackets and dialogue lines."
    )


class SceneScriptWriter:
    def __init__(self, chat_model):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def write_scene_scripts(
        self,
        panel_analyses: List[PanelAnalysis],
        characters: List[VisualCharacter],
        storyboard_meta: StoryboardMeta,
    ) -> List[str]:
        """
        Convert panel analyses into structured screenplay scene scripts.
        One scene per panel.

        Args:
            panel_analyses: Ordered list of per-panel analysis results.
            characters: List of unique characters identified across all panels.
            storyboard_meta: Holistic storyboard analysis.

        Returns:
            List of scene script strings, one per panel, compatible with Script2VideoPipeline.
        """
        parser = PydanticOutputParser(pydantic_object=WriteSceneScriptsResponse)

        # Format characters text
        characters_text = ""
        for char in characters:
            characters_text += (
                f"- {char.identifier} ({char.role_assessment})\n"
                f"  Static features: {char.static_features}\n"
                f"  Dynamic features: {char.dynamic_features}\n"
                f"  Appears in panels: {char.panel_appearances}\n\n"
            )

        # Format panel analyses text
        panel_analyses_text = ""
        for pa in panel_analyses:
            chars = ", ".join(pa.characters_present) if pa.characters_present else "no characters"
            panel_analyses_text += (
                f"Panel {pa.panel_idx}:\n"
                f"  Environment: {pa.environment}\n"
                f"  Characters: [{chars}]\n"
                f"  Scene: {pa.scene_description}\n"
                f"  Camera: {pa.camera_angle}\n"
                f"  Mood: {pa.mood}\n"
                f"  Action: {pa.implied_action}\n"
                f"  Audio: {pa.implied_audio}\n"
                f"  Continuity: {pa.narrative_continuity}\n\n"
            )

        human_text = human_prompt_template.format(
            narrative_summary=storyboard_meta.narrative_summary,
            tone=storyboard_meta.tone,
            visual_style=storyboard_meta.visual_style,
            genre=storyboard_meta.genre,
            narrative_arc=storyboard_meta.narrative_arc,
            setting_description=storyboard_meta.setting_description,
            characters_text=characters_text,
            panel_analyses_text=panel_analyses_text,
        )

        messages = [
            SystemMessage(content=system_prompt_template.format(
                format_instructions=parser.get_format_instructions()
            )),
            HumanMessage(content=human_text),
        ]

        chain = self.chat_model | parser
        response: WriteSceneScriptsResponse = await chain.ainvoke(messages)

        scripts = response.scene_scripts

        # Validate count matches panels
        if len(scripts) != len(panel_analyses):
            logging.warning(
                f"SceneScriptWriter produced {len(scripts)} scripts for "
                f"{len(panel_analyses)} panels. Expected 1:1 mapping."
            )

        logging.info(f"Generated {len(scripts)} scene scripts from {len(panel_analyses)} panels.")
        return scripts

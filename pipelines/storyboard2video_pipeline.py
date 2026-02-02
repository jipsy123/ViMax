import os
import json
import logging
import asyncio
from typing import List, Dict, Optional
from moviepy import VideoFileClip, concatenate_videoclips
import yaml
from langchain.chat_models import init_chat_model
import importlib

from agents import (
    StoryboardAnalyzer,
    PanelAnalyzer,
    VisualCharacterExtractor,
    CharacterPortraitsGenerator,
    ReferenceImageSelector,
)
from interfaces import (
    StoryboardMeta,
    PanelAnalysis,
    VisualCharacter,
    CharacterInScene,
)
from utils.storyboard_splitter import StoryboardSplitter
from utils.rate_limiter import RateLimiter


class Storyboard2VideoPipeline:
    def __init__(
        self,
        chat_model,
        image_generator,
        video_generator,
        working_dir: str,
        storyboard_splitter_config: Optional[dict] = None,
    ):
        self.chat_model = chat_model
        self.image_generator = image_generator
        self.video_generator = video_generator
        self.working_dir = working_dir
        os.makedirs(self.working_dir, exist_ok=True)

        # Utility
        splitter_config = storyboard_splitter_config or {}
        self.storyboard_splitter = StoryboardSplitter(**splitter_config)

        # Agents
        self.storyboard_analyzer = StoryboardAnalyzer(chat_model=self.chat_model)
        self.panel_analyzer = PanelAnalyzer(chat_model=self.chat_model)
        self.visual_character_extractor = VisualCharacterExtractor(chat_model=self.chat_model)
        self.character_portraits_generator = CharacterPortraitsGenerator(
            image_generator=self.image_generator
        )
        self.reference_image_selector = ReferenceImageSelector(chat_model=self.chat_model)

    @classmethod
    def init_from_config(cls, config_path: str):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        chat_model_args = config["chat_model"]["init_args"]
        chat_model = init_chat_model(**chat_model_args)

        # Create separate rate limiters for each service
        chat_model_rpm = config.get("chat_model", {}).get("max_requests_per_minute", None)
        chat_model_rpd = config.get("chat_model", {}).get("max_requests_per_day", None)
        image_generator_rpm = config.get("image_generator", {}).get("max_requests_per_minute", None)
        image_generator_rpd = config.get("image_generator", {}).get("max_requests_per_day", None)
        video_generator_rpm = config.get("video_generator", {}).get("max_requests_per_minute", None)
        video_generator_rpd = config.get("video_generator", {}).get("max_requests_per_day", None)

        chat_model_rate_limiter = RateLimiter(
            max_requests_per_minute=chat_model_rpm,
            max_requests_per_day=chat_model_rpd
        ) if (chat_model_rpm or chat_model_rpd) else None

        image_rate_limiter = RateLimiter(
            max_requests_per_minute=image_generator_rpm,
            max_requests_per_day=image_generator_rpd
        ) if (image_generator_rpm or image_generator_rpd) else None

        video_rate_limiter = RateLimiter(
            max_requests_per_minute=video_generator_rpm,
            max_requests_per_day=video_generator_rpd
        ) if (video_generator_rpm or video_generator_rpd) else None

        # Display rate limiting configuration
        if chat_model_rate_limiter:
            limits = []
            if chat_model_rpm:
                limits.append(f"{chat_model_rpm} req/min")
            if chat_model_rpd:
                limits.append(f"{chat_model_rpd} req/day")
            print(f"Chat model rate limiting: {', '.join(limits)}")

        if image_rate_limiter:
            limits = []
            if image_generator_rpm:
                limits.append(f"{image_generator_rpm} req/min")
            if image_generator_rpd:
                limits.append(f"{image_generator_rpd} req/day")
            print(f"Image generator rate limiting: {', '.join(limits)}")

        if video_rate_limiter:
            limits = []
            if video_generator_rpm:
                limits.append(f"{video_generator_rpm} req/min")
            if video_generator_rpd:
                limits.append(f"{video_generator_rpd} req/day")
            print(f"Video generator rate limiting: {', '.join(limits)}")

        image_generator_cls_module, image_generator_cls_name = config["image_generator"]["class_path"].rsplit(".", 1)
        image_generator_cls = getattr(importlib.import_module(image_generator_cls_module), image_generator_cls_name)
        image_generator_args = config["image_generator"]["init_args"]
        image_generator_args["rate_limiter"] = image_rate_limiter
        image_generator = image_generator_cls(**image_generator_args)

        video_generator_cls_module, video_generator_cls_name = config["video_generator"]["class_path"].rsplit(".", 1)
        video_generator_cls = getattr(importlib.import_module(video_generator_cls_module), video_generator_cls_name)
        video_generator_args = config["video_generator"]["init_args"]
        video_generator_args["rate_limiter"] = video_rate_limiter
        video_generator = video_generator_cls(**video_generator_args)

        storyboard_splitter_config = config.get("storyboard_splitter", None)

        return cls(
            chat_model=chat_model,
            image_generator=image_generator,
            video_generator=video_generator,
            working_dir=config["working_dir"],
            storyboard_splitter_config=storyboard_splitter_config,
        )

    # ─────────────────────────────────────────────
    # Main entry point
    # ─────────────────────────────────────────────

    async def __call__(
        self,
        storyboard_image_path: str,
        style: Optional[str] = None,
    ) -> str:
        """
        Convert a storyboard image into a long-form video.

        Args:
            storyboard_image_path: Path to the storyboard image (PNG/JPG).
            style: Visual style for generated content. If None, auto-detected from storyboard.

        Returns:
            Path to the final concatenated video.
        """

        # Step 1: Panel Splitting
        panel_paths = self.split_storyboard(storyboard_image_path)

        # Step 2: Holistic Storyboard Analysis
        storyboard_meta = await self.analyze_storyboard(panel_paths)

        # Auto-detect style from storyboard if not provided
        if style is None:
            style = storyboard_meta.visual_style
            print(f"Auto-detected style: {style}")

        # Step 3: Per-Panel Analysis (parallelized)
        panel_analyses = await self.analyze_panels(panel_paths, storyboard_meta)

        # Step 4: Character Identification & Tracking
        visual_characters = await self.extract_characters(
            panel_paths, panel_analyses, storyboard_meta
        )

        # Step 5: Convert VisualCharacter -> CharacterInScene for downstream compatibility
        characters = self.convert_to_characters_in_scene(visual_characters)

        # Step 6: Character Portrait Generation
        character_portraits_registry = await self.generate_character_portraits(
            characters=characters,
            character_portraits_registry=None,
            style=style,
        )

        # Step 7: Generate panel videos (1 frame + 1 video per panel, parallelized)
        video_paths = await self.generate_panel_videos(
            panel_paths=panel_paths,
            panel_analyses=panel_analyses,
            visual_characters=visual_characters,
            characters=characters,
            character_portraits_registry=character_portraits_registry,
            storyboard_meta=storyboard_meta,
            style=style,
        )

        # Step 8: Concatenate Panel Videos
        final_video_path = os.path.join(self.working_dir, "final_video.mp4")
        if os.path.exists(final_video_path):
            print(f"🚀 Skipped concatenating videos, already exists.")
        else:
            print(f"🎬 Starting concatenating videos...")
            video_clips = [VideoFileClip(p) for p in video_paths]
            final_video = concatenate_videoclips(video_clips)
            final_video.write_videofile(final_video_path, codec="libx264", preset="medium")
            print(f"☑️ Concatenated videos, saved to {final_video_path}.")

        return final_video_path

    # ─────────────────────────────────────────────
    # Step helpers (each with caching)
    # ─────────────────────────────────────────────

    def split_storyboard(self, storyboard_image_path: str) -> List[str]:
        """Step 1: Split storyboard into panels with caching."""
        panels_dir = os.path.join(self.working_dir, "panels")
        panels_manifest = os.path.join(self.working_dir, "panels_manifest.json")

        if os.path.exists(panels_manifest):
            with open(panels_manifest, "r", encoding="utf-8") as f:
                panel_paths = json.load(f)
            print(f"🚀 Loaded {len(panel_paths)} panels from existing manifest.")
            return panel_paths

        panel_paths = self.storyboard_splitter.split(storyboard_image_path, panels_dir)

        with open(panels_manifest, "w", encoding="utf-8") as f:
            json.dump(panel_paths, f, ensure_ascii=False, indent=4)

        return panel_paths

    async def analyze_storyboard(self, panel_paths: List[str]) -> StoryboardMeta:
        """Step 2: Holistic storyboard analysis with caching."""
        meta_path = os.path.join(self.working_dir, "storyboard_meta.json")

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = StoryboardMeta.model_validate(json.load(f))
            print(f"🚀 Loaded storyboard meta from existing file.")
            return meta

        print("🧠 Analyzing storyboard holistically...")
        meta = await self.storyboard_analyzer.analyze_storyboard(panel_paths)

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta.model_dump(), f, ensure_ascii=False, indent=4)
        print(f"✅ Storyboard analysis complete and saved to {meta_path}.")

        return meta

    async def analyze_panels(
        self, panel_paths: List[str], storyboard_meta: StoryboardMeta
    ) -> List[PanelAnalysis]:
        """Step 3: Per-panel analysis (parallel) with caching."""
        analyses_path = os.path.join(self.working_dir, "panel_analyses.json")

        if os.path.exists(analyses_path):
            with open(analyses_path, "r", encoding="utf-8") as f:
                analyses = [PanelAnalysis.model_validate(a) for a in json.load(f)]
            print(f"🚀 Loaded {len(analyses)} panel analyses from existing file.")
            return analyses

        print(f"🧠 Analyzing {len(panel_paths)} panels in parallel...")
        tasks = []
        for idx, panel_path in enumerate(panel_paths):
            adjacent = []
            if idx > 0:
                adjacent.append(panel_paths[idx - 1])
            if idx < len(panel_paths) - 1:
                adjacent.append(panel_paths[idx + 1])

            tasks.append(self.panel_analyzer.analyze_panel(
                panel_idx=idx,
                panel_image_path=panel_path,
                storyboard_meta=storyboard_meta,
                adjacent_panel_paths=adjacent,
            ))

        analyses = list(await asyncio.gather(*tasks))

        with open(analyses_path, "w", encoding="utf-8") as f:
            json.dump([a.model_dump() for a in analyses], f, ensure_ascii=False, indent=4)
        print(f"✅ Analyzed {len(analyses)} panels and saved to {analyses_path}.")

        return analyses

    async def extract_characters(
        self,
        panel_paths: List[str],
        panel_analyses: List[PanelAnalysis],
        storyboard_meta: StoryboardMeta,
    ) -> List[VisualCharacter]:
        """Step 4: Cross-panel character identification with caching."""
        chars_path = os.path.join(self.working_dir, "visual_characters.json")

        if os.path.exists(chars_path):
            with open(chars_path, "r", encoding="utf-8") as f:
                characters = [VisualCharacter.model_validate(c) for c in json.load(f)]
            print(f"🚀 Loaded {len(characters)} visual characters from existing file.")
            return characters

        print("🧠 Identifying characters across panels...")
        characters = await self.visual_character_extractor.extract_characters(
            panel_image_paths=panel_paths,
            panel_analyses=panel_analyses,
            storyboard_meta=storyboard_meta,
        )

        with open(chars_path, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in characters], f, ensure_ascii=False, indent=4)
        print(f"✅ Identified {len(characters)} unique characters and saved to {chars_path}.")

        return characters

    def convert_to_characters_in_scene(
        self, visual_characters: List[VisualCharacter]
    ) -> List[CharacterInScene]:
        """Step 5: Convert VisualCharacter to CharacterInScene for downstream compatibility."""
        characters_path = os.path.join(self.working_dir, "characters.json")

        if os.path.exists(characters_path):
            with open(characters_path, "r", encoding="utf-8") as f:
                characters = [CharacterInScene.model_validate(c) for c in json.load(f)]
            print(f"🚀 Loaded {len(characters)} characters (converted) from existing file.")
            return characters

        characters = []
        for idx, vc in enumerate(visual_characters):
            characters.append(CharacterInScene(
                idx=idx,
                identifier_in_scene=vc.identifier,
                is_visible=True,
                static_features=vc.static_features,
                dynamic_features=vc.dynamic_features,
            ))

        with open(characters_path, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in characters], f, ensure_ascii=False, indent=4)
        print(f"✅ Converted {len(characters)} characters to scene format.")

        return characters

    async def generate_character_portraits(
        self,
        characters: List[CharacterInScene],
        character_portraits_registry: Optional[Dict[str, Dict[str, Dict[str, str]]]],
        style: str,
    ):
        """Step 6: Generate character portraits (reuses Idea2VideoPipeline pattern)."""
        character_portraits_registry_path = os.path.join(
            self.working_dir, "character_portraits_registry.json"
        )
        if character_portraits_registry is None:
            if os.path.exists(character_portraits_registry_path):
                with open(character_portraits_registry_path, 'r', encoding='utf-8') as f:
                    character_portraits_registry = json.load(f)
            else:
                character_portraits_registry = {}

        tasks = [
            self._generate_portraits_for_single_character(character, style)
            for character in characters
            if character.identifier_in_scene not in character_portraits_registry
        ]
        if tasks:
            for future in asyncio.as_completed(tasks):
                character_portraits_registry.update(await future)
                with open(character_portraits_registry_path, 'w', encoding='utf-8') as f:
                    json.dump(character_portraits_registry, f, ensure_ascii=False, indent=4)

            print(f"✅ Completed character portrait generation for {len(characters)} characters.")
        else:
            print("🚀 All characters already have portraits, skipping portrait generation.")

        return character_portraits_registry

    async def _generate_portraits_for_single_character(
        self,
        character: CharacterInScene,
        style: str,
    ):
        """Generate front/side/back portraits for a single character."""
        character_dir = os.path.join(
            self.working_dir, "character_portraits",
            f"{character.idx}_{character.identifier_in_scene}"
        )
        os.makedirs(character_dir, exist_ok=True)

        front_portrait_path = os.path.join(character_dir, "front.png")
        if not os.path.exists(front_portrait_path):
            front_portrait_output = await self.character_portraits_generator.generate_front_portrait(
                character, style
            )
            front_portrait_output.save(front_portrait_path)

        side_portrait_path = os.path.join(character_dir, "side.png")
        if not os.path.exists(side_portrait_path):
            side_portrait_output = await self.character_portraits_generator.generate_side_portrait(
                character, front_portrait_path
            )
            side_portrait_output.save(side_portrait_path)

        back_portrait_path = os.path.join(character_dir, "back.png")
        if not os.path.exists(back_portrait_path):
            back_portrait_output = await self.character_portraits_generator.generate_back_portrait(
                character, front_portrait_path
            )
            back_portrait_output.save(back_portrait_path)

        print(f"☑️ Completed character portrait generation for {character.identifier_in_scene}.")

        return {
            character.identifier_in_scene: {
                "front": {
                    "path": front_portrait_path,
                    "description": f"A front view portrait of {character.identifier_in_scene}.",
                },
                "side": {
                    "path": side_portrait_path,
                    "description": f"A side view portrait of {character.identifier_in_scene}.",
                },
                "back": {
                    "path": back_portrait_path,
                    "description": f"A back view portrait of {character.identifier_in_scene}.",
                },
            }
        }

    # ─────────────────────────────────────────────
    # Step 7: Direct panel → frame → video
    # ─────────────────────────────────────────────

    def _build_panel_to_character_map(
        self,
        visual_characters: List[VisualCharacter],
        num_panels: int,
    ) -> Dict[int, List[int]]:
        """
        Build a mapping from panel_idx → list of character indices
        using VisualCharacter.panel_appearances.
        """
        panel_char_map: Dict[int, List[int]] = {i: [] for i in range(num_panels)}
        for char_idx, vc in enumerate(visual_characters):
            for panel_idx in vc.panel_appearances:
                if panel_idx in panel_char_map:
                    panel_char_map[panel_idx].append(char_idx)
        return panel_char_map

    async def generate_panel_videos(
        self,
        panel_paths: List[str],
        panel_analyses: List[PanelAnalysis],
        visual_characters: List[VisualCharacter],
        characters: List[CharacterInScene],
        character_portraits_registry: Dict[str, Dict[str, Dict[str, str]]],
        storyboard_meta: StoryboardMeta,
        style: str,
    ) -> List[str]:
        """
        Step 7: Generate one frame image + one video for each panel.
        All panels are processed in parallel (rate limiters handle throttling).

        Returns:
            Ordered list of video paths, one per panel.
        """
        panel_char_map = self._build_panel_to_character_map(
            visual_characters, len(panel_paths)
        )

        tasks = [
            self.generate_video_for_single_panel(
                panel_idx=idx,
                panel_path=panel_paths[idx],
                panel_analysis=panel_analyses[idx],
                characters=characters,
                character_portraits_registry=character_portraits_registry,
                panel_char_map=panel_char_map,
                storyboard_meta=storyboard_meta,
                style=style,
            )
            for idx in range(len(panel_paths))
        ]

        video_paths = list(await asyncio.gather(*tasks))
        return video_paths

    async def generate_video_for_single_panel(
        self,
        panel_idx: int,
        panel_path: str,
        panel_analysis: PanelAnalysis,
        characters: List[CharacterInScene],
        character_portraits_registry: Dict[str, Dict[str, Dict[str, str]]],
        panel_char_map: Dict[int, List[int]],
        storyboard_meta: StoryboardMeta,
        style: str,
    ) -> str:
        """
        Generate a single frame image and a single video for one panel.

        Flow:
            1. Build reference image pool (character portraits + panel image)
            2. Build frame prompt from PanelAnalysis fields
            3. ReferenceImageSelector → select best refs + generate optimized prompt
            4. image_generator → 1 frame image
            5. video_generator → 1 video clip

        Returns:
            Path to the generated video.
        """
        panel_dir = os.path.join(self.working_dir, "frames", str(panel_idx))
        os.makedirs(panel_dir, exist_ok=True)

        video_path = os.path.join(panel_dir, "video.mp4")

        # Early exit if video already cached
        if os.path.exists(video_path):
            print(f"🚀 Skipped panel {panel_idx}, video already exists.")
            return video_path

        # ── 1. Build available reference images ──
        available_images = []

        # Add character portraits for characters visible in this panel
        char_indices = panel_char_map.get(panel_idx, [])
        for char_idx in char_indices:
            identifier = characters[char_idx].identifier_in_scene
            if identifier in character_portraits_registry:
                registry_item = character_portraits_registry[identifier]
                for view, item in registry_item.items():
                    available_images.append((item["path"], item["description"]))

        # Add the original panel image as composition reference
        panel_desc = (
            f"Storyboard reference panel. "
            f"Camera: {panel_analysis.camera_angle}. "
            f"Scene: {panel_analysis.scene_description[:150]}. "
            f"Use this as composition and framing reference."
        )
        available_images.append((panel_path, panel_desc))

        # ── 2. Build frame prompt from PanelAnalysis ──
        frame_prompt = (
            f"Style: {style}. "
            f"{panel_analysis.environment} "
            f"{panel_analysis.scene_description} "
            f"Camera: {panel_analysis.camera_angle}. "
            f"Mood: {panel_analysis.mood}."
        )

        # ── 3. ReferenceImageSelector ──
        selector_output_path = os.path.join(panel_dir, "selector_output.json")
        if os.path.exists(selector_output_path):
            with open(selector_output_path, 'r', encoding='utf-8') as f:
                selector_output = json.load(f)
            print(f"🚀 Loaded existing reference selection for panel {panel_idx}.")
        else:
            print(f"🔍 Selecting reference images for panel {panel_idx}...")
            selector_output = await self.reference_image_selector.select_reference_images_and_generate_prompt(
                available_image_path_and_text_pairs=available_images,
                frame_description=frame_prompt,
            )
            with open(selector_output_path, 'w', encoding='utf-8') as f:
                json.dump(selector_output, f, ensure_ascii=False, indent=4)
            print(f"☑️ Selected references for panel {panel_idx}.")

        reference_pairs = selector_output["reference_image_path_and_text_pairs"]
        prompt = selector_output["text_prompt"]

        # Build the final prompt with reference image descriptions
        prefix_prompt = ""
        for i, (image_path, text) in enumerate(reference_pairs):
            prefix_prompt += f"Image {i}: {text}\n"
        combined_prompt = f"{prefix_prompt}\n{prompt}"
        reference_image_paths = [item[0] for item in reference_pairs]

        # ── 4. Generate frame image ──
        frame_path = os.path.join(panel_dir, "frame.png")
        if os.path.exists(frame_path):
            print(f"🚀 Skipped frame generation for panel {panel_idx}, already exists.")
        else:
            print(f"🖼️ Generating frame for panel {panel_idx}...")
            frame_image = await self.image_generator.generate_single_image(
                prompt=combined_prompt,
                reference_image_paths=reference_image_paths,
                size="1600x900",
            )
            frame_image.save(frame_path)
            print(f"☑️ Generated frame for panel {panel_idx}, saved to {frame_path}.")

        # ── 5. Generate video from frame ──
        motion_prompt = panel_analysis.implied_action
        if panel_analysis.implied_audio:
            motion_prompt += f"\n{panel_analysis.implied_audio}"

        print(f"🎬 Generating video for panel {panel_idx}...")
        video_output = await self.video_generator.generate_single_video(
            prompt=motion_prompt,
            reference_image_paths=[frame_path],
        )
        video_output.save(video_path)
        print(f"☑️ Generated video for panel {panel_idx}, saved to {video_path}.")

        return video_path

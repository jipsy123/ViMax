import os
import json
import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from moviepy import VideoFileClip, concatenate_videoclips
import yaml
from langchain.chat_models import init_chat_model
import importlib

from agents import (
    StoryboardAnalyzer,
    PanelAnalyzer,
    VisualCharacterExtractor,
    SceneScriptWriter,
    CharacterPortraitsGenerator,
)
from interfaces import (
    StoryboardMeta,
    PanelAnalysis,
    VisualCharacter,
    CharacterInScene,
)
from pipelines.script2video_pipeline import Script2VideoPipeline
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

        # New agents
        self.storyboard_analyzer = StoryboardAnalyzer(chat_model=self.chat_model)
        self.panel_analyzer = PanelAnalyzer(chat_model=self.chat_model)
        self.visual_character_extractor = VisualCharacterExtractor(chat_model=self.chat_model)
        self.scene_script_writer = SceneScriptWriter(chat_model=self.chat_model)

        # Existing reusable agent
        self.character_portraits_generator = CharacterPortraitsGenerator(
            image_generator=self.image_generator
        )

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

        # Step 7: Scene Script Generation
        scene_scripts = await self.write_scene_scripts(
            panel_analyses, visual_characters, storyboard_meta
        )

        # Step 8: Per-Scene Video Generation via Script2VideoPipeline
        all_video_paths = []

        for idx, scene_script in enumerate(scene_scripts):
            scene_working_dir = os.path.join(self.working_dir, f"scene_{idx}")
            os.makedirs(scene_working_dir, exist_ok=True)

            # Build additional reference images from the source panel
            additional_reference_images = self._build_panel_references(
                idx, panel_analyses, panel_paths
            )

            # Build user_requirement from storyboard meta
            user_requirement = (
                f"Tone: {storyboard_meta.tone}. "
                f"Genre: {storyboard_meta.genre}. "
                f"Visual style: {style}. "
                f"Maintain visual consistency with the storyboard's composition and framing."
            )

            script2video_pipeline = Script2VideoPipeline(
                chat_model=self.chat_model,
                image_generator=self.image_generator,
                video_generator=self.video_generator,
                working_dir=scene_working_dir,
            )

            print(f"\n{'='*60}")
            print(f"🎬 Starting Scene {idx} (from panel {idx})")
            print(f"{'='*60}")

            final_video_path = await script2video_pipeline(
                script=scene_script,
                user_requirement=user_requirement,
                style=style,
                characters=characters,
                character_portraits_registry=character_portraits_registry,
                additional_reference_images=additional_reference_images,
            )
            all_video_paths.append(final_video_path)

        # Step 9: Concatenate Scene Videos
        final_video_path = os.path.join(self.working_dir, "final_video.mp4")
        if os.path.exists(final_video_path):
            print(f"🚀 Skipped concatenating videos, already exists.")
        else:
            print(f"🎬 Starting concatenating videos...")
            video_clips = [VideoFileClip(p) for p in all_video_paths]
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

    async def write_scene_scripts(
        self,
        panel_analyses: List[PanelAnalysis],
        visual_characters: List[VisualCharacter],
        storyboard_meta: StoryboardMeta,
    ) -> List[str]:
        """Step 7: Generate scene scripts with caching."""
        scripts_path = os.path.join(self.working_dir, "scene_scripts.json")

        if os.path.exists(scripts_path):
            with open(scripts_path, "r", encoding="utf-8") as f:
                scripts = json.load(f)
            print(f"🚀 Loaded {len(scripts)} scene scripts from existing file.")
            return scripts

        print("🧠 Writing scene scripts from panel analyses...")
        scripts = await self.scene_script_writer.write_scene_scripts(
            panel_analyses=panel_analyses,
            characters=visual_characters,
            storyboard_meta=storyboard_meta,
        )

        with open(scripts_path, "w", encoding="utf-8") as f:
            json.dump(scripts, f, ensure_ascii=False, indent=4)
        print(f"✅ Generated {len(scripts)} scene scripts and saved to {scripts_path}.")

        return scripts

    def _build_panel_references(
        self,
        scene_idx: int,
        panel_analyses: List[PanelAnalysis],
        panel_paths: List[str],
    ) -> List[Tuple[str, str]]:
        """Build additional reference image pairs from the source panel for this scene."""
        references = []

        # 1:1 mapping — scene_idx corresponds to panel_idx
        if scene_idx < len(panel_paths) and scene_idx < len(panel_analyses):
            pa = panel_analyses[scene_idx]
            description = (
                f"Storyboard reference panel. "
                f"Camera: {pa.camera_angle}. "
                f"Scene: {pa.scene_description[:150]}. "
                f"Use this as composition and framing reference."
            )
            references.append((panel_paths[scene_idx], description))

        return references

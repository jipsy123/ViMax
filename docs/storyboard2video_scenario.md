# Storyboard2Video Pipeline — Running Scenario

## Scenario: 12-panel action storyboard, 2 characters

**Input**: A single storyboard image (`storyboard.png`) — a 4x3 grid of hand-drawn panels depicting a chase sequence between a detective and a thief.

```
$ python main_storyboard2video.py
```

### Step 1: Panel Splitting (OpenCV, no API calls)
```
Splitting storyboard into panels...
  Detected 12 contours, grouped into 3 rows of 4 panels each.
  Saved panel_000.png through panel_011.png
Split storyboard into 12 panels.
```
Cache: `panels/panel_000.png` ... `panel_011.png`, `panels_manifest.json`

### Step 2: Holistic Storyboard Analysis (1 LLM call)
```
Analyzing storyboard holistically...
Storyboard analysis complete and saved.
```
All 12 panel images sent to the LLM in one multimodal message. Returns:
```json
{
  "narrative_summary": "A detective pursues a thief through city streets at night...",
  "tone": "tense, suspenseful",
  "visual_style": "noir-inspired, high contrast with dramatic shadows",
  "genre": "action/thriller",
  "total_panels": 12,
  "themes": ["justice", "pursuit", "urban danger"]
}
```
Cache: `storyboard_meta.json`

```
Auto-detected style: noir-inspired, high contrast with dramatic shadows
```

### Step 3: Per-Panel Analysis (12 LLM calls, parallel)
```
Analyzing 12 panels in parallel...
Analyzed 12 panels.
```
Each panel gets its own LLM call with the panel image + adjacent panels + holistic context. Example for panel 0:
```json
{
  "panel_idx": 0,
  "scene_description": "A detective in a trench coat stands under a streetlight, scanning a dark alley.",
  "environment": "Night. Wet cobblestone street, dim streetlamp, foggy background.",
  "characters_present": ["trench_coat_detective"],
  "camera_angle": "Medium shot, slightly low angle",
  "mood": "ominous, anticipatory",
  "implied_action": "The detective slowly turns his head, scanning the alley entrance.",
  "implied_audio": "Rain pattering on cobblestones. Distant police siren.",
  "narrative_continuity": "Opening shot. Establishes protagonist and setting."
}
```
Cache: `panel_analyses.json`

### Step 4: Character Identification (1 LLM call)
```
Identifying characters across panels...
Identified 2 unique characters.
```
All 12 panels + panel analyses sent in one multimodal call. Returns:
```json
[
  {
    "identifier": "Detective Morgan",
    "static_features": "Male, 40s, tall, sharp jawline, dark trench coat, fedora hat",
    "dynamic_features": "Determined expression, purposeful stride, occasionally draws revolver",
    "panel_appearances": [0, 1, 2, 3, 5, 6, 8, 9, 10, 11],
    "role_assessment": "protagonist"
  },
  {
    "identifier": "The Thief",
    "static_features": "Male, 30s, lean build, black hoodie, messenger bag slung across chest",
    "dynamic_features": "Frantic movement, looking over shoulder, clutching bag protectively",
    "panel_appearances": [1, 2, 3, 4, 5, 7, 8, 9, 10, 11],
    "role_assessment": "antagonist"
  }
]
```
Cache: `visual_characters.json`

### Step 5: Convert Characters (no API calls)
```
Converted 2 characters to scene format.
```
Maps `VisualCharacter` to `CharacterInScene` with `idx=0` (Detective Morgan), `idx=1` (The Thief).

Cache: `characters.json`

### Step 6: Character Portraits (6 image generation calls)
```
Generating portraits for Detective Morgan...
  front.png
  side.png
  back.png
Completed character portrait generation for Detective Morgan.

Generating portraits for The Thief...
  front.png
  side.png
  back.png
Completed character portrait generation for The Thief.

Completed character portrait generation for 2 characters.
```
Cache: `character_portraits/0_Detective Morgan/{front,side,back}.png`, `character_portraits/1_The Thief/{front,side,back}.png`, `character_portraits_registry.json`

### Step 7: Panel Videos (12 LLM + 12 image + 12 video calls, parallel)

All 12 panels run in parallel. Here's what happens inside each one:

**Panel 0** (Detective Morgan visible — from `panel_appearances`):
```
Selecting reference images for panel 0...
```
Reference pool built:
```
Image 0: "A front view portrait of Detective Morgan."     <- character portrait
Image 1: "A side view portrait of Detective Morgan."      <- character portrait
Image 2: "A back view portrait of Detective Morgan."      <- character portrait
Image 3: "Storyboard reference panel. Camera: Medium shot, slightly low angle. Scene: A detective in a trench coat stands under a streetlight..."  <- original panel
```
`ReferenceImageSelector` picks best refs (e.g., front portrait + panel image) and generates an optimized prompt:
```
Selected references for panel 0.
```
Cache: `frames/0/selector_output.json`

```
Generating frame for panel 0...
Generated frame for panel 0.
```
Cache: `frames/0/frame.png`

```
Generating video for panel 0...
```
Motion prompt: `"The detective slowly turns his head, scanning the alley entrance.\nRain pattering on cobblestones. Distant police siren."`
```
Generated video for panel 0.
```
Cache: `frames/0/video.mp4`

**Panel 3** (both characters visible — `panel_appearances` shows both appear in panel 3):
```
Selecting reference images for panel 3...
```
Reference pool:
```
Image 0: "A front view portrait of Detective Morgan."
Image 1: "A side view portrait of Detective Morgan."
Image 2: "A back view portrait of Detective Morgan."
Image 3: "A front view portrait of The Thief."
Image 4: "A side view portrait of The Thief."
Image 5: "A back view portrait of The Thief."
Image 6: "Storyboard reference panel. Camera: Wide shot..."
```
The selector picks the most relevant subset (e.g., Morgan front + Thief back + panel) and generates a prompt that specifies which character references which portrait.
```
Selected references for panel 3.
Generating frame for panel 3...
Generated frame for panel 3.
Generating video for panel 3...
Generated video for panel 3.
```

**Panel 4** (only The Thief visible):
```
Selecting reference images for panel 4...
```
Reference pool only has Thief's 3 portraits + panel image (4 images total — no Detective portraits since he doesn't appear in panel 4).

*(Panels 1-11 all run similarly in parallel, throttled by rate limiters)*

### Step 8: Concatenate (no API calls)
```
Starting concatenating videos...
Concatenated videos, saved to .working_dir/storyboard2video/final_video.mp4.

Final video saved to: .working_dir/storyboard2video/final_video.mp4
```

---

## Final API Call Tally

| Category | Calls | Source |
|---|---|---|
| LLM: holistic analysis | 1 | Step 2 |
| LLM: panel analysis | 12 | Step 3 (parallel) |
| LLM: character extraction | 1 | Step 4 |
| LLM: reference selection | 12 | Step 7 (parallel, 1 per panel) |
| **LLM total** | **26** | |
| Image: character portraits | 6 | Step 6 (2 chars x 3 views) |
| Image: panel frames | 12 | Step 7 (1 per panel) |
| **Image total** | **18** | |
| Video: panel videos | 12 | Step 7 (1 per panel) |
| **Video total** | **12** | |

## Cache structure on disk
```
.working_dir/storyboard2video/
├── panels/panel_000.png ... panel_011.png
├── panels_manifest.json
├── storyboard_meta.json
├── panel_analyses.json
├── visual_characters.json
├── characters.json
├── character_portraits_registry.json
├── character_portraits/
│   ├── 0_Detective Morgan/  front.png, side.png, back.png
│   └── 1_The Thief/         front.png, side.png, back.png
├── frames/
│   ├── 0/  selector_output.json, frame.png, video.mp4
│   ├── 1/  ...
│   └── 11/ ...
└── final_video.mp4
```

If the run crashes at any point (e.g., rate limit hit during panel 7's video generation), re-running picks up from exactly where it left off — panels 0-6 skip entirely, panel 7 skips its selector + frame and retries only the video.

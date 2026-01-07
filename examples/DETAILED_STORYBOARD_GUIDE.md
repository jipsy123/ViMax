# Working with Detailed Storyboards in ViMax

This guide explains how to use ViMax when you already have a detailed, pre-planned storyboard (like a 3x3 panel layout with specific shot descriptions).

## 🤔 The Challenge

ViMax's **StoryboardArtist agent** is designed to automatically plan shots from simple ideas or scripts. If you provide an already-detailed storyboard, the agent might:

- ❌ Reinterpret your specific shot compositions
- ❌ Change camera angles you carefully specified
- ❌ Lose specific visual details you included
- ❌ Reorganize the shot sequence

**The problem**: ViMax wants to do the planning, but you've already done it!

---

## ✅ Three Solutions

We've created **three approaches** to preserve your detailed planning while using ViMax's powerful generation system:

### **Approach 1: Script Format** (⭐ Recommended for Most Users)
- **Difficulty**: Easy
- **Control Level**: Medium-High
- **Best For**: Users with detailed panel descriptions who want some AI assistance

Convert your storyboard panels into screenplay-style scene descriptions. Let ViMax's agents handle the shot planning, but guide them with rich visual details.

**File**: `examples/detailed_storyboard_approach1_script.py`

### **Approach 2: Guided Planning** (⭐ Best Balance)
- **Difficulty**: Easy
- **Control Level**: High
- **Best For**: Users who want to guide the AI precisely via requirements

Provide a clean narrative as the `idea`, then use the `user_requirement` parameter to specify exact shot compositions, camera angles, and panel structure.

**File**: `examples/detailed_storyboard_approach2_guided.py`

### **Approach 3: Direct Injection** (⚡ Maximum Control)
- **Difficulty**: Advanced
- **Control Level**: Maximum
- **Best For**: Users who need pixel-perfect control and understand ViMax's internal data structures

Bypass the StoryboardArtist agent entirely by creating the storyboard data structure manually and saving it to the working directory.

**File**: `examples/detailed_storyboard_approach3_direct.py`

---

## 📊 Detailed Comparison

| Feature | Approach 1: Script | Approach 2: Guided | Approach 3: Direct |
|---------|-------------------|-------------------|-------------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Control Over Shots** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Preserves Details** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **AI Assistance** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Best For** | Quick conversion | Detailed guidance | Exact replication |

---

## 🎯 When to Use Each Approach

### Use **Approach 1 (Script Format)** When:
- ✅ You have detailed panel descriptions but want AI help with shot planning
- ✅ You're comfortable with screenplay format
- ✅ You want ViMax to add cinematographic variety
- ✅ You're okay with the AI making some creative decisions

**Example**: You have a 9-panel storyboard with visual descriptions, but you're open to the AI adding intercutting, reaction shots, or camera movements.

### Use **Approach 2 (Guided Planning)** When:
- ✅ You want to specify exact shot compositions via requirements
- ✅ You have a clear vision but want AI to handle technical details
- ✅ You want the best balance of control and automation
- ✅ You're providing a 3x3 or similar grid storyboard

**Example**: You have a precise 3x3 storyboard layout with specific camera angles, lighting descriptions, and text overlays that you want preserved exactly.

### Use **Approach 3 (Direct Injection)** When:
- ✅ You need pixel-perfect control over every shot
- ✅ You're comfortable working with Python data structures
- ✅ You want to bypass ViMax's planning agents entirely
- ✅ You have a production-ready storyboard that shouldn't be changed

**Example**: You're a professional storyboard artist with a client-approved board that must be executed exactly as designed.

---

## 💡 Example: Your SpaceX Storyboard

Let's look at how your detailed SpaceX storyboard would work with each approach:

### Your Original Prompt Structure:
```
3x3 Grid:
- Row 1: The Dream and The Falls (Panels 1-3)
- Row 2: The Turning Point (Panels 4-6)
- Row 3: The Revolution (Panels 7-9)

Each panel has:
- Visual Description
- Specific prompt for AI
- Audio/Text overlays
- Camera angle
- Lighting specification
```

### **Approach 1**: Convert to Script
```python
script = """
EXT. OFFICE BALCONY - NIGHT (2002)
[Detailed scene description matching Panel 1]
TEXT OVERLAY: "2002: The Goal is Mars."

INT. WAREHOUSE - DAY
[Detailed scene description matching Panel 2]
...
"""
```
✅ **Pros**: Natural format, easy to write
⚠️ **Cons**: AI might add/remove shots

### **Approach 2**: Use Requirements
```python
idea = "SpaceX story from dream to reusable rockets..."

user_requirement = """
STRUCTURE: Create exactly 3 scenes with 3 panels each.

Scene 1 - Panel 1 "The Vision":
- Location: Office balcony at night
- Shot type: Medium close-up
- Lighting: Soft ambient city light
- Include text: "2002: The Goal is Mars."
[Repeat for all 9 panels with exact specifications]
"""
```
✅ **Pros**: Precise control, guides AI exactly
✅ **Cons**: Requires detailed requirements text

### **Approach 3**: Manual Data Structure
```python
storyboard = [
    ShotBriefDescription(
        idx=0,
        cam_idx=0,
        visual_desc="A medium close-up shot of...",
        audio_desc="[Text Overlay] 2002: The Goal is Mars."
    ),
    # Repeat for all 9+ shots
]
```
✅ **Pros**: Perfect control, exact replication
⚠️ **Cons**: Requires understanding ViMax internals

---

## 🎬 Recommended Workflow

For your SpaceX storyboard specifically, we recommend **Approach 2 (Guided Planning)**:

1. **Extract the narrative** → Put in `idea` parameter
2. **Extract all panel specifications** → Put in `user_requirement` parameter
3. **Specify visual style** → Put in `style` parameter
4. **Run the pipeline** → ViMax generates with your exact specifications

This preserves:
- ✅ Your 3x3 panel structure
- ✅ Your specific camera angles
- ✅ Your lighting descriptions
- ✅ Your text overlays
- ✅ Your audio specifications

While still getting:
- ✅ ViMax's multi-shot planning
- ✅ Character consistency tracking
- ✅ Parallel generation speed
- ✅ Professional video assembly

---

## 📝 Quick Start Template

Here's a template for converting your detailed storyboard:

```python
import asyncio
from pipelines.idea2video_pipeline import Idea2VideoPipeline

# 1. Extract the core narrative
idea = """
[Your story in 2-3 paragraphs]
"""

# 2. Specify exact panel structure
user_requirement = """
STRUCTURE: Create exactly [N] scenes.

Scene 1 - Panel 1 "[Panel Name]":
- Location: [Where]
- Subject: [Who/What]
- Shot type: [Wide/Medium/Close-up/etc.]
- Camera angle: [High/Low/Eye-level/etc.]
- Mood: [Emotion]
- Lighting: [Description]
- Include: [Text overlays, special elements]

[Repeat for each panel]

CINEMATOGRAPHY REQUIREMENTS:
- [Overall style notes]
- [Pacing requirements]
- [Technical specifications]
"""

# 3. Define visual style
style = """
[Visual style description]
[Evolution of style across scenes]
[Reference comparisons]
"""

# 4. Run
async def main():
    pipeline = Idea2VideoPipeline.init_from_config(
        config_path="configs/idea2video_vertex.yaml"
    )
    await pipeline(idea=idea, user_requirement=user_requirement, style=style)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔧 Tips for Best Results

### For All Approaches:

1. **Be Specific About Characters**
   - Include detailed descriptions: age, appearance, clothing
   - Use consistent identifiers (e.g., `<ELON MUSK>`)
   - Specify which characters appear in which shots

2. **Specify Camera Work Precisely**
   - Shot type: Wide, Medium, Close-up, Extreme close-up
   - Angle: High, Low, Eye-level, Dutch angle
   - Movement: Static, Pan, Tilt, Dolly, Crane

3. **Describe Lighting Clearly**
   - Source: Natural, Artificial, Mixed
   - Quality: Harsh, Soft, Diffused
   - Direction: Front, Back, Side
   - Time: Golden hour, Midday, Night

4. **Include Audio/Text Specifications**
   - Text overlays: Exact wording
   - Sound effects: Specific descriptions
   - Music cues: Mood and timing

### For Approach 2 Specifically:

5. **Use Clear Section Headers**
   ```
   Scene 1 - Panel 1 "The Vision":
   Scene 1 - Panel 2 "The Garage Days":
   ```

6. **Number Everything**
   - Scenes: 1, 2, 3
   - Panels: 1-9
   - Shots: Specify how many per panel

7. **Be Explicit About Structure**
   ```
   CRITICAL: Preserve the exact narrative structure - 9 distinct moments.
   ```

---

## ⚠️ Common Pitfalls to Avoid

1. **Don't mix approaches** - Pick one and stick with it
2. **Don't under-specify** - More detail = better results
3. **Don't skip character descriptions** - ViMax needs them for consistency
4. **Don't forget audio** - Text overlays and sounds are part of your vision
5. **Don't expect 100% accuracy** - Even Approach 3 involves AI generation

---

## 🎓 Learning Path

**Beginner** → Start with **Approach 1**
- Convert your panels to script format
- See how ViMax interprets them
- Learn what details it preserves/changes

**Intermediate** → Move to **Approach 2**
- Use detailed requirements
- Guide the AI precisely
- Balance control and automation

**Advanced** → Try **Approach 3**
- Understand ViMax's data structures
- Bypass agents selectively
- Maximum control for production work

---

## 📚 Additional Resources

- **Example Files**:
  - `examples/detailed_storyboard_approach1_script.py`
  - `examples/detailed_storyboard_approach2_guided.py`
  - `examples/detailed_storyboard_approach3_direct.py`

- **Data Structures**:
  - `interfaces/shot_description.py` - Shot structure definition
  - `interfaces/character.py` - Character structure
  - `agents/storyboard_artist.py` - How ViMax plans shots

- **Documentation**:
  - `VERTEX_AI_INTEGRATION.md` - Setting up Vertex AI
  - `README_ZH.md` - Original ViMax documentation

---

## ❓ FAQ

**Q: Will my specific camera angles be preserved?**
- Approach 1: Mostly, if described clearly
- Approach 2: Yes, if specified in requirements
- Approach 3: Exactly

**Q: Can I specify text overlays?**
- Yes! Include them in `audio_desc` field or requirements

**Q: How many shots will I get?**
- Approach 1: AI decides based on scene complexity
- Approach 2: You specify in requirements (e.g., "2-3 shots per panel")
- Approach 3: Exactly as many as you define

**Q: Will character appearance stay consistent?**
- Yes! All approaches use ViMax's character portrait system

**Q: Can I mix detailed and simple descriptions?**
- Yes! Provide detail where needed, let AI fill in elsewhere

---

## 🎬 Summary

**Your detailed storyboard is valuable** - don't let it get lost in translation!

Use:
- **Approach 2** for your SpaceX storyboard (best balance)
- **Approach 1** if you want more AI creative freedom
- **Approach 3** if you need production-ready precision

All three preserve ViMax's core strengths:
- ✅ Long video generation (minutes, not seconds)
- ✅ Multi-shot professional cinematography
- ✅ Character consistency across shots
- ✅ Parallel generation for speed
- ✅ Intelligent assembly and transitions

**The result**: Your detailed vision + ViMax's powerful architecture = Professional long-form video! 🚀

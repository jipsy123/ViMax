# Using Images with ViMax: Complete Guide

ViMax supports **three ways** to use your own images instead of relying purely on text prompts.

---

## ✅ **What You Can Do**

### **1. Custom Character Portraits** (⭐ Easiest)
Use your own photos/drawings as character references
- **Use Case**: Real people, brand mascots, existing character designs
- **Difficulty**: Easy
- **Example**: `custom_character_images.py`

### **2. Storyboard Image References** (⭐⭐ Advanced)
Use storyboard sketches/panels to guide composition
- **Use Case**: Convert hand-drawn storyboards, match concept art
- **Difficulty**: Advanced
- **Example**: `custom_storyboard_images.py`

### **3. Hybrid Text + Image Prompting** (⭐⭐⭐ Expert)
Combine detailed text prompts with reference images
- **Use Case**: Maximum control over every aspect
- **Difficulty**: Expert
- **Example**: Combine approaches 1 & 2

---

## 🎨 **Option 1: Custom Character Portraits**

### **What It Does**
Replaces AI-generated character portraits with your own images, ensuring characters look exactly like your references throughout the video.

### **When to Use**
- ✅ You have photos of real people
- ✅ You have brand mascots/logos
- ✅ You have character designs from previous work
- ✅ You want consistent character appearance

### **How It Works**

```python
from pipelines.script2video_pipeline import Script2VideoPipeline
from interfaces import CharacterInScene

# Define characters
characters = [
    CharacterInScene(
        idx=0,
        identifier_in_scene="ELON MUSK",
        description="Male, 40s, determined, casual business attire"
    )
]

# Provide YOUR images (front, side, back views)
character_portraits_registry = {
    "ELON MUSK": {
        "front": {
            "path": "/path/to/elon_front.jpg",  # Your photo
            "description": "Front view of Elon Musk"
        },
        "side": {
            "path": "/path/to/elon_side.jpg",   # Your photo
            "description": "Side profile of Elon Musk"
        },
        "back": {
            "path": "/path/to/elon_back.jpg",   # Your photo
            "description": "Back view of Elon Musk"
        }
    }
}

# Generate video
await pipeline(
    script=script,
    user_requirement=requirement,
    style=style,
    characters=characters,  # Pass defined characters
    character_portraits_registry=character_portraits_registry  # YOUR images!
)
```

### **Image Requirements**
- **Format**: JPG, PNG (standard image formats)
- **Views Needed**: Front, Side, Back (3 images per character)
- **Quality**: Higher resolution = better results (1024x1024+ recommended)
- **Background**: Clean background preferred (or AI will include it)
- **Lighting**: Even lighting for best consistency

### **Tips**
✅ Use high-quality, well-lit photos
✅ Keep backgrounds simple/neutral
✅ Ensure all 3 views show same clothing/styling
✅ Use consistent aspect ratio across views
⚠️ Don't mix different clothing styles between views

---

## 🖼️ **Option 2: Storyboard Image References**

### **What It Does**
Uses your storyboard sketches/panels as reference images to guide the composition and framing of generated shots.

### **When to Use**
- ✅ You have hand-drawn storyboards
- ✅ You have concept art you want to match
- ✅ You want specific compositions/camera angles
- ✅ You're adapting existing visual material

### **How It Works**

The ReferenceImageSelector agent can use storyboard images alongside character portraits when generating frames. Your storyboard panels guide:
- Camera angles and framing
- Character positioning
- Environment layout
- Visual composition

### **Implementation Approaches**

#### **Approach A: Indirect (via Character Portraits)**
```python
# Use storyboard panels as "environment" character references
character_portraits_registry = {
    "BACKGROUND_ENV": {
        "front": {
            "path": "/path/to/storyboard_panel_1.jpg",
            "description": "Office balcony environment with Mars visible"
        },
        "side": {
            "path": "/path/to/storyboard_panel_1_angle2.jpg",
            "description": "Side view of balcony environment"
        },
        "back": {
            "path": "/path/to/storyboard_panel_1_angle3.jpg",
            "description": "Alternate angle of balcony"
        }
    }
}
```

#### **Approach B: Direct (via Working Directory)**
```python
import os
import shutil

# Set up working directory
pipeline.working_dir = ".working_dir/custom_storyboard"
os.makedirs(pipeline.working_dir, exist_ok=True)

# Pre-place storyboard images in shot directories
for shot_idx, panel_path in enumerate(storyboard_panels):
    shot_dir = os.path.join(pipeline.working_dir, "shots", str(shot_idx))
    os.makedirs(shot_dir, exist_ok=True)

    # Copy your storyboard panel
    shutil.copy(
        panel_path,
        os.path.join(shot_dir, "reference_composition.png")
    )

# Then run pipeline - it will find and use these references
await pipeline(script=script, ...)
```

### **Storyboard Image Requirements**
- **Format**: JPG, PNG
- **Content**: Clear composition showing:
  - Camera angle
  - Subject placement
  - Background elements
  - Key visual elements
- **Quality**: Sketch quality is fine, doesn't need to be polished
- **Annotations**: Can include arrows, notes (AI will ignore them)

---

## 🎯 **Option 3: Hybrid Text + Image**

### **What It Does**
Combines detailed text prompts (from the storyboard guide) with custom images for maximum control.

### **When to Use**
- ✅ You have both detailed descriptions AND reference images
- ✅ You need pixel-perfect control
- ✅ Production work requiring exact specifications

### **How It Works**

```python
# 1. Detailed text prompt (from DETAILED_STORYBOARD_GUIDE.md)
user_requirement = """
Scene 1 - Panel 1 "The Vision":
- Location: Office balcony at night
- Subject: Elon Musk gazing at Mars
- Shot type: Medium close-up
- Camera angle: Eye level
- Lighting: Soft ambient city light
- Composition: Subject right of frame, Mars upper left
...
"""

# 2. Character reference images
character_portraits_registry = {
    "ELON MUSK": {
        "front": {"path": "/your/elon_front.jpg", ...},
        "side": {"path": "/your/elon_side.jpg", ...},
        "back": {"path": "/your/elon_back.jpg", ...}
    }
}

# 3. Storyboard panel references
# Pre-place in working directory (Approach B above)

# 4. Generate with ALL inputs
await pipeline(
    script=script,
    user_requirement=user_requirement,  # Detailed text
    style=style,
    characters=characters,
    character_portraits_registry=character_portraits_registry  # Your images
)
```

### **Result**
- Text guides: Shot composition, camera angles, lighting
- Character images ensure: Exact character appearance
- Storyboard images guide: Environmental composition
- **= Maximum fidelity to your vision**

---

## 📊 **Comparison Table**

| Capability | Text Only | + Character Images | + Storyboard Images | Hybrid (All) |
|------------|-----------|-------------------|---------------------|--------------|
| **Character Consistency** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Composition Control** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Setup Time** | 5 min | 15 min | 30 min | 45 min |
| **Best For** | Quick tests | Real people | Visual matching | Production |

---

## 💡 **Practical Examples**

### **Example 1: Real Person in Video**
```python
# You want Elon Musk in your video using actual photos

characters = [CharacterInScene(idx=0, identifier_in_scene="ELON MUSK", ...)]

character_portraits_registry = {
    "ELON MUSK": {
        "front": {"path": "elon_photos/front.jpg", "description": "Elon front"},
        "side": {"path": "elon_photos/side.jpg", "description": "Elon side"},
        "back": {"path": "elon_photos/back.jpg", "description": "Elon back"}
    }
}
```
**Result**: Video featuring Elon with consistent appearance matching your photos

### **Example 2: Brand Mascot**
```python
# Company mascot "Robo" needs to appear in training video

character_portraits_registry = {
    "ROBO": {
        "front": {"path": "brand/robo_front.png", "description": "Robo mascot front"},
        "side": {"path": "brand/robo_side.png", "description": "Robo mascot side"},
        "back": {"path": "brand/robo_back.png", "description": "Robo mascot back"}
    }
}
```
**Result**: Your exact brand mascot appears consistently throughout

### **Example 3: Convert Hand-Drawn Storyboard**
```python
# You sketched 9 storyboard panels on paper, scanned them

storyboard_panels = [
    "scans/panel_1_vision.jpg",
    "scans/panel_2_garage.jpg",
    ...
]

# Use Approach 2B to pre-place them
# ViMax generates video matching your panel compositions
```
**Result**: Video that closely matches your hand-drawn storyboard

---

## 🔧 **Technical Details**

### **How ViMax Uses Your Images**

1. **Character Portraits**:
   - Loaded into `character_portraits_registry`
   - Used by `ReferenceImageSelector` agent
   - Passed to image generator as reference images
   - Ensures character consistency across all shots

2. **Storyboard References**:
   - Can be included in available reference images
   - AI analyzes composition and framing
   - Guides image generation process
   - Not pixel-perfect, but influences strongly

3. **Image Processing**:
   - Images are loaded as PIL/numpy arrays
   - Passed to image generator (Imagen 3, etc.)
   - Used as style/composition reference
   - Combined with text prompts

### **Data Structure**

```python
# Character portraits registry format
{
    "CHARACTER_NAME": {
        "front": {
            "path": "/absolute/path/to/image.jpg",
            "description": "Text description of this view"
        },
        "side": {...},
        "back": {...}
    }
}
```

### **File Paths**
- Use **absolute paths**: `/home/user/images/photo.jpg`
- Or relative to working dir: `./my_refs/photo.jpg`
- Ensure files exist before running
- Supported formats: JPG, PNG, WebP

---

## ⚠️ **Limitations & Tips**

### **Limitations**
- ❌ Not pixel-perfect: AI interprets references, doesn't copy exactly
- ❌ Can't guarantee exact composition: Text + images = guidance, not law
- ❌ Quality depends on: Reference image quality + model capabilities
- ❌ Multiple references: Too many can confuse the AI

### **Best Practices**
✅ **Fewer is Better**: 1-3 reference images per shot works best
✅ **High Quality**: Use 1024x1024+ resolution for references
✅ **Consistency**: Keep lighting/style consistent across references
✅ **Clear Subjects**: Avoid cluttered backgrounds in references
✅ **Test First**: Try with 1-2 shots before full production

### **Common Issues**

**Problem**: Character doesn't look like reference
- **Solution**: Use higher quality images, multiple consistent views

**Problem**: Storyboard composition not followed
- **Solution**: Add detailed text descriptions matching the image

**Problem**: AI mixes elements from multiple references
- **Solution**: Reduce number of references, be more specific in text

---

## 📚 **Examples**

- **Basic Character Images**: `custom_character_images.py`
- **Storyboard References**: `custom_storyboard_images.py`
- **Detailed Text Guide**: `DETAILED_STORYBOARD_GUIDE.md`

---

## 🎬 **Summary**

**YES - You can use images with ViMax!**

**Three approaches**:
1. **Character Portraits** → Real people/mascots (Easy)
2. **Storyboard References** → Match compositions (Advanced)
3. **Hybrid** → Maximum control (Expert)

**Best workflow**:
- Start with **text only** to test
- Add **character images** for consistency
- Add **storyboard images** for composition
- Combine **all** for production work

**The result**: Your vision (text + images) + ViMax's architecture = Professional long-form video! 🚀

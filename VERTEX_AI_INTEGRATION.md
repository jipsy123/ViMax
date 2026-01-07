# Integrating ViMax with Google Vertex AI

This guide shows you how to use ViMax's long video generation architecture with your own **Google Vertex AI** account (Veo 3 + Imagen 3).

## 🎯 What You're Extracting

ViMax's **architectural innovation** for long videos:
- ✅ **Multi-agent planning system** (Storyboard Artist, Camera Tree, etc.)
- ✅ **Shot-by-shot decomposition** (scenes → shots → frames)
- ✅ **Parallel generation** (all shots generated concurrently)
- ✅ **Intelligent reference tracking** (character consistency)
- ✅ **Professional cinematography** (multiple camera angles, transitions)

**What changes**: Just the API endpoints (swap Google AI Studio → Vertex AI)

---

## 📋 Prerequisites

### 1. Google Cloud Setup

```bash
# Install Google Cloud SDK
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate with your Google Cloud account
gcloud auth application-default login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com
```

### 2. Install Dependencies

```bash
# Install Vertex AI SDK
pip install google-cloud-aiplatform

# Or update your environment
uv add google-cloud-aiplatform
uv sync
```

### 3. Verify Access to Veo 3

Ensure your Google Cloud project has access to:
- **Veo 3** (preview access may be required)
- **Imagen 3** (preview access may be required)

Check here: https://console.cloud.google.com/vertex-ai/publishers

---

## 🚀 Quick Start

### Step 1: Update Configuration

Edit `configs/idea2video_vertex.yaml` or `configs/script2video_vertex.yaml`:

```yaml
chat_model:
  init_args:
    model: gemini-2.5-flash
    model_provider: google_vertexai
    project: YOUR_GCP_PROJECT_ID  # ← Replace this
    location: us-central1

image_generator:
  class_path: tools.ImageGeneratorImagen3VertexAPI
  init_args:
    project_id: YOUR_GCP_PROJECT_ID  # ← Replace this
    location: us-central1
    model_name: imagen-3.0-generate-001

video_generator:
  class_path: tools.VideoGeneratorVeo3VertexAPI
  init_args:
    project_id: YOUR_GCP_PROJECT_ID  # ← Replace this
    location: us-central1
    t2v_model: veo-3-001
    ff2v_model: veo-3-001
    flf2v_model: veo-3-001
```

### Step 2: Run Your First Video

```bash
# For idea-to-video
python main_idea2video_vertex.py

# For script-to-video
python main_script2video_vertex.py
```

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    ViMax Pipeline (Unchanged)                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. Scene Decomposition                                 │  │
│  │    - Break long narrative into scenes                  │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 2. Shot Planning (Storyboard Artist)                   │  │
│  │    - Design cinematography for each scene              │  │
│  │    - Multiple camera angles, shot types                │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 3. Camera Tree Construction                            │  │
│  │    - Hierarchical camera relationships                 │  │
│  │    - Smooth transitions between angles                 │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4. Parallel Frame Generation                           │  │
│  │    - Generate first/last frames for all shots          │  │
│  │    - Use reference images for consistency              │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 5. Parallel Video Generation                           │  │
│  │    - Convert frames → videos (all shots at once)       │  │
│  │    - Keyframe interpolation (first + last frame)       │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 6. Intelligent Assembly                                │  │
│  │    - Concatenate all shots → final video               │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│              API Layer (Vertex AI Integration)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Gemini     │  │   Imagen 3   │  │    Veo 3     │        │
│  │ (Planning)   │  │   (Frames)   │  │   (Videos)   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Files Created for Vertex AI Integration

### New Files

1. **`tools/image_generator_imagen3_vertex_api.py`**
   - Adapter for Vertex AI Imagen 3
   - Supports reference images for character consistency
   - Handles async operations

2. **`tools/video_generator_veo3_vertex_api.py`**
   - Adapter for Vertex AI Veo 3
   - Supports 3 modes:
     - Text-to-Video (no reference)
     - Image-to-Video (1 reference frame)
     - Keyframe-to-Video (2 reference frames)

3. **`configs/idea2video_vertex.yaml`**
   - Configuration for idea-to-video with Vertex AI

4. **`configs/script2video_vertex.yaml`**
   - Configuration for script-to-video with Vertex AI

5. **`main_idea2video_vertex.py`**
   - Example script using Vertex AI config

6. **`main_script2video_vertex.py`**
   - Example script using Vertex AI config

---

## 🔑 Key Differences: Vertex AI vs Google AI Studio

| Feature | Google AI Studio (Default) | Vertex AI (Your Integration) |
|---------|---------------------------|------------------------------|
| **Authentication** | API Key | GCloud ADC |
| **Access** | Public preview | Enterprise GCP account |
| **Billing** | Separate | GCP billing account |
| **Quotas** | Shared public limits | Your dedicated quotas |
| **Models** | Veo 3.1 preview | Veo 3 production |
| **Control** | Limited | Full control |
| **Cost** | Pay-per-use | GCP pricing |

---

## 💡 How It Works: The "No Extension" Approach

### ❌ Traditional Extension API Approach
```
Generate 6s → Extend → Extend → Extend → Extend
   (Clip 1)    (Clip 2) (Clip 3) (Clip 4) (Clip 5)

Problems:
- Sequential (slow)
- Character drift
- No planning
- Limited control
```

### ✅ ViMax with Vertex AI Approach
```
1. PLAN: Storyboard designs 5 shots
   - Shot 0: Wide establishing shot
   - Shot 1: Medium two-shot
   - Shot 2: Close-up character A
   - Shot 3: Over-shoulder reverse
   - Shot 4: Wide resolution shot

2. GENERATE FRAMES IN PARALLEL:
   Shot 0: First frame ✓
   Shot 1: First frame ✓, Last frame ✓  (uses Shot 0 as reference)
   Shot 2: First frame ✓, Last frame ✓  (uses character portrait)
   Shot 3: First frame ✓               (uses Shot 2 as reference)
   Shot 4: First frame ✓, Last frame ✓

3. GENERATE VIDEOS IN PARALLEL:
   All 5 shots → Vertex AI Veo 3 (keyframe interpolation)
   ↓
   Each shot: 8 seconds

4. STITCH:
   Concatenate → 40-second professional video

Advantages:
- Parallel (fast)
- Character consistency (portraits + references)
- Professional cinematography
- Full control
```

---

## 🎬 Example Usage

### Idea to Video

```python
import asyncio
from pipelines.idea2video_pipeline import Idea2VideoPipeline

idea = """
A detective cat discovers a mysterious toy in an abandoned mansion.
She investigates room by room, building suspense until the reveal.
"""

user_requirement = """
For adults, create exactly 3 scenes.
Each scene should have 4-6 shots for cinematic variety.
"""

style = "Film noir, moody lighting, dramatic angles"

async def main():
    pipeline = Idea2VideoPipeline.init_from_config(
        config_path="configs/idea2video_vertex.yaml"
    )
    await pipeline(
        idea=idea,
        user_requirement=user_requirement,
        style=style
    )

if __name__ == "__main__":
    asyncio.run(main())
```

**Result**: ~15 shots × 8 seconds = **2-minute cinematic video** with professional shot composition!

---

## 🔧 Customization Options

### Adjust Rate Limits

In your config file:
```yaml
video_generator:
  max_requests_per_minute: 10  # Adjust based on your quota
  max_requests_per_day: 100    # Adjust based on budget
```

### Change Models

```yaml
image_generator:
  init_args:
    model_name: imagen-3.0-generate-001  # or newer model

video_generator:
  init_args:
    t2v_model: veo-3-001   # Text-to-video model
    ff2v_model: veo-3-001  # Image-to-video model
    flf2v_model: veo-3-001 # Keyframe interpolation model
```

### Adjust Video Parameters

Modify the video generator adapter (`tools/video_generator_veo3_vertex_api.py`):
```python
async def generate_single_video(
    prompt: str,
    reference_image_paths: List[str],
    resolution: str = "1080p",  # or "720p", "480p"
    aspect_ratio: str = "16:9",  # or "9:16", "1:1"
    duration: int = 8,           # seconds per shot
):
```

---

## 💰 Cost Considerations

**Vertex AI Pricing** (approximate, check current pricing):
- **Gemini 2.5 Flash**: ~$0.00001/character
- **Imagen 3**: ~$0.02-0.05/image
- **Veo 3**: ~$0.10-0.30/second of video

**Example Cost for 2-minute video**:
- Planning (Gemini): ~$0.10
- Frames (15 shots × 2 frames): ~$0.60
- Videos (15 shots × 8 sec): ~$36.00
- **Total**: ~$37 for a 2-minute professional video

**Compare to traditional production**: Thousands of dollars + weeks of work!

---

## 🐛 Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
gcloud auth application-default login

# Verify current project
gcloud config get-value project

# Check enabled APIs
gcloud services list --enabled
```

### Quota Errors

1. Check quotas: https://console.cloud.google.com/iam-admin/quotas
2. Request quota increase if needed
3. Adjust rate limits in config files

### Model Access

If you get "model not found" errors:
1. Verify Veo 3 access in your project
2. Check model availability in your region
3. Try different location (e.g., `us-central1`, `europe-west4`)

---

## 📚 Additional Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Veo 3 Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/video/overview)
- [Imagen 3 Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview)
- [ViMax GitHub](https://github.com/HKUDS/ViMax)

---

## ✅ Summary

You've successfully integrated ViMax's long video architecture with your Vertex AI account!

**What you can now do**:
1. Generate **multi-minute videos** (not just 6-8 second clips)
2. Use **professional cinematography** (multiple camera angles, shot types)
3. Maintain **character consistency** across long videos
4. Generate **faster** (parallel shot generation)
5. Have **full control** over your infrastructure and costs

**The secret**: ViMax's innovation isn't the API—it's the **multi-agent planning system** that orchestrates shot-by-shot video generation with cinematic intelligence.

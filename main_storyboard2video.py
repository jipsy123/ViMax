import asyncio
from pipelines.storyboard2video_pipeline import Storyboard2VideoPipeline


# SET YOUR STORYBOARD IMAGE PATH HERE
storyboard_image_path = "path/to/your/storyboard.png"

# Optional: override the auto-detected style from the storyboard
# If None, style is automatically inferred from the storyboard's visual style
style = None


async def main():
    pipeline = Storyboard2VideoPipeline.init_from_config(
        config_path="configs/storyboard2video.yaml"
    )
    final_video = await pipeline(
        storyboard_image_path=storyboard_image_path,
        style=style,
    )
    print(f"\nFinal video saved to: {final_video}")


if __name__ == "__main__":
    asyncio.run(main())

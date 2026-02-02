import asyncio
from pipelines.storyboard2video_pipeline import Storyboard2VideoPipeline


async def main():
    storyboard_image_path = input("Enter the path to your storyboard image: ").strip()

    style_input = input("Enter visual style (or press Enter to auto-detect from storyboard): ").strip()
    style = style_input if style_input else None

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

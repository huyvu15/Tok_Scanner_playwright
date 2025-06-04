from TikTokApi import TikTokApi
import asyncio
import os
import json

ms_token = os.environ.get("ms_token", None)  # get your own ms_token from your cookies on tiktok.com

async def trending_videos():
    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token], 
            num_sessions=1, 
            sleep_after=3, 
            browser=os.getenv("TIKTOK_BROWSER", "chromium")
        )

        videos_data = []

        async for video in api.trending.videos(count=30):
            video_data = video.as_dict
            videos_data.append(video_data)

        # Save all video data to a.json
        with open("a.json", "w", encoding="utf-8") as f:
            json.dump(videos_data, f, ensure_ascii=False, indent=4)

        print("Saved trending videos to a.json")

if __name__ == "__main__":
    asyncio.run(trending_videos())

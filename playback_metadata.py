from TikTokApi import TikTokApi
import asyncio
import os
import json

ms_token = os.environ.get("ms_token", None) # get your own ms_token from your cookies on tiktok.com

async def trending_videos():
    videos_data = []
    
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser=os.getenv("TIKTOK_BROWSER", "chromium"))
        async for video in api.trending.videos(count=30):
            print(f"Processing video: {video.id}")
            videos_data.append(video.as_dict)
    
    # Save data to JSON file
    with open('a.json', 'w', encoding='utf-8') as f:
        json.dump(videos_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(videos_data)} videos to a.json")

if __name__ == "__main__":
    asyncio.run(trending_videos())
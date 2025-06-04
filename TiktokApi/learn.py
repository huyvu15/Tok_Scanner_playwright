import asyncio
from TikTokApi import TikTokApi

async def main():
    api = TikTokApi()
    await api.create_sessions(num_sessions=1)
    try:
        hashtag = api.hashtag(name="phng.anh.l157")
        await hashtag.info()  # Load thông tin để có id

        videos = []
        async for video in hashtag.videos(count=10):
            videos.append(video)

        for v in videos:
            print(f"Video ID: {v.id}")
            print(f"Author: {v.author.username}")
            print(f"Description: {v.desc}")
            print(f"Stats: {v.stats}")
            print(f"Video URL: {v.video.download_addr}")
            print("="*40)
    finally:
        if hasattr(api, "stop"):
            await api.stop()

if __name__ == "__main__":
    asyncio.run(main())
    

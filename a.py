import asyncio
import json
from TikTokApi import TikTokApi
from TikTokApi.exceptions import CaptchaException, EmptyResponseException, InvalidJSONException

async def get_trending_videos(api, count=10):
    try:
        async for video in api.trending.videos(count=count):
            description = getattr(video, 'desc', None) or getattr(video, 'text', 'No description')
            print(f"Trending Video ID: {video.id}, Description: {description}")
    except (CaptchaException, EmptyResponseException, InvalidJSONException) as e:
        print(f"Error fetching trending videos: {e}")

async def get_videos_by_hashtag(api, hashtag_name, count=10):
    try:
        hashtag = api.hashtag(name=hashtag_name)
        await hashtag.info()
        async for video in hashtag.videos(count=count):
            description = getattr(video, 'desc', None) or getattr(video, 'text', 'No description')
            print(f"Hashtag #{hashtag_name} Video ID: {video.id}, Description: {description}")
    except (CaptchaException, EmptyResponseException, InvalidJSONException) as e:
        print(f"Error fetching videos by hashtag '{hashtag_name}': {e}")

async def get_user_info(api, username):
    try:
        user = api.user(username=username)
        user_data = await user.info()
        print(f"User info for {username}: {user_data}")
    except (CaptchaException, EmptyResponseException, InvalidJSONException) as e:
        print(f"Error fetching user info for {username}: {e}")

async def get_user_videos(api, username, count=10):
    try:
        user = api.user(username=username)
        async for video in user.videos(count=count):
            description = getattr(video, 'desc', None) or getattr(video, 'text', 'No description')
            print(f"User {username} Video ID: {video.id}, Description: {description}")
    except (CaptchaException, EmptyResponseException, InvalidJSONException) as e:
        print(f"Error fetching videos for user {username}: {e}")

async def get_video_info(api, video_url):
    try:
        video = api.video(url=video_url)
        video_data = await video.info()
        print(f"Video info for {video_url}: {video_data}")

        # Lưu dữ liệu video ra file JSON
        filename = f"video_{video_data['id']}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(video_data, f, ensure_ascii=False, indent=4)
        print(f"Saved video data to {filename}")

    except Exception as e:
        print(f"Error fetching video info: {e}")

async def main():
    api = TikTokApi()
    await api.create_sessions(num_sessions=1, headless=False, browser='webkit')

    print("== Trending Videos ==")
    await get_trending_videos(api, count=10)

    print("\n== Videos by Hashtag #funny ==")
    await get_videos_by_hashtag(api, "funny", count=10)

    print("\n== User Info for 'charlidamelio' ==")
    await get_user_info(api, "charlidamelio")

    print("\n== Videos by User 'charlidamelio' ==")
    await get_user_videos(api, "charlidamelio", count=5)

    print("\n== Video Info for specific video ==")
    video_url = "https://www.tiktok.com/@huyvu_i15/video/7498045626652036359"
    await get_video_info(api, video_url)

    if hasattr(api, "stop"):
        await api.stop()

if __name__ == "__main__":
    asyncio.run(main())

from TikTokApi import TikTokApi
import asyncio
import os

ms_token = os.environ.get(
    "ms_token", None
)  # set your own ms_token, needs to have done a search before for this to work


async def search_users():
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser=os.getenv("TIKTOK_BROWSER", "chromium"))
        async for user in api.search.users("huyvu_i15", count=10):
            print(user, user.user_id, user.username)
            user_info = api.get_user(sec_uid="MS4wLjABAAAAc2eF_vK-q4cNwo8X-GmUVcHhM05RVAbO7tUp5NrZWwKFk-uVDRPunofFnBtZkfNP")


if __name__ == "__main__":
    asyncio.run(search_users())
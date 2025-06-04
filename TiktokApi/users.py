import asyncio
import time
from TikTokApi import TikTokApi
from TikTokApi.exceptions import CaptchaException, EmptyResponseException, InvalidJSONException
from playwright.async_api import async_playwright

async def get_ms_token():
    """
    Lấy ms_token từ TikTok web
    """
    async with async_playwright() as p:
        # Khởi tạo browser với proxy
        browser = await p.webkit.launch(
            headless=True,
            proxy={
                "server": "http://api.yourproxy.click:5106",
                "username": "mobi5",
                "password": "Infi2132"
            }
        )
        
        try:
            # Tạo context và page
            context = await browser.new_context()
            page = await context.new_page()
            
            # Truy cập TikTok
            print("Đang truy cập TikTok để lấy ms_token...")
            await page.goto("https://www.tiktok.com/", wait_until="networkidle")
            
            # Đợi một chút để trang load hoàn toàn
            await asyncio.sleep(3)
            
            # Lấy ms_token từ localStorage hoặc cookies
            ms_token = None
            
            # Thử lấy từ localStorage trước
            try:
                ms_token = await page.evaluate("""
                    () => {
                        return localStorage.getItem('msToken') || 
                               window.msToken ||
                               document.cookie.split(';').find(row => row.startsWith(' msToken='))?.split('=')[1];
                    }
                """)
            except:
                pass
            
            # Nếu không có từ localStorage, thử lấy từ cookies
            if not ms_token:
                cookies = await context.cookies()
                for cookie in cookies:
                    if cookie['name'] == 'msToken':
                        ms_token = cookie['value']
                        break
            
            # Nếu vẫn không có, thử lấy từ network requests
            if not ms_token:
                print("Đang chờ để lấy ms_token từ network requests...")
                await asyncio.sleep(5)
                
                # Thử lại lấy từ page context
                ms_token = await page.evaluate("""
                    () => {
                        // Thử nhiều cách khác nhau để lấy ms_token
                        return window.msToken || 
                               localStorage.getItem('msToken') ||
                               sessionStorage.getItem('msToken') ||
                               document.querySelector('script')?.textContent?.match(/msToken["\']?:\s*["\']([^"\']+)/)?.[1];
                    }
                """)
            
            if ms_token:
                print(f"Đã lấy được ms_token: {ms_token[:20]}...")
                return ms_token
            else:
                print("Không thể lấy được ms_token, sẽ tiếp tục mà không có token")
                return None
                
        except Exception as e:
            print(f"Lỗi khi lấy ms_token: {e}")
            return None
        finally:
            await browser.close()

async def get_user_info(api, username):
    try:
        user = api.user(username=username)
        user_data = await user.info()
        print(f"User info for {username}:")
        print(f"ID: {user_data.get('id')}")
        print(f"Unique ID: {user_data.get('uniqueId')}")
        print(f"Nickname: {user_data.get('nickname')}")
        print(f"Signature: {user_data.get('signature')}")
        # Follower count nằm trong authorStats hoặc stats
        followers = user_data.get('followerCount') or user_data.get('authorStats', {}).get('followerCount') or user_data.get('stats', {}).get('followerCount')
        print(f"Followers: {followers}")
        following = user_data.get('followingCount') or user_data.get('authorStats', {}).get('followingCount') or user_data.get('stats', {}).get('followingCount')
        print(f"Following: {following}")
        video_count = user_data.get('videoCount') or user_data.get('authorStats', {}).get('videoCount') or user_data.get('stats', {}).get('videoCount')
        print(f"Video Count: {video_count}")
        print(f"Verified: {user_data.get('verified')}")
        print(f"Avatar URL: {user_data.get('avatarLarger')}")
    except (CaptchaException, EmptyResponseException, InvalidJSONException) as e:
        print(f"Error fetching user info for {username}: {e}")

async def main():
    # Bước 1: Lấy ms_token từ web
    print("=== Bước 1: Lấy ms_token ===")
    ms_token = await get_ms_token()
    
    # Bước 2: Khởi tạo TikTokApi với ms_token
    print("=== Bước 2: Khởi tạo TikTokApi ===")
    api = TikTokApi()
    
    # Tạo session với ms_token (nếu có)
    session_config = {
        "num_sessions": 1,
        "headless": False,
        "browser": 'chromium',
        "proxies": [{
            "server": "http://api.yourproxy.click:5106",
            "username": "mobi6",
            "password": "Infi2132"
        }],
        "sleep_after": 5,
    }
    
    # Thêm ms_token vào config nếu có
    if ms_token:
        session_config["ms_tokens"] = [ms_token]
        print("Đã thêm ms_token vào session")
    
    await api.create_sessions(**session_config)
    
    # Bước 3: Lấy thông tin user
    print("=== Bước 3: Lấy thông tin user ===")
    username = "huyvu_i15"
    await get_user_info(api, username)

    # Đóng api
    if hasattr(api, "stop"):
        await api.stop()

if __name__ == "__main__":
    asyncio.run(main())
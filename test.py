from playwright.sync_api import sync_playwright
import time
import json
import random
import requests

# Danh sách proxy
proxy_list = [
    {"server": "http://api.yourproxy.click:5108", "username": "mobi8", "password": "Infi2132"},
    {"server": "http://api.yourproxy.click:5107", "username": "mobi7", "password": "Infi2132"},
    {"server": "http://api.yourproxy.click:5106", "username": "mobi6", "password": "Infi2132"},
    {"server": "http://api.yourproxy.click:5105", "username": "mobi5", "password": "Infi2132"}
]

# API key cho SadCaptcha
API_KEY = '1fe5d8775bd1d9c0facd4363f8e466e5'
CAPTCHA_API_URL = 'https://www.sadcaptcha.com/api/v1/captcha/solve'

def solve_captcha(image_url):
    """
    Gửi CAPTCHA đến SadCaptcha API để giải quyết.
    """
    response = requests.post(CAPTCHA_API_URL, data={
        'api_key': API_KEY,
        'captcha_url': image_url  # CAPTCHA image URL từ TikTok
    })
    result = response.json()

    if result.get('status') == 'success':
        return result['solution']  # Giải pháp CAPTCHA trả về
    else:
        print("Không thể giải CAPTCHA")
        return None

def collect_user_profiles_and_info():
    with sync_playwright() as p:
        # Chọn một proxy ngẫu nhiên từ danh sách
        proxy = random.choice(proxy_list)
        
        # Mở trình duyệt với proxy
        browser = p.chromium.launch(headless=False, proxy={
            "server": proxy["server"],
            "username": proxy["username"],
            "password": proxy["password"]
        })
        page = browser.new_page()

        # Giả mạo dấu vân tay của trình duyệt
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1366, "height": 768},  # Cấu hình viewport
            locale="en-US",  # Cấu hình địa phương
            geolocation={"latitude": 40.7128, "longitude": -74.0060},  # Thiết lập vị trí giả
            permissions=["geolocation"]  # Được phép vị trí
        )

        page = context.new_page()

        # Điều hướng đến trang TikTok và thêm độ trễ để tránh bị phát hiện là bot
        page.goto("https://www.tiktok.com/")
        time.sleep(random.uniform(4, 6))  # Đợi để tránh captcha

        # Nếu bị chuyển hướng đến trang explore, quay lại trang chính TikTok
        if page.url == "https://www.tiktok.com/explore":
            page.goto("https://www.tiktok.com/")
            time.sleep(random.uniform(3, 5))

        # Cuộn trang với tốc độ chậm và thêm độ trễ ngẫu nhiên
        for _ in range(50):  # Cuộn trang 50 lần
            page.evaluate('window.scrollBy(0, window.innerHeight)')
            time.sleep(random.uniform(3, 6))  # Đợi trang tải thêm

        # Thu thập tất cả các liên kết hồ sơ người dùng
        user_links = page.query_selector_all("a[href^='/@']")
        profile_links = [link.get_attribute('href') for link in user_links]

        # Loại bỏ các liên kết trùng lặp
        profile_links = list(set(profile_links))

        all_profiles = []

        # Lần lượt truy cập vào từng hồ sơ và lấy thông tin
        for profile_url in profile_links:
            page.goto(f"https://www.tiktok.com{profile_url}")
            time.sleep(random.uniform(3, 5))  # Thêm thời gian tải trang hồ sơ

            # Kiểm tra xem có CAPTCHA không
            captcha_image_url = page.query_selector('img.captcha-image')  # Chỉ thị để xác định CAPTCHA
            if captcha_image_url:
                captcha_solution = solve_captcha(captcha_image_url.get_attribute('src'))
                if captcha_solution:
                    # Gửi giải pháp CAPTCHA nếu có
                    page.fill('input[name="captcha_solution"]', captcha_solution)
                    page.click('button[type="submit"]')

                    # Đợi một chút để TikTok xử lý CAPTCHA
                    time.sleep(random.uniform(3, 5))

            # Tiếp tục lấy thông tin sau khi giải CAPTCHA
            username = page.inner_text("h1")
            followers_count = page.inner_text("strong[data-e2e='followers-count']")
            following_count = page.inner_text("strong[data-e2e='following-count']")
            likes_count = page.inner_text("strong[data-e2e='likes-count']")

            bio_element = page.query_selector("h2[data-e2e='user-bio']")
            bio = bio_element.inner_text() if bio_element else "No bio available"

            link_element = page.query_selector("a.css-847r2g-SpanLink.eht0fek")
            link = link_element.get_attribute("href") if link_element else "No link available"

            blue_check = page.query_selector("path[fill-rule='evenodd'][clip-rule='evenodd'][d='M37.1213 15.8787...']")
            is_verified = "Yes" if blue_check else "No"

            profile_link = page.url  # Đường link của trang hồ sơ

            profile_data = {
                "username": username,
                "followers": followers_count,
                "following": following_count,
                "likes": likes_count,
                "bio": bio,
                "profile_link": profile_link,
                "external_link": link,
                "is_verified": is_verified
            }

            all_profiles.append(profile_data)

            # In ra thông tin thu thập được từ hồ sơ
            print(f"Username: {username}")
            print(f"Followers: {followers_count}")
            print(f"Following: {following_count}")
            print(f"Likes: {likes_count}")
            print(f"Bio: {bio}")
            print(f"Profile Link: {profile_link}")
            print(f"External Link: {link}")
            print(f"Verified: {is_verified}")
            print("-" * 50)

            # Lưu thông tin vào file JSON sau khi lấy được từ mỗi hồ sơ
            with open("user_profiles.json", "w", encoding="utf-8") as f:
                json.dump(all_profiles, f, ensure_ascii=False, indent=4)

        browser.close()

# Gọi hàm
collect_user_profiles_and_info()

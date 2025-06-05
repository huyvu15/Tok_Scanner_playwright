from playwright.sync_api import sync_playwright
import time
import json

def collect_user_profiles_and_info():
    with sync_playwright() as p:
        # Mở trình duyệt
        browser = p.chromium.launch(headless=False, proxy={
            "server": "http://api.yourproxy.click:5108",
            "username": "mobi8",
            "password": "Infi2132"
        })
        page = browser.new_page()

        # Điều hướng đến trang TikTok
        page.goto("https://www.tiktok.com/")

        # Đảm bảo trang đã tải xong
        time.sleep(2)

        # Cuộn trang để tải thêm nội dung (scrolling)
        for _ in range(50):  # Cuộn trang 5 lần
            page.evaluate('window.scrollBy(0, window.innerHeight)')
            time.sleep(2)  # Đợi trang tải thêm

        # Thu thập tất cả các liên kết hồ sơ người dùng (các liên kết bắt đầu bằng "/@")
        user_links = page.query_selector_all("a[href^='/@']")
        profile_links = [link.get_attribute('href') for link in user_links]

        # Loại bỏ các liên kết trùng lặp
        profile_links = list(set(profile_links))

        # Lưu thông tin vào một danh sách để ghi vào file JSON
        all_profiles = []

        # Lần lượt truy cập vào từng hồ sơ và lấy thông tin
        for profile_url in profile_links:
            # Điều hướng đến hồ sơ người dùng
            page.goto(f"https://www.tiktok.com{profile_url}")

            # Đảm bảo trang đã tải xong
            time.sleep(2)

            # Lấy thông tin từ trang hồ sơ (ví dụ: tên người dùng, số người theo dõi, số lượt thích, dòng quote, và đường link)
            username = page.inner_text("h1")
            followers_count = page.inner_text("strong[data-e2e='followers-count']")
            following_count = page.inner_text("strong[data-e2e='following-count']")
            likes_count = page.inner_text("strong[data-e2e='likes-count']")

            # Lấy phần bio (quote) từ <h2> với data-e2e="user-bio"
            bio_element = page.query_selector("h2[data-e2e='user-bio']")
            bio = bio_element.inner_text() if bio_element else "No bio available"

            # Lấy link dưới profile
            link_element = page.query_selector("a.css-847r2g-SpanLink.eht0fek")
            link = link_element.get_attribute("href") if link_element else "No link available"

            # Kiểm tra tích xanh
            blue_check = page.query_selector("path[fill-rule='evenodd'][clip-rule='evenodd'][d='M37.1213 15.8787C38.2929 17.0503 38.2929 18.9497 37.1213 20.1213L23.6213 33.6213C22.4497 34.7929 20.5503 34.7929 19.3787 33.6213L10.8787 25.1213C9.70711 23.9497 9.70711 22.0503 10.8787 20.8787C12.0503 19.7071 13.9497 19.7071 15.1213 20.8787L21.5 27.2574L32.8787 15.8787C34.0503 14.7071 35.9497 14.7071 37.1213 15.8787Z']")
            is_verified = "Yes" if blue_check else "No"

            profile_link = page.url  # Đường link của trang hồ sơ

            # Tạo một dictionary chứa thông tin hồ sơ người dùng
            profile_data = {
                "username": username,
                "followers": followers_count,
                "following": following_count,
                "likes": likes_count,
                "bio": bio,
                "profile_link": profile_link,
                "external_link": link,  # Link m.me nếu có
                "is_verified": is_verified  # Tích xanh (verified)
            }

            # Thêm thông tin vào danh sách
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

        # Đóng trình duyệt
        browser.close()

# Gọi hàm collect_user_profiles_and_info để thu thập các liên kết hồ sơ và thông tin
collect_user_profiles_and_info()

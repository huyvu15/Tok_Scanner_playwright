import asyncio
from pyppeteer import launch

async def sleep(ms):
    await asyncio.sleep(ms / 1000)

async def get_api_headers(url):
    try:
        browser = await launch(headless=True)  # Start headless browser
        page = await browser.newPage()
        print(f"Đang tải trang: {url}")
        await page.goto(url)

        # Extract headers from page using evaluate function
        def extract_headers():
            return {
                'anonymous-user-id': window.localStorage.getItem('anonymous-user-id'),
                'timestamp': window.localStorage.getItem('timestamp'),
                'user-sign': window.localStorage.getItem('user-sign')
            }

        api_headers = await page.evaluate(extract_headers)
        print(f"Đã trích xuất tiêu đề: {api_headers}")

        await browser.close()
        return api_headers
    except Exception as e:
        print(f"Đã xảy ra lỗi: {str(e)}")

async def main():
    url = 'https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pad/en'
    headers = await get_api_headers(url)
    print(f"Tiêu đề API: {headers}")

# Run the main function to get headers
asyncio.run(main())

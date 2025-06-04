import asyncio
import json
import random
import time
from datetime import datetime
from typing import List, Dict, Optional
import aiofiles
import logging
from TikTokApi import TikTokApi
from TikTokApi.exceptions import InvalidResponseException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TikTokUserCrawler:
    def __init__(self, proxies: Optional[List[str]] = None, use_proxy_rotation: bool = True):
        """
        TikTok User Crawler với proxy support
        
        Args:
            proxies: List proxy dạng ["http://user:pass@ip:port", ...]
            use_proxy_rotation: Có rotate proxy không
        """
        self.proxies = proxies or []
        self.use_proxy_rotation = use_proxy_rotation
        self.current_proxy_index = 0
        self.api = None
        
        # Rate limiting settings
        self.request_delay = (1, 3)  # Random delay 1-3 giây
        self.batch_delay = (5, 10)   # Delay giữa các batch
        self.max_retries = 3
        
    def get_current_proxy(self) -> Optional[str]:
        """Lấy proxy hiện tại"""
        if not self.proxies:
            return None
        return self.proxies[self.current_proxy_index]
    
    def rotate_proxy(self):
        """Rotate sang proxy tiếp theo"""
        if self.proxies and self.use_proxy_rotation:
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            logger.info(f"Rotated to proxy: {self.get_current_proxy()}")
    
    async def init_api(self):
        """Khởi tạo TikTok API với proxy"""
        proxy = self.get_current_proxy()
        
        try:
            self.api = TikTokApi(
                proxy=proxy,
                custom_verify_fp="verify_" + str(random.randint(100000, 999999)),
                use_test_endpoints=False
            )
            logger.info(f"API initialized with proxy: {proxy}")
        except Exception as e:
            logger.error(f"Failed to initialize API: {e}")
            raise
    
    async def close_api(self):
        """Đóng API session"""
        if self.api:
            await self.api.close_session()
    
    async def safe_request(self, func, *args, **kwargs):
        """Thực hiện request với retry và error handling"""
        for attempt in range(self.max_retries):
            try:
                # Random delay để tránh rate limit
                await asyncio.sleep(random.uniform(*self.request_delay))
                
                result = await func(*args, **kwargs)
                return result
                
            except InvalidResponseException as e:
                logger.warning(f"Invalid response (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    # Rotate proxy và retry
                    self.rotate_proxy()
                    await self.close_api()
                    await self.init_api()
                    await asyncio.sleep(random.uniform(*self.batch_delay))
                else:
                    raise e
                    
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(random.uniform(*self.batch_delay))
                else:
                    raise e

    async def get_user_info(self, username: str) -> Dict:
        """Lấy thông tin cơ bản của user"""
        await self.init_api()
        
        try:
            user = self.api.user(username=username)
            user_data = await self.safe_request(user.info)
            
            # Extract thông tin quan trọng
            info = {
                'username': user.username,
                'user_id': user.user_id,
                'sec_uid': user.sec_uid,
                'display_name': user_data.get('user', {}).get('nickname', ''),
                'bio': user_data.get('user', {}).get('signature', ''),
                'follower_count': user_data.get('stats', {}).get('followerCount', 0),
                'following_count': user_data.get('stats', {}).get('followingCount', 0),
                'likes_count': user_data.get('stats', {}).get('heartCount', 0),
                'video_count': user_data.get('stats', {}).get('videoCount', 0),
                'verified': user_data.get('user', {}).get('verified', False),
                'private_account': user_data.get('user', {}).get('privateAccount', False),
                'avatar_url': user_data.get('user', {}).get('avatarLarger', ''),
                'crawl_time': datetime.now().isoformat(),
                'raw_data': user_data
            }
            
            logger.info(f"Successfully crawled user info: {username}")
            logger.info(f"Followers: {info['follower_count']:,}, Videos: {info['video_count']:,}")
            return info
            
        finally:
            await self.close_api()
    
    async def crawl_user_videos(self, username: str, count: int = 50) -> List[Dict]:
        """Crawl videos của user"""
        await self.init_api()
        
        try:
            user = self.api.user(username=username)
            videos_data = []
            
            video_count = 0
            async for video in user.videos(count=count):
                try:
                    # Lấy thông tin video
                    video_info = {
                        'id': video.id,
                        'url': video.url,
                        'author': video.author.username if video.author else username,
                        'create_time': video.create_time.isoformat() if video.create_time else None,
                        'description': getattr(video, 'desc', ''),
                        'hashtags': [tag.name for tag in video.hashtags] if video.hashtags else [],
                        'mentions': getattr(video, 'mentions', []),
                        'stats': {
                            'views': video.stats.get('playCount', 0) if video.stats else 0,
                            'likes': video.stats.get('diggCount', 0) if video.stats else 0,
                            'comments': video.stats.get('commentCount', 0) if video.stats else 0,
                            'shares': video.stats.get('shareCount', 0) if video.stats else 0
                        },
                        'music': {
                            'id': getattr(video, 'music_id', None),
                            'title': getattr(video, 'music_title', None),
                            'author': getattr(video, 'music_author', None)
                        },
                        'video_meta': {
                            'duration': getattr(video, 'duration', None),
                            'width': getattr(video, 'width', None),
                            'height': getattr(video, 'height', None)
                        },
                        'crawl_time': datetime.now().isoformat(),
                        'raw_data': video.as_dict
                    }
                    
                    videos_data.append(video_info)
                    video_count += 1
                    
                    logger.info(f"Crawled video {video_count}/{count}: {video.id} - Views: {video_info['stats']['views']:,}")
                    
                    # Delay sau mỗi 10 videos để tránh rate limit
                    if video_count % 10 == 0:
                        await asyncio.sleep(random.uniform(*self.batch_delay))
                        
                except Exception as e:
                    logger.error(f"Error crawling video: {e}")
                    continue
            
            logger.info(f"Successfully crawled {len(videos_data)} videos for user: {username}")
            return videos_data
            
        finally:
            await self.close_api()
    
    async def crawl_user_liked_videos(self, username: str, count: int = 30) -> List[Dict]:
        """Crawl liked videos của user (chỉ có thể nếu profile public)"""
        await self.init_api()
        
        try:
            user = self.api.user(username=username)
            liked_videos = []
            
            try:
                video_count = 0
                async for video in user.liked(count=count):
                    video_info = {
                        'id': video.id,
                        'url': video.url,
                        'author': video.author.username if video.author else None,
                        'create_time': video.create_time.isoformat() if video.create_time else None,
                        'description': getattr(video, 'desc', ''),
                        'hashtags': [tag.name for tag in video.hashtags] if video.hashtags else [],
                        'stats': {
                            'views': video.stats.get('playCount', 0) if video.stats else 0,
                            'likes': video.stats.get('diggCount', 0) if video.stats else 0,
                            'comments': video.stats.get('commentCount', 0) if video.stats else 0,
                            'shares': video.stats.get('shareCount', 0) if video.stats else 0
                        },
                        'crawl_time': datetime.now().isoformat()
                    }
                    liked_videos.append(video_info)
                    video_count += 1
                    
                    logger.info(f"Crawled liked video {video_count}/{count}: {video.id}")
                    
                    await asyncio.sleep(random.uniform(*self.request_delay))
                    
            except Exception as e:
                logger.warning(f"Cannot crawl liked videos for {username} (may be private): {e}")
                return []
            
            logger.info(f"Successfully crawled {len(liked_videos)} liked videos for: {username}")
            return liked_videos
            
        finally:
            await self.close_api()
    
    async def get_user_playlists(self, username: str, count: int = 20) -> List[Dict]:
        """Lấy playlists của user"""
        await self.init_api()
        
        try:
            user = self.api.user(username=username)
            playlists = []
            
            try:
                async for playlist in user.playlists(count=count):
                    playlist_info = {
                        'id': getattr(playlist, 'id', None),
                        'title': getattr(playlist, 'title', None),
                        'description': getattr(playlist, 'desc', None),
                        'video_count': getattr(playlist, 'video_count', 0),
                        'crawl_time': datetime.now().isoformat(),
                        'raw_data': playlist.as_dict if hasattr(playlist, 'as_dict') else {}
                    }
                    playlists.append(playlist_info)
                    
                    logger.info(f"Found playlist: {playlist_info['title']}")
                    await asyncio.sleep(random.uniform(*self.request_delay))
                    
            except Exception as e:
                logger.warning(f"Cannot get playlists for {username}: {e}")
                return []
            
            logger.info(f"Successfully found {len(playlists)} playlists for: {username}")
            return playlists
            
        finally:
            await self.close_api()
    
    async def crawl_complete_user_data(self, username: str, 
                                     include_videos: bool = True,
                                     include_liked: bool = True,
                                     include_playlists: bool = True,
                                     video_count: int = 50,
                                     liked_count: int = 30) -> Dict:
        """Crawl toàn bộ thông tin user"""
        logger.info(f"Starting complete crawl for user: {username}")
        
        complete_data = {
            'username': username,
            'crawl_timestamp': datetime.now().isoformat(),
            'user_info': {},
            'videos': [],
            'liked_videos': [],
            'playlists': []
        }
        
        try:
            # 1. Lấy thông tin cơ bản
            logger.info("=== Getting user basic info ===")
            complete_data['user_info'] = await self.get_user_info(username)
            
            # 2. Lấy videos nếu được yêu cầu
            if include_videos:
                logger.info(f"=== Getting user videos (count: {video_count}) ===")
                complete_data['videos'] = await self.crawl_user_videos(username, video_count)
            
            # 3. Lấy liked videos nếu được yêu cầu
            if include_liked:
                logger.info(f"=== Getting liked videos (count: {liked_count}) ===")
                complete_data['liked_videos'] = await self.crawl_user_liked_videos(username, liked_count)
            
            # 4. Lấy playlists nếu được yêu cầu
            if include_playlists:
                logger.info("=== Getting user playlists ===")
                complete_data['playlists'] = await self.get_user_playlists(username)
            
            # Summary
            logger.info("=== CRAWL SUMMARY ===")
            logger.info(f"User: {complete_data['user_info'].get('display_name', username)}")
            logger.info(f"Followers: {complete_data['user_info'].get('follower_count', 0):,}")
            logger.info(f"Videos crawled: {len(complete_data['videos'])}")
            logger.info(f"Liked videos crawled: {len(complete_data['liked_videos'])}")
            logger.info(f"Playlists found: {len(complete_data['playlists'])}")
            
            return complete_data
            
        except Exception as e:
            logger.error(f"Complete user crawl failed: {e}")
            raise
    
    async def save_data(self, data: Dict, filename: str = None):
        """Lưu data ra file JSON"""
        if not filename:
            username = data.get('username', 'unknown')
            timestamp = int(time.time())
            filename = f"tiktok_user_{username}_{timestamp}.json"
        
        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        
        logger.info(f"Data saved to: {filename}")
        return filename


# ========================= USAGE EXAMPLES =========================

async def crawl_single_user_info():
    """Ví dụ crawl thông tin cơ bản 1 user"""
    
    # Khởi tạo crawler (không dùng proxy)
    crawler = TikTokUserCrawler()
    
    try:
        # Crawl thông tin user
        user_info = await crawler.get_user_info("therock")
        print(json.dumps(user_info, indent=2, ensure_ascii=False, default=str))
        
    except Exception as e:
        logger.error(f"Error: {e}")

async def crawl_user_with_proxy():
    """Ví dụ crawl với proxy"""
    
    # Danh sách proxy (thay thế bằng proxy thật)
    proxies = [
        "http://username:password@proxy1.com:8080",
        "http://username:password@proxy2.com:8080",
        "http://username:password@proxy3.com:8080"
    ]
    
    # Khởi tạo crawler với proxy
    crawler = TikTokUserCrawler(proxies=proxies, use_proxy_rotation=True)
    
    try:
        # Crawl toàn bộ thông tin user
        complete_data = await crawler.crawl_complete_user_data(
            username="davidteathercodes",
            include_videos=True,
            include_liked=True,
            include_playlists=True,
            video_count=30,
            liked_count=20
        )
        
        # Lưu data
        filename = await crawler.save_data(complete_data)
        print(f"Complete data saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error: {e}")

async def crawl_multiple_users():
    """Ví dụ crawl nhiều users"""
    
    usernames = ["huyvu_i15"]#, "willsmith", "selenagomez"]
    
    # Proxy list (optional)
    proxies = [
        "http://mobi8:Infi2132@api.yourproxy.click:5108"
    ]
    
    crawler = TikTokUserCrawler(proxies=proxies)
    
    all_users_data = []
    
    for username in usernames:
        try:
            logger.info(f"Crawling user: {username}")
            
            user_data = await crawler.crawl_complete_user_data(
                username=username,
                include_videos=True,
                include_liked=False,  # Skip liked videos để nhanh hơn
                include_playlists=False,
                video_count=20
            )
            
            all_users_data.append(user_data)
            
            # Delay giữa các users
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Failed to crawl {username}: {e}")
            continue
    
    # Lưu tất cả data
    final_data = {
        'crawl_timestamp': datetime.now().isoformat(),
        'total_users': len(all_users_data),
        'users': all_users_data
    }
    
    filename = f"multiple_users_crawl_{int(time.time())}.json"
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(final_data, ensure_ascii=False, indent=2, default=str))
    
    logger.info(f"All users data saved to: {filename}")

# ========================= MAIN EXECUTION =========================

if __name__ == "__main__":
    # Chọn một trong các ví dụ để chạy:
    
    # 1. Crawl thông tin cơ bản 1 user (không proxy)
    # asyncio.run(crawl_single_user_info())
    
    # 2. Crawl đầy đủ 1 user với proxy
    # asyncio.run(crawl_user_with_proxy())
    
    # 3. Crawl nhiều users
    asyncio.run(crawl_multiple_users())
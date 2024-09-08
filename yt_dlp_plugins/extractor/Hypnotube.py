import re
from bs4 import BeautifulSoup
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import (
    ExtractorError,
    urlencode_postdata
)
from yt_dlp.extractor import generic
from urllib.parse import urlparse, urlunparse


class HypnotubeBaseIE(InfoExtractor):
    _VALID_URL = "None"  # Workaround for error: TypeError: first argument must be string or compiled pattern
    _LOGIN_URL = 'https://hypnotube.com/login'
    _NETRC_MACHINE = 'hypnotube'

    def _perform_login(self, username, password):
        login_form = {
            'ahd_username': username,
            'ahd_password': password,
            'Submit': ''
        }

        login_response = self._download_webpage(
            self._LOGIN_URL, None,
            note='Logging in',
            data=urlencode_postdata(login_form))

        if re.search(r'<div class="notification error">The login information you have provided was incorrect', login_response, re.IGNORECASE):
            raise ExtractorError('Login failed: incorrect username or password', expected=True)

        self._detect_logged_in_user(login_response)

    def _detect_logged_in_user(self, webpage):
        soup = BeautifulSoup(webpage, 'html.parser')
        user_name_elem = soup.find('span', class_='name_normal user-name') or soup.find('span', 'name_premium user-name')

        if user_name_elem:
            logged_in_user = user_name_elem.get_text(strip=True)
            self.to_screen(f"Logged in as: {logged_in_user}")
        else:
            raise ExtractorError('Login failed', expected=False)

    def _handle_login(self):
        username, password = self._get_login_info()
        if username and password:
            self._perform_login(username, password)

    def _extract_uploader_info(self, soup):
        uploader_elem = soup.find("a", href=re.compile(r'https?://hypnotube\.com/user/.*-(?P<id>\d+)/'))
        uploader_id, uploader_url, uploader_name = None, None, "Anonymous"

        if uploader_elem:
            uploader_id_match = re.search(r'https?://hypnotube\.com/user/.*-(?P<id>\d+)/', uploader_elem['href'])
            uploader_id = uploader_id_match.group('id') if uploader_id_match else None
            uploader_url = uploader_elem['href']
            uploader_name = uploader_elem.get_text(strip=True).replace("Submitted by", "").strip()

        return uploader_id, uploader_name, uploader_url

    def _extract_comments(self, item_id):
        comments_url = f'https://hypnotube.com/templates/hypnotube/template.ajax_comments.php?id={item_id}'
        comments_webpage = self._download_webpage(comments_url, item_id, note='Downloading comments page')
        soup = BeautifulSoup(comments_webpage, 'html.parser')
        comments = []

        for comment_block in soup.find_all('div', class_='block'):
            # Extract author name
            author = comment_block.find('strong').get_text(strip=True)

            # Extract author link and associated details
            author_link = comment_block.find_previous_sibling('a')
            author_thumbnail = author_link.find('img')['src'] if author_link and author_link.find('img') else None
            author_url = author_link['href'] if author_link and 'href' in author_link.attrs else None
            author_id_match = re.search(r'user/([a-zA-Z0-9_-]+)-(\d+)/', author_url) if author_url else None
            author_id = author_id_match.group(2) if author_id_match else None

            # Correctly determine if the user is VIP or normal based on the class of the <a> tag
            author_a_tag = comment_block.find('a', href=True)
            author_membership = ''  # default to NOTHING
            if author_a_tag:
                if 'name_premium' in author_a_tag.get('class', []):
                    author_membership = 'VIP'
                elif 'name_normal' in author_a_tag.get('class', []):
                    author_membership = 'normal'

            # Extract comment time text
            time_element = comment_block.find('a')
            _time_text = None
            if time_element:
                time_text_block = time_element.find_next_sibling(string=True)
                _time_text = time_text_block.strip() if time_text_block else None

            # Extract comment text
            text = comment_block.find('p').get_text(strip=True)

            # Append all data to the comments list
            comments.append({
                'author': author,
                'author_id': author_id,
                'author_thumbnail': author_thumbnail,
                'author_url': author_url,
                'author_membership': author_membership,
                '_time_text': _time_text,
                'text': text,
            })

        return comments




    def _extract_video_stats(self, soup):
        stats = soup.find("div", class_="stats-container").find_all("li")
        
        # Extract duration safely
        duration_str = stats[0].find("span", class_="sub-label").get_text(strip=True) if len(stats) > 0 else None
        duration = None
        if duration_str:
            duration_parts = duration_str.split(':')
            if len(duration_parts) == 3:  # HH:MM:SS format
                duration = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])
            elif len(duration_parts) == 2:  # MM:SS format
                duration = int(duration_parts[0]) * 60 + int(duration_parts[1])
        
        # Extract view count safely
        view_count = int(stats[1].find("span", class_="sub-label").get_text(strip=True)) if len(stats) > 1 else None
        
        # Extract upload date safely
        upload_date = stats[2].find("span", class_="sub-label").get_text(strip=True).replace("-", "").replace(":", "").replace(" ", "")[:8] if len(stats) > 2 else None

        return duration, view_count, upload_date


    def _extract_title(self, soup):
        title_elem = soup.find('h1')
        if title_elem and title_elem.get_text(strip=True):
            return title_elem.get_text(strip=True)
        # Fallback to use a default title if h1 is empty or missing
        return 'Untitled'


    def _extract_description(self, soup):
        description_elem = soup.find('div', class_="main-description")
        return description_elem.get_text(strip=True) if description_elem else None

    def _extract_thumbnail(self, soup):
        thumbnail_elem = soup.find("meta", property="og:image")
        return thumbnail_elem['content'] if thumbnail_elem else None


class HypnotubeVideoIE(HypnotubeBaseIE):
    IE_NAME = 'HypnotubeCom:Video_Plugin'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/video/(?:.*-)?(?P<id>\d+)\.html'

    def _real_extract(self, url):
        self._handle_login()

        video_id_match = re.search(self._VALID_URL, url)
        video_id = video_id_match.group('id')
        webpage = self._download_webpage(url, video_id)
        soup = BeautifulSoup(webpage, 'html.parser')

        uploader_id, uploader_name, uploader_url = self._extract_uploader_info(soup)
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        duration, view_count, upload_date = self._extract_video_stats(soup)
        formats = self._extract_formats(webpage, url)
        thumbnail = self._extract_thumbnail(soup)
        comments = self._extract_comments(video_id)

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader_name,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'comments': comments
        }

    def _extract_formats(self, webpage, url):
        soup = BeautifulSoup(webpage, 'html.parser')
        video_elem = soup.find('video', id='thisPlayer')

        if not video_elem:
            notice_elem = soup.find(id='notice_overl') or soup.find(id='playerOverlay')
            if notice_elem:
                notice_text = notice_elem.get_text(strip=True)
                raise ExtractorError(f"Video cannot be accessed, HypnoTube says: {notice_text}", expected=True)
            raise ExtractorError(f"Could not find video element on the page: {url}")

        formats = []
        for source in video_elem.find_all('source'):
            format_url = source.get('src')
            format_label = source.get('label')
            if not format_url or not format_label:
                continue

            preference = -10 if format_label.lower() == 'sd' else 0
            formats.append({
                'url': format_url,
                'format_id': format_label,
                'ext': 'mp4',
                'preference': preference,
                'http_headers': {'Referer': 'https://hypnotube.com/index.php'}
            })
        
        if not formats:
            raise ExtractorError(f"Could not extract video formats, the video might be private or restricted: {url}")
        
        return formats




class HypnotubePlaylistIE(HypnotubeBaseIE):
    IE_NAME = 'HypnotubeCom:Playlist'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/playlist/(?P<id>\d+)/(?P<slug>[^/]+)(?:/page(?P<page>\d+)\.html)?/?'

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        playlist_id = mobj.group('id')
        slug = mobj.group('slug')
        playlist_title = None
        entries = []

        page_num = 1
        while True:
            if (page_num == 1):
                page_url = url
            else:
                page_url = f'https://hypnotube.com/playlist/{playlist_id}/{slug}/page{page_num}.html'
            
            webpage, handle = self._download_webpage_handle(page_url, playlist_id, note=f'Downloading page {page_num}', fatal=False)
            if webpage is None:  # Handle invalid page
                break

            # Check if the final URL after redirects is different from the original URL
            if handle.url != page_url:
                self.report_warning(f'Playlist {playlist_id} appears to be invalid, redirected to a different page.')
                break
            
            soup = BeautifulSoup(webpage, 'html.parser')
            
            if not playlist_title:  # Only get the title from the first page
                playlist_title_elem = soup.find('h1')
                playlist_title = playlist_title_elem.get_text(strip=True) if playlist_title_elem else f'Playlist {playlist_id}'

            new_entries = list(self._entries(soup))
            if not new_entries:
                break
            entries.extend(new_entries)
            page_num += 1

        return self.playlist_result(entries, playlist_id, playlist_title)

    def _entries(self, soup):
        for a in soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/video/.+-(\d+)\.html')):
            video_url = a['href']
            parsed_url = urlparse(video_url)
            video_url_without_params = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
            video_id_match = re.search(r'.+-(\d+)\.html', video_url_without_params)
            if video_id_match:
                video_id = video_id_match.group(1)
                yield self.url_result(video_url_without_params, ie_key=HypnotubeVideoIE.ie_key())

class HypnotubeFavoritesIE(HypnotubeBaseIE):
    IE_NAME = 'HypnotubeCom:Favorites'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/favorites/(?:page(?P<page_num>\d+))?'

    def _get_user_info(self):
        profile_url = 'https://hypnotube.com/my-profile'
        profile_page = self._download_webpage(profile_url, None, note='Downloading user profile page')
        soup = BeautifulSoup(profile_page, 'html.parser')

        # Extract the logged-in username
        username_elem = soup.find('li', class_='profile-field-username')
        logged_in_username = username_elem.find('span', class_='sub-desc').get_text(strip=True) if username_elem else 'Unknown'

        return logged_in_username

    def _entries(self, user_id):
        page_num = 1
        video_count = 0
        while True:
            favorites_url = f'https://hypnotube.com/favorites/page{page_num}.html'
            webpage = self._download_webpage(favorites_url, user_id, note=f'Downloading favorites page {page_num}')
            soup = BeautifulSoup(webpage, 'html.parser')

            # Extract video links
            video_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/video/.+-(?P<id>\d+)\.html'))
            # Extract gallery links
            gallery_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/galleries/.+-(?P<id>\d+)\.html'))

            if not video_links and not gallery_links:
                if video_count == 0:
                    self.report_warning("No videos or galleries found on the favorites page. Possible login or cookie issues.")
                break

            for link in gallery_links:
                video_count += 1
                gallery_url = link['href']
                yield self.url_result(gallery_url, ie=HypnotubeGalleryIE.ie_key())

            for link in video_links:
                video_count += 1
                video_url = link['href']
                yield self.url_result(video_url, ie=HypnotubeVideoIE.ie_key())

            page_num += 1

    def _real_extract(self, url):
        self._handle_login()

        mobj = re.match(self._VALID_URL, url)
        user_id = 'favorite'
        logged_in_username = self._get_user_info()  # Get logged-in username from the profile page
        entries = self._entries(user_id)
        return self.playlist_result(entries, playlist_id=user_id, playlist_title=f"{logged_in_username} - Favorites")

        return self.playlist_result(entries, playlist_id=user_id, playlist_title=f"{logged_in_username} - Favorites")



class HypnotubeUserIE(HypnotubeBaseIE):
    IE_NAME = 'HypnotubeCom:User_Plugin'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/(?:user/.+-(?P<id>\d+)|uploads-by-user/(?P<id1>\d+)(?:/page\d+\.html)?(?:\?photos=1)?)'

    def _entries(self, user_id, content_type):
        page_num = 1
        item_count = 0
        while True:
            if content_type == '?photos=1':
                user_url = f'https://hypnotube.com/uploads-by-user/{user_id}/page{page_num}.html{content_type}'
            else:
                user_url = f'https://hypnotube.com/uploads-by-user/{user_id}/page{page_num}.html'

            webpage = self._download_webpage(user_url, user_id, note=f'Downloading user page {page_num} ({content_type})')
            soup = BeautifulSoup(webpage, 'html.parser')

            if content_type == '?photos=1':
                item_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/galleries/.+-(?P<id>\d+)\.html'))
            else:
                item_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/video/.+-(?P<id>\d+)\.html'))

            if not item_links:
                if item_count == 0:
                    pass
                break

            for link in item_links:
                item_count += 1
                item_url = link['href']
                ie_key = HypnotubeGalleryIE.ie_key() if content_type == '?photos=1' else HypnotubeVideoIE.ie_key()
                yield self.url_result(item_url, ie_key=ie_key)

            page_num += 1

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('id') or mobj.group('id1')

        if '?photos=1' in url:
            entries = self._entries(user_id, content_type='?photos=1')
            return self.playlist_result(entries, user_id)
        
        elif 'uploads-by-user' in url:
            entries = self._entries(user_id, content_type='')
            return self.playlist_result(entries, user_id)

        else:
            # First extract photos
            photo_entries = list(self._entries(user_id, content_type='?photos=1'))
            # Then extract videos
            video_entries = list(self._entries(user_id, content_type=''))

            # Combine both photo and video entries
            entries = photo_entries + video_entries
            return self.playlist_result(entries, user_id)


class HypnotubeChannelsIE(HypnotubeBaseIE):
    IE_NAME = 'HypnotubeCom:Channels_Plugin'
    _VALID_URL = r'https?:\/\/(?:www\.)?hypnotube\.com\/channels\/(?P<id>\d+)\/(?P<name>[^\/]+)(?:\/page(?P<page>\d+)\.html)?\/?'

    def _entries(self, channel_id, channel_name):
        page_num = 1
        video_count = 0
        while True:
            channel_url = f'https://hypnotube.com/channels/{channel_id}/{channel_name}/page{page_num}.html'
            webpage = self._download_webpage(channel_url, channel_id, note=f'Downloading channel page {page_num}')
            soup = BeautifulSoup(webpage, 'html.parser')

            video_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/video/.+-(?P<id>\d+)\.html'))

            if not video_links:
                if video_count == 0:
                    pass
                else:
                    pass
                break

            for link in video_links:
                video_count += 1
                video_url = link['href']
                yield self.url_result(video_url, ie=HypnotubeVideoIE.ie_key())

            page_num += 1

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id = mobj.group('id')
        channel_name = mobj.group('name')
        entries = self._entries(channel_id, channel_name)
        return self.playlist_result(entries)



class HypnotubeGalleryIE(HypnotubeBaseIE):
    IE_NAME = 'HypnotubeCom:Gallery'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/galleries/.+-(?P<id>\d+)\.html'

    def _real_extract(self, url):
        gallery_id = self._match_id(url)

        # Modify the URL to include the 'image' parameter
        if '?image=' in url:
            url = re.sub(r'\?image=\d+', '?image=1', url)
        else:
            url = f'{url}?image=1'

        webpage = self._download_webpage(url, gallery_id)
        soup = BeautifulSoup(webpage, 'html.parser')

        # Handle access restriction errors
        access_error = soup.find('div', class_='notification alert')
        if access_error:
            error_message = access_error.get_text(strip=True).replace("Click here to view their profile", "").strip()
            raise ExtractorError(f'Access restricted: {error_message}', expected=True)

        # Extract common metadata using base class methods
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        uploader_id, uploader_name, uploader_url = self._extract_uploader_info(soup)

        # Use the base method to extract video stats (view count and upload date)
        duration, view_count, upload_date = self._extract_video_stats(soup)

        # Extract the image URLs from the JavaScript 'images.push'
        image_urls = re.findall(r"images\.push\('(https?://[^\']+)'", webpage)

        # Shared metadata for both the playlist and individual entries
        common_metadata = {
            'media_type': "Gallery",
            'HYPNOTUBE_gallery': "Gallery",
            'HYPNOTUBE_gallery_id': gallery_id,
            'HYPNOTUBE_gallery_title': title,
            'uploader': uploader_name,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
            'upload_date': upload_date,
            'view_count': view_count,
        }

        # Build playlist entries for each image
        entries = [
            {
                'id': f'{gallery_id}_{idx}',
                'title': title,
                'url': img_url,
                'format_id': img_url.split('.')[-1].split('?')[0],
                'ext': img_url.split('.')[-1].split('?')[0],
                **common_metadata,  # Include common metadata in each entry
            }
            for idx, img_url in enumerate(image_urls, 1)
        ]

        # Extract comments using the base class method
        comments = self._extract_comments(gallery_id)

        # Return the images as a playlist with additional metadata
        return {
            '_type': 'playlist',
            'id': gallery_id,
            'title': title,
            'description': description,
            'comments': comments,
            'entries': entries,
            **common_metadata,  # Include common metadata at the playlist level
        }

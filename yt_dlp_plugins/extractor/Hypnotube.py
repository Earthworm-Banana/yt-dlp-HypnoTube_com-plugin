from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.compat import compat_str
from yt_dlp.extractor import generic
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urlunparse

class HypnotubeVideoIE(InfoExtractor):
    IE_NAME = 'HypnotubeCom:Video_Plugin'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/video/.+-(?P<id>\d+)\.html'

    def _real_extract(self, url):
        video_id_match = re.search(self._VALID_URL, url)
        video_id = video_id_match.group('id')
        return self._extract_video_info(video_id, url)

    def _extract_video_info(self, video_id, url):
        webpage = self._download_webpage(url, video_id)
        soup = BeautifulSoup(webpage, 'html.parser')

        uploader_id, uploader_name, uploader_url = self._extract_uploader_info(soup)
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        duration, view_count, upload_date = self._extract_video_stats(soup)
        formats = self._extract_formats(url)
        thumbnail = self._extract_thumbnail(soup)
        comments = self._extract_comments(video_id)

        info = {
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

        return info

    def _extract_thumbnail(self, soup):
        thumbnail_elem = soup.find("meta", property="og:image")
        return thumbnail_elem['content'] if thumbnail_elem else None

    def _extract_uploader_info(self, soup):
        uploader_id = None
        uploader_url = None
        uploader_name = None

        uploader_elem = soup.find("a", href=re.compile(r'https?://hypnotube\.com/user/.*-(?P<id>\d+)/'))
        if uploader_elem:
            uploader_id_match = re.search(r'https?://hypnotube\.com/user/.*-(?P<id>\d+)/', uploader_elem['href'])
            uploader_id = uploader_id_match.group('id') if uploader_id_match else None
            uploader_url = uploader_elem['href']
            uploader_name = uploader_elem.get_text(strip=True).replace("Submitted by", "").strip()

        return uploader_id, uploader_name, uploader_url

    def _extract_title(self, soup):
        title_elem = soup.find("h1")
        return title_elem.get_text(strip=True) if title_elem else None

    def _extract_description(self, soup):
        description_elem = soup.find("div", class_="main-description")
        return description_elem.get_text(strip=True) if description_elem else None

    def _extract_video_stats(self, soup):
        stats = soup.find("div", class_="stats-container").find_all("li")
        duration_str = stats[0].find("span", class_="sub-label").get_text(strip=True)
        duration_parts = duration_str.split(':')
        if len(duration_parts) == 3:  # Check if duration includes hours
            duration = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])
        else:
            duration = int(duration_parts[0]) * 60 + int(duration_parts[1])
        view_count = int(stats[1].find("span", class_="sub-label").get_text(strip=True))
        upload_date = stats[2].find("span", class_="sub-label").get_text(strip=True).replace("-", "").replace(":", "").replace(" ", "")[:8]
        return duration, view_count, upload_date

    def _extract_formats(self, url):
        generic_extractor = generic.GenericIE()
        generic_extractor.set_downloader(self._downloader)
        return generic_extractor.extract(url)['formats']

    def _extract_comments(self, video_id):
        comments_url = f'https://hypnotube.com/templates/hypnotube/template.ajax_comments.php?id={video_id}'
        comments_webpage = self._download_webpage(comments_url, video_id, note='Downloading comments page')
        soup = BeautifulSoup(comments_webpage, 'html.parser')
        comments = []

        for comment_block in soup.find_all('div', class_='block'):
            author = comment_block.find('strong').get_text(strip=True)

            author_link = comment_block.find_previous_sibling('a')
            if author_link is not None:
                author_thumbnail = author_link.find('img')
                if author_thumbnail is not None:
                    author_thumbnail = author_thumbnail['src']
                else:
                    author_thumbnail = None
                author_url = author_link['href']
                author_id_match = re.search(r'user/([a-zA-Z0-9_-]+)-(\d+)/', author_url)
                if author_id_match:
                    author_id = author_id_match.group(2)
                else:
                    author_id = None
            else:
                author_thumbnail = author_url = author_id = None

            a_tag = comment_block.find('a')
            if a_tag is not None:
                time_text_block = a_tag.find_next_sibling(string=True)
                _time_text = time_text_block.strip() if time_text_block else None
            else:
                _time_text = None

            text = comment_block.find('p').get_text(strip=True)
            comments.append({
                'author': author,
                'author_id': author_id,
                'author_thumbnail': author_thumbnail,
                'author_url': author_url,
                '_time_text': _time_text,
                'text': text,
            })
        return comments

    def _extract_user_videos(self, user_id, user_url):
        webpage = self._download_webpage(user_url, user_id)
        soup = BeautifulSoup(webpage, 'html.parser')

        video_links = soup.find_all('a', href=re.compile(self._VALID_URL))

        entries = []
        for link in video_links:
            video_url = link['href']
            entries.append(self.url_result(video_url, 'HypnotubeVideoIE'))

        # Check for pagination
        pagination_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/uploads-by-user/.*?/page(\d+)\.html'))
        if pagination_links:
            last_page = int(pagination_links[-1]['href'].split('/')[-1].split('.')[0][4:])
            page_urls = [re.sub(r'(page)\d+', fr'\g<1>{page}', user_url) for page in range(2, last_page + 1)]
            for page_url in page_urls:
                page_webpage = self._download_webpage(page_url, user_id)
                page_soup = BeautifulSoup(page_webpage, 'html.parser')
                page_video_links = page_soup.find_all('a', href=re.compile(self._VALID_URL))
                for link in page_video_links:
                    video_url = link['href']
                    entries.append(self.url_result(video_url, 'HypnotubeVideoIE'))

        return self.playlist_result(entries, user_id)

class HypnotubePlaylistIE(InfoExtractor):
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

class HypnotubeFavoritesIE(InfoExtractor):
    IE_NAME = 'HypnotubeCom:Favorites'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/favorites/(?:page(?P<page_num>\d+))?'

    def _entries(self, user_id):
        page_num = 1
        video_count = 0
        while True:
            favorites_url = f'https://hypnotube.com/favorites/page{page_num}.html'
            webpage = self._download_webpage(favorites_url, user_id, note=f'Downloading favorites page {page_num}')
            soup = BeautifulSoup(webpage, 'html.parser')

            video_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/video/.+-(?P<id>\d+)\.html'))
            if not video_links:
                if video_count == 0:
                    self.report_warning(
                        "No videos found on the favorites page. This could be due to several reasons: "
                        "1. You may need to log in using a valid cookie file. "
                        "2. Your cookie may have expired. "
                        "3. There may genuinely be no videos in your favorites. "
                        "4. There could be a bug with the page or extractor.")
                break

            for link in video_links:
                video_count += 1
                video_url = link['href']
                yield self.url_result(video_url, ie=HypnotubeVideoIE.ie_key())

            page_num += 1

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = 'favorite'  # Not specific to a user, but a generic session-based favorites.
        if not mobj:
            raise ExtractorError('Could not extract user or page number from URL', expected=True)
        
        entries = self._entries(user_id)
        return self.playlist_result(entries, playlist_id=user_id, playlist_title="User Favorites")

class HypnotubeUserIE(InfoExtractor):
    IE_NAME = 'HypnotubeCom:User_Plugin'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/(?:user/.+-(?P<id>\d+)|uploads-by-user/(?P<id1>\d+)(?:/page\d+\.html)?)'

    def _entries(self, user_id):
        page_num = 1
        video_count = 0
        while True:
            user_url = f'https://hypnotube.com/uploads-by-user/{user_id}/page{page_num}.html'
            webpage = self._download_webpage(user_url, user_id, note=f'Downloading user page {page_num}')
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
        user_id = mobj.group('id') or mobj.group('id1')
        entries = self._entries(user_id)
        return self.playlist_result(entries, user_id)

class HypnotubeChannelsIE(InfoExtractor):
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

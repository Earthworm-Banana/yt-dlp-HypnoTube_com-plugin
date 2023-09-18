from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.compat import compat_str
from bs4 import BeautifulSoup
import re
#from rich import print

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
        formats = self._extract_formats(webpage, url)
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
            uploader_url = uploader_elem['href'] if uploader_elem else None
            uploader_name = uploader_elem.get_text(strip=True).replace("Submitted by", "").strip() if uploader_elem else None

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

    def _extract_formats(self, webpage, url):
        matches = re.findall(r'"(https?://[^"]+\.(?:mov|avi|flv|wmv|mkv|avi|mkv|flv|wmv|mpg|mpeg|m4v|3gp|webm|mp2|m2v|mpeg4|f4v|mp4))"', webpage)
        if not matches:
            raise ValueError(f"Could not extract video, might be private: {url}")
        formats = []
        for i, match in enumerate(matches):
            format_id = "HD" if i == 0 else "SD"
            formats.append({
                'url': match,
                'format_id': format_id,
                'ext': 'mp4',
                'preference': -1 if i == 0 else -10
            })
        return formats

    def _extract_comments(self, video_id):
        comments_url = f'https://hypnotube.com/templates/hypnotube/template.ajax_comments.php?id={video_id}'
        comments_webpage = self._download_webpage(comments_url, video_id, note='Downloading comments page')
        soup = BeautifulSoup(comments_webpage, 'html.parser')
        comments = []

        for comment_block in soup.find_all('div', class_='block'):
            author = comment_block.find('strong').get_text(strip=True)

            # Extracting author_thumbnail, author_id, and author_url
            author_link = comment_block.find_previous_sibling('a')
            author_thumbnail = author_link.find('img')['src']
            author_url = author_link['href']
            author_id_match = re.search(r'user/([a-zA-Z0-9_-]+)-(\d+)/', author_url)
            if author_id_match:
                author_id = author_id_match.group(2)
            else:
                author_id = None

            # Extracting _time_text
            time_text_block = comment_block.find('a').find_next_sibling(string=True)
            if time_text_block:
                _time_text = time_text_block.strip()
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




class HypnotubeUserIE(InfoExtractor):
    IE_NAME = 'HypnotubeCom:User_Plugin'
    _VALID_URL = r'https?://(?:www\.)?hypnotube\.com/(?:user/.+-(?P<id>\d+)|uploads-by-user/(?P<id1>\d+)(?:/page\d+\.html)?)'

    def _entries(self, user_id):
        page_num = 1
        video_count = 0
        while True:
            user_url = f'https://hypnotube.com/uploads-by-user/{user_id}/page{page_num}.html'
            #print(f"Checking {user_url}")
            webpage = self._download_webpage(user_url, user_id, note=f'Downloading user page {page_num}')
            soup = BeautifulSoup(webpage, 'html.parser')

            video_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/video/.+-(?P<id>\d+)\.html'))

            if not video_links:
                if video_count == 0:
                    #print(f"[red]No videos found[/red]")
                    pass
                else:
                    #print(f"[green]Found {video_count} videos[/green]")
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
    # example: https://hypnotube.com/channels/38/hd/
    # example: https://hypnotube.com/channels/38/hd/page1.html
    IE_NAME = 'HypnotubeCom:Channels_Plugin'
    _VALID_URL = r'https?:\/\/(?:www\.)?hypnotube\.com\/channels\/(?P<id>\d+)\/(?P<name>[^\/]+)(?:\/page(?P<page>\d+)\.html)?\/?'

    def _entries(self, channel_id, channel_name):
        page_num = 1
        video_count = 0
        while True:
            channel_url = f'https://hypnotube.com/channels/{channel_id}/{channel_name}/page{page_num}.html'
            #print(f"Checking {channel_url}")
            webpage = self._download_webpage(channel_url, channel_id, note=f'Downloading channel page {page_num}')
            soup = BeautifulSoup(webpage, 'html.parser')

            video_links = soup.find_all('a', href=re.compile(r'https?://(?:www\.)?hypnotube\.com/video/.+-(?P<id>\d+)\.html'))

            if not video_links:
                if video_count == 0:
                    #print(f"[red]No videos found[/red]")
                    pass
                else:
                    #print(f"[green]Found {video_count} videos[/green]")
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

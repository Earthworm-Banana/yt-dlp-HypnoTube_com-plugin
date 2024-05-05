# HypnoTube.com YT-DLP Plugin 🛠️

## Introduction 📚

Welcome to the HypnoTube.com YT-DLP Plugin, a specialized tool for augmenting your video downloading experience from HypnoTube.com. This plugin allows you to efficiently fetch individual videos, complete user uploads, entire channels, or even full playlists using yt-dlp.

> 📝 **Note**: This plugin and README were largely assisted by OpenAI’s GPT-4 model.

## Features 🌟

- **Individual Video Downloads** 🎥: Directly download HypnoTube videos to your machine.
- **User Uploads** 👤: Download all videos from a specific HypnoTube user.
- **Channel (Categories) Downloads** 📺: Extract an entire set of videos from a HypnoTube channel (Categories).
- **Playlist Downloads** 📋: Retrieve all videos from a specified HypnoTube playlist.

## Installation Guide for Windows 11 🖥️

> ⚠️ **Note**: These installation steps are specifically for Windows 11 and have been tested solely on this platform.

1. Open the Command Prompt (`cmd`).
2. Navigate to your yt-dlp plugins directory:

```bash
cd C:\Users\%username%\AppData\Roaming\yt-dlp\plugins
```

3. Clone the plugin repository:

```bash
git clone https://github.com/Earthworm-Banana/yt-dlp-HypnoTube_com-plugin.git
```

## Pip Install Method (Tested on a-Shell iOS App) 📱

> ⚠️ **Note**: This pip install method has only been tested on the “a-Shell” iOS terminal app.

1. Open your terminal or command line application.
2. Install the plugin by running:

```bash
python3 -m pip install -U https://github.com/Earthworm-Banana/yt-dlp-HypnoTube_com-plugin/archive/refs/heads/master.zip
```

> 📘 **Note**: This pip install method should work on any system that has yt-dlp installed via pip.

> For other methods of installing this plugin package, consult [installing yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins).

## Usage Guidelines 📋

### Commands 📜

- **Individual Video Download** 🎥:

```bash
yt-dlp “https://hypnotube.com/video/shock-409.html”
```

- **User Uploads Download** 👤:

```bash
yt-dlp “https://hypnotube.com/user/ambersis-3082/“
```

- **Channel Download** 📺:

```bash
yt-dlp “https://hypnotube.com/channels/38/hd/“
```

- **Playlist Download** 📋:

```bash
yt-dlp “https://hypnotube.com/playlist/93707/stim-gooning/”
```

### 🔍 Metadata Extraction

The plugin extracts various types of metadata, including:

- 📝 Video Title
- 🆔 Video ID
- 🗓️ Release Date
- 👤 Uploader
- 👁️ View Count
- ⏰ Video Duration
- 🖼️ Thumbnails

To retrieve thumbnails, use:

```bash
yt-dlp —add-headers “Referer: https://hypnotube.com” [URL]
```

Also, use either `—embed-thumbnails` (recommended) or `—write-thumbnail` for proper thumbnail handling.

### Limitations and Known Issues ❗

- **Metadata Limitations**: 📄 Some metadata fields may not populate due to limitations in the information accessible from HypnoTube (or haven't gotten around to implement them).

- **Private Video Downloads**: 🛑 The plugin cannot download private videos from HypnoTube.

- **Photo Gallery Downloads**: 📷 The plugin is unable to download photo galleries from HypnoTube.

## Support and Contributions 🤝

For any inquiries or contributions, please [open an issue on GitHub](https://github.com/Earthworm-Banana/yt-dlp-HypnoTube_com-plugin/issues).

Thank you for choosing the HypnoTube.com YT-DLP Plugin. Happy downloading! 🙏
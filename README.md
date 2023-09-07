# HypnoTube.com YT-DLP Plugin 🛠️

## Introduction 📚

Welcome to the HypnoTube.com YT-DLP Plugin, a specialized tool for augmenting your video downloading experience from HypnoTube.com. This plugin allows you to efficiently fetch individual videos, complete user uploads, or entire channels using yt-dlp.

> 📝 **Note**: This plugin and README were largely assisted by OpenAI's GPT-4 model. 

## Features 🌟

- **Individual Video Downloads** 🎥: Directly download HypnoTube videos to your machine.
- **User Uploads** 👤: Retrieve a comprehensive list of videos from a specific HypnoTube user.
- **Channel Downloads** 📺: Extract an entire set of videos from a HypnoTube channel.

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

> 📘 For other methods of installing this plugin package, consult [installing yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins).

## Usage Guidelines 📋

### Commands 📜

- **Individual Video Download** 🎥:
    
    ```bash
    yt-dlp "https://hypnotube.com/video/shock-409.html"
    ```

- **User Uploads Download** 👤:

    ```bash
    yt-dlp "https://hypnotube.com/user/ambersis-3082/"
    ```
  
- **Channel Download** 📺:

    ```bash
    yt-dlp "https://hypnotube.com/channels/38/hd/"
    ```

### Metadata Extraction 🔍

The plugin extracts various types of metadata, including:

- Video Title 📝
- Video ID 🆔
- Release Date 🗓️
- Uploader Information 👤
- View Count 👁️
- Video Duration ⏰

### Limitations and Known Issues ❗

- **Thumbnail Extraction**: 🖼️ Currently, thumbnail extraction is not supported. Extracting thumbnails proved to be a difficult challenge as the thumbnails don't follow a predictable pattern. Despite numerous attempts, it seems virtually impossible to retrieve thumbnails reliably at this time.

- **Metadata Limitations**: 📄 Some metadata fields may not populate due to limitations in the information accessible from HypnoTube.

- **Private Video Downloads**: 🛑 The plugin cannot download private videos from HypnoTube.

- **Photo Gallery Downloads**: 📷 The plugin is unable to download photo galleries from HypnoTube.

## Support and Contributions 🤝

For any inquiries or contributions, please [open an issue on GitHub](https://github.com/Earthworm-Banana/yt-dlp-HypnoTube_com-plugin/issues).

Thank you for choosing the HypnoTube.com YT-DLP Plugin. Happy downloading! 🙏

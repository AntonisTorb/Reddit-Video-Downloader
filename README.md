# Reddit Video Downloader
Python CLI app to download videos from Reddit.

## !!! IMPORTANT !!!
The script requires [FFMPPEG](https://ffmpeg.org/) to be installed in order to combine video and audio files. You can find several tutorials on YouTube on how to install it (I personally use [this build](https://github.com/yt-dlp/FFmpeg-Builds/releases/tag/latest) from the yt-dlp project).

## Parameters:
        -h, --help            show this help message and exit
        -u URL, --url URL     Download video from provided URL.
        -f FILE, --file FILE  Download videos from URLs in provided .txt file (one URL per line).

## How to use

First open the terminal window/command prompt/powershell window in the directory where the main.py file is located. In order to change directory you can use the following command: `cd "path/"`

Make sure to install all the requirements with the command: `pip install -r requirements.txt `


There are two ways to download videos using this app:

- For a single video from reddit post page URL, use the following command: 
    
        python main.py -u "post page url"

- For multiple or a single video by using a text file with reddit post URL(s), use the following command:

        python main.py -f "path to file.txt"

## To do
- ~~Add download in parts functionality for longer video lengths.~~ Done!
- ~~Add retries in case of network disruptions.~~ Done!
- Bug fixes/optimization/refactoring.

## Thank you and enjoy!
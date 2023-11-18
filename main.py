import argparse
import os
from pathlib import Path
import subprocess
import time

import requests

headers = {
    "headers_video": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, identity",
        "Accept-Language": "en-GB,en;q=0.5",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "v.redd.it",
        "Origin": "https://old.reddit.com",
        "Range": "",
        "Referer": "https://old.reddit.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
    },
    "headers_info": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, identity",
        "Accept-Language": "en-GB,en;q=0.5",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "v.redd.it",
        "Range": "bytes=0-",
        "Referer": "https://old.reddit.com/",
        "Sec-Fetch-Dest": "video",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
    },
    "headers_audio": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, identity",
        "Accept-Language": "en-GB,en;q=0.5",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "v.redd.it",
        "Origin": "https://old.reddit.com",
        "Range": "bytes=0-899",
        "Referer": "https://old.reddit.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
    }
}


def get_urls(page_url: str) -> tuple[str, str]|tuple[None, None]:
    '''Gets the required URLs for video and audio files from the web page json.'''

    r = requests.get(f"{page_url[:-1]}.json", 
                     headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"})
    if r.status_code != 200:
        print(f"{r.status_code} for {page_url}. Please check URL provided and your connection status.")
        return None, None
    try:
        video_url = r.json()[0]["data"]["children"][0]["data"]["secure_media"]["reddit_video"]["fallback_url"][:-16]
        has_audio = r.json()[0]["data"]["children"][0]["data"]["secure_media"]["reddit_video"]["has_audio"]
    except TypeError:
        print("Post does not contain a video.")
        return None, None
    if has_audio:
        audio_url = f"https://v.redd.it/{video_url.split('/')[3]}/DASH_AUDIO_128.mp4"
    else:
        audio_url = None

    return video_url, audio_url


def request_with_retries(url: str, headers: dict[str,str], acceptable_codes: list = [206], retries: int = 5) -> requests.Response:
    '''Perform request with retries if the request status code is not in the provided list.'''

    r = requests.get(url, headers=headers, stream=True)
    while retries and r.status_code not in acceptable_codes:
        retries -= 1
        time.sleep(2)
        r = requests.get(url, headers=headers, stream=True)
    return r


def get_video(page_url: str, headers: dict[dict[str,str]]) -> None:
    '''Gets and saves the video and audio files, combines them and removes temporary files.'''

    # Resetting headers.
    headers["headers_video"]["Range"] = ""
    headers["headers_audio"]["Range"] = "bytes=0-899"

    print(f"Getting video from url: {page_url}. Please wait...")
    filename_final = page_url.split("/")[6]
    
    # Just in case.
    if Path(f"_vid-{filename_final}.mp4").exists():
        os.remove(f"_vid-{filename_final}.mp4")
    if Path(f"_audio-{filename_final}.mp4").exists():
        os.remove(f"_audio-{filename_final}.mp4")

    video_url, audio_url = get_urls(page_url)
    if video_url is None:
        return
    
    # Get info on video content length.
    r_vid_info = request_with_retries(video_url, headers["headers_info"])
    if r_vid_info.status_code != 206:
        print(f"Error {r_vid_info.status_code} getting info.")
        return
    max_vid = int(r_vid_info.headers["Content-Length"])

    # Get video file in chunks or all at once depending on size.
    if max_vid > 2097152:
        parts = max_vid // 1048576 + 1
        for part in range(0, parts):
            start = part * 1048576 + 1 if part > 0 else 0
            end = (part+1) * 1048576 if (part+1) * 1048576 < max_vid else max_vid
            headers["headers_video"]["Range"] = f"bytes={start}-{end}"

            # Get video file.
            r_video = request_with_retries(video_url, headers["headers_video"])
            if r_video.status_code != 206:
                print(f"Error {r_video.status_code} getting video.")
                if Path(f"_video-{filename_final}.mp4").exists():
                    os.remove(f"_video-{filename_final}.mp4")
                return
            with open(f"_video-{filename_final}.mp4", "ab") as file:
                file.write(r_video.content)
    else:
        headers["headers_video"]["Range"] = f"bytes=0-{max_vid}"

        # Get video file.
        r_video = request_with_retries(video_url, headers["headers_video"])
        if r_video.status_code != 206:
            print(f"Error {r_video.status_code} getting video file.")
            if Path(f"_video-{filename_final}.mp4").exists():
                os.remove(f"_video-{filename_final}.mp4")
            return
        with open(f"_video-{filename_final}.mp4", "wb") as file:
            file.write(r_video.content)

    # No Audio.
    if not audio_url:
        try:
            os.rename(f"_video-{filename_final}.mp4", f"{filename_final}.mp4")
        except FileExistsError:
            replace = input(f"File '{filename_final}.mp4' already exists. Overwrite? [y/N] ")
            if replace.lower() == "y":
                os.remove(f"{filename_final}.mp4")
                os.rename(f"_video-{filename_final}.mp4", f"{filename_final}.mp4")
            else:
                os.remove(f"_video-{filename_final}.mp4")
        print(f"{page_url}: Done!")
        return

    # Get info on audio content length.
    r_aud_info = request_with_retries(audio_url, headers["headers_audio"], [206, 403])
    if r_aud_info.status_code == 403:
        audio_url = audio_url.replace("AUDIO_128", "audio")  # Older format.
        time.sleep(2)
        r_aud_info = request_with_retries(audio_url, headers["headers_audio"])

    if r_aud_info.status_code != 206:
        print(f"Error {r_aud_info.status_code} getting audio info.")
        return
    
    max_aud = int(r_aud_info.headers["Content-Range"].split("/")[1])

    # Get audio file in chunks or all at once depending on size.
    if max_aud > 2097152:
        parts = max_aud // 1048576 + 1
        for part in range(0, parts):
            start = part * 1048576 + 1 if part > 0 else 0
            end = (part+1) * 1048576 if (part+1) * 1048576 < max_aud else max_aud
            headers["headers_audio"]["Range"] = f"bytes={start}-{end}"

            # Get video file.
            r_audio = request_with_retries(audio_url, headers["headers_audio"])
            if r_audio.status_code != 206:
                print(f"Error {r_audio.status_code} getting audio.")
                if Path(f"_audio-{filename_final}.mp4").exists():
                    os.remove(f"_audio-{filename_final}.mp4")
                return
            with open(f"_audio-{filename_final}.mp4", "ab") as file:
                file.write(r_audio.content)
    else:
        headers["headers_audio"]["Range"] = f"bytes=0-{max_aud}"

        # Get audio file.
        r_audio = request_with_retries(audio_url, headers["headers_audio"])
        if r_audio.status_code != 206:
            print(f"Error {r_audio.status_code} getting audio file.")
            return
        with open(f"_audio-{filename_final}.mp4", "wb") as file:
            file.write(r_audio.content)

    try:
        # Combine video and audio files.
        subprocess.run(
            f'ffmpeg -hide_banner -loglevel error -i "_video-{filename_final}.mp4" -i "_audio-{filename_final}.mp4" -map "0:0" -map "1:0" -c copy "{filename_final}.mp4"'
        )

        # Remove temporary files. 
        os.remove(f"_video-{filename_final}.mp4")
        os.remove(f"_audio-{filename_final}.mp4")
    except:
        print("FFMPEG error, leaving separate video and audio files.")
    
    print(f"{page_url}: Done!")


def get_multi_videos(file_path: str, headers: dict[dict[str,str]]) -> None:
    '''Used to download multiple files in sequence.'''

    file_path = Path(file_path)
    if not file_path.exists():
        print("Filepath for url source does not exist!")
        return
    with open(file_path, "r") as file:
        url_list = file.read().splitlines()
    for page_url in url_list:
        get_video(page_url, headers)
        time.sleep(2)


if __name__ == "__main__":

    # CLI arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=str, help="Download video from provided URL.")
    parser.add_argument("-f", "--file", type=str, help="Download videos from URLs in provided .txt file (one URL per line).")
    args = parser.parse_args()
    
    page_url = args.url
    url_file = args.file
    
    if page_url:
        get_video(page_url, headers)
    elif url_file:
        get_multi_videos(url_file, headers)
    else:
        print("Use command: 'python main.py -h' or 'python3 main.py -h' for assistance.")
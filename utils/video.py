import time
import tempfile
import platform
import subprocess
from moviepy.editor import (AudioFileClip, CompositeVideoClip
                            , TextClip, VideoFileClip)
import requests
import os


class ImageMagickError(Exception):
    """Custom exception for ImageMagick-related errors"""
    pass


def verify_imagemagick():
    """Verify ImageMagick installation and return its path"""
    custom_path = r"C:\Program Files\ImageMagick-6.9.13-Q16-HDRI\convert.exe"
    if os.path.exists(custom_path):
        try:
            subprocess.check_output([custom_path, "-version"])
            return custom_path
        except subprocess.CalledProcessError:
            pass

    search_commands = [
        ["where", "magick"] if platform.system() == "Windows" else ["which", "convert"],
        ["where", "convert"] if platform.system() == "Windows" else ["which", "magick"]
    ]

    for cmd in search_commands:
        try:
            path = subprocess.check_output(cmd).decode().strip()
            subprocess.check_output([path, "-version"])
            return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    raise ImageMagickError("ImageMagick not found. Please verify the installation")


def download_file(url, filename):
    """Download a file with error handling"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        with open(filename, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download file from {url}: {str(e)}")


def safe_delete_file(filepath, max_attempts=5, delay=1):
    """Safely delete a file with multiple attempts"""
    for attempt in range(max_attempts):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
                continue
            print(f"Warning: Could not delete {filepath} after {max_attempts} attempts: {str(e)}")
            return False


def create_text_clip(text, t1, t2, video_size=(1920, 1080)):
    """Create a text clip with improved visibility"""
    try:
        text_clip = TextClip(
            txt=text,
            fontsize=70,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(video_size[0] * 0.9, None),
            align='center'
        )
        y_position = video_size[1] * 0.8
        return (text_clip
                .set_position(('center', y_position))
                .set_start(t1)
                .set_end(t2))
    except Exception as e:
        raise Exception(f"Failed to create text clip: {str(e)}")


# def get_output_media(audio_file_path, timed_captions, background_video_data, video_server):
#     """Generate video with proper resource cleanup and error handling"""
#     OUTPUT_FILE_NAME = os.getenv("OUTPUT_FILE_NAME")
#     temp_files = []
#     video_clips = []
#
#     try:
#         # Verify and configure ImageMagick
#         magick_path = verify_imagemagick()
#         os.environ['IMAGEMAGICK_BINARY'] = magick_path
#         print(f"Using ImageMagick from: {magick_path}")
#
#         visual_clips = []
#         video_size = (1080, 1920)  # Set default video size
#
#         for (t1, t2), video_url in background_video_data:
#             with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
#                 temp_files.append(temp_video.name)
#                 download_file(video_url, temp_video.name)
#                 video_clip = VideoFileClip(temp_video.name)
#
#                 video_clip = video_clip.resize(height=1920)  # Scale height to 1920 while keeping aspect ratio
#
#                 # Optionally, center-crop the video to fit exactly into (1080, 1920)
#                 if video_clip.w > 1080:  # If width is greater than 1080, crop it
#                     x_center = video_clip.w / 2
#                     video_clip = video_clip.crop(x1=x_center - 540, x2=x_center + 540)
#
#                 video_clips.append(video_clip)
#                 if not visual_clips:
#                     video_size = video_clip.size
#                 video_clip = video_clip.set_start(t1).set_end(t2)
#                 visual_clips.append(video_clip)
#
#         if not os.path.exists(audio_file_path):
#             raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
#
#         audio_clip = AudioFileClip(audio_file_path)
#
#         for (t1, t2), text in timed_captions:
#             try:
#                 text_clip = create_text_clip(text, t1, t2, video_size)
#                 visual_clips.append(text_clip)
#             except Exception as e:
#                 print(f"Failed to create TextClip for caption '{text}': {e}")
#
#         video = CompositeVideoClip(visual_clips, size=video_size)
#         video.audio = audio_clip
#         video.duration = audio_clip.duration
#
#         video.write_videofile(
#             OUTPUT_FILE_NAME,
#             codec='libx264',
#             audio_codec='aac',
#             fps=30,
#             bitrate="8000k",
#             preset='medium',
#             temp_audiofile=tempfile.NamedTemporaryFile(suffix='.m4a', delete=False).name
#         )
#
#         return OUTPUT_FILE_NAME
#
#     except ImageMagickError as e:
#         raise e
#     except Exception as e:
#         raise Exception(f"Video generation failed: {str(e)}")
#     finally:
#         for clip in video_clips:
#             try:
#                 clip.close()
#             except:
#                 pass
#         time.sleep(1)
#         for temp_file in temp_files:
#             safe_delete_file(temp_file)


def get_output_media(audio_file_path, timed_captions, background_video_data, video_server):
    """Generate video with memory optimization"""
    OUTPUT_FILE_NAME = os.getenv("OUTPUT_FILE_NAME")
    temp_files = []
    video_clips = []

    try:
        # Verify and configure ImageMagick
        magick_path = verify_imagemagick()
        os.environ['IMAGEMAGICK_BINARY'] = magick_path
        print(f"Using ImageMagick from: {magick_path}")

        visual_clips = []
        video_size = (1080, 1920)

        # Process videos in smaller batches
        batch_size = 3
        for i in range(0, len(background_video_data), batch_size):
            batch = background_video_data[i:i + batch_size]

            for (t1, t2), video_url in batch:
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                    temp_files.append(temp_video.name)
                    download_file(video_url, temp_video.name)

                    # Use lower resolution for processing
                    video_clip = VideoFileClip(temp_video.name, target_resolution=(960, 540))
                    video_clip = video_clip.resize(height=1920)

                    if video_clip.w > 1080:
                        x_center = video_clip.w / 2
                        video_clip = video_clip.crop(x1=x_center - 540, x2=x_center + 540)

                    video_clip = video_clip.set_start(t1).set_end(t2)
                    visual_clips.append(video_clip)

                    # Clean up immediately after processing each video
                    safe_delete_file(temp_video.name)

        audio_clip = AudioFileClip(audio_file_path)

        # Process text clips in batches
        for (t1, t2), text in timed_captions:
            try:
                text_clip = create_text_clip(text, t1, t2, video_size)
                visual_clips.append(text_clip)
            except Exception as e:
                print(f"Failed to create TextClip for caption '{text}': {e}")

        # Use lower quality settings for processing
        video = CompositeVideoClip(visual_clips, size=video_size)
        video.audio = audio_clip
        video.duration = audio_clip.duration

        # Use more memory-efficient settings for video write
        video.write_videofile(
            OUTPUT_FILE_NAME,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            bitrate="4000k",
            preset='faster',
            temp_audiofile=tempfile.NamedTemporaryFile(suffix='.m4a', delete=False).name,
            remove_temp=True,
            threads=2,
            logger=None
        )

        return OUTPUT_FILE_NAME

    except Exception as e:
        raise Exception(f"Video generation failed: {str(e)}")
    finally:
        # Clean up resources
        for clip in video_clips:
            try:
                clip.close()
            except:
                pass
        for temp_file in temp_files:
            safe_delete_file(temp_file)
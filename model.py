import asyncio
import os
from dotenv import load_dotenv
import assemblyai as aai
from utils.script import generate_script
from utils.audio import generate_audio
from utils.timed_caption import generate_timed_captions_assemblyai
from utils.timed_keywords import getVideoSearchQueriesTimed, merge_empty_intervals
from utils.background_videos import generate_video_url
from utils.video import get_output_media

load_dotenv()

# Load API key from environment variables
aai_api_key = os.getenv("AAI_API_KEY")
aai.settings.api_key = aai_api_key

# Define the model_implement function
async def model_implement(topic: str, sample_file_name: str, video_server: str ,voice: str, language:str, content_type:str ):
    try:
        # Step 1: Generate the script based on the topic
        script = generate_script(topic, language,content_type)
        print(f"Generated script: {script}")

        # Step 2: Generate and save the audio based on the script
        await generate_audio(script, sample_file_name ,voice)
        print(f"Audio saved as {sample_file_name}")

        # Step 3: Generate captions using AssemblyAI
        captions = generate_timed_captions_assemblyai(sample_file_name)
        print(f"Generated captions: {captions}")

        # Step 4: Get video search queries based on the script and captions
        search_terms = getVideoSearchQueriesTimed(script, captions)
        print(f"Generated search terms: {search_terms}")

        # Step 5: Generate background video URLs based on search terms
        background_video_urls = None
        if search_terms:
            background_video_urls = generate_video_url(search_terms, video_server)
            print(f"Generated background video URLs: {background_video_urls}")
        else:
            print("No background video URLs generated.")

        # Step 6: Merge empty intervals in the background video URLs
        background_video_urls = merge_empty_intervals(background_video_urls)
        print(f"Merged background video URLs: {background_video_urls}")

        # Step 7: Generate the final video with the background videos, audio, and captions
        if background_video_urls:
            video = get_output_media(sample_file_name, captions, background_video_urls, video_server)
            print(f"Generated video: {video}")
            return video  # Return the path or URL of the generated video
        else:
            print("No video generated due to missing background video URLs.")
            return None  # If no video is generated, return None

    except Exception as e:
        print(f"An error occurred during the model implementation: {e}")
        return None  # Return None in case of an error

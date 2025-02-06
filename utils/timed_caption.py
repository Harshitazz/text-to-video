import assemblyai as aai
import re
from typing import List, Tuple


def generate_timed_captions_assemblyai(audio_filename: str, max_caption_size: int = 15, min_duration: float = 2.0) -> \
List[Tuple[Tuple[float, float], str]]:
    """
    Generate timed captions using AssemblyAI with extended time periods.
    """
    # Initialize transcriber
    transcriber = aai.Transcriber()

    # Get full transcription with word-level timestamps
    transcript = transcriber.transcribe(audio_filename)

    print(transcript.text)
    print(transcript.words)

    return get_captions_with_longer_time_assemblyai(transcript, max_caption_size, min_duration)


def clean_word(word: str) -> str:
    """
    Clean word by removing unwanted characters.
    """
    return re.sub(r'[^\w\s\-_"\'\']', '', word)


def get_captions_with_longer_time_assemblyai(transcript, max_caption_size: int = 15, min_duration: float = 2.0) -> List[
    Tuple[Tuple[float, float], str]]:
    """
    Process AssemblyAI transcript into timed captions format with longer durations.
    """
    caption_pairs = []

    if not transcript.words:
        return caption_pairs

    current_group = []
    current_start = None
    last_end = None

    for word_data in transcript.words:
        if not current_start:
            current_start = word_data.start / 1000.0  # Convert to seconds

        current_group.append(clean_word(word_data.text))
        last_end = word_data.end / 1000.0  # Update end time

        # Finalize the caption if conditions are met
        if len(' '.join(current_group)) >= max_caption_size or (last_end - current_start) >= min_duration:
            caption_pairs.append(
                ((current_start, last_end), ' '.join(current_group))
            )
            current_group = []
            current_start = None  # Reset for the next group

    # Add the last group if any words remain
    if current_group:
        caption_pairs.append(
            ((current_start, last_end), ' '.join(current_group))
        )

    return caption_pairs

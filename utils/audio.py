import os
from pathlib import Path
import asyncio
import edge_tts


async def generate_audio(text, output_filename, voice):
    """Generate audio file with error handling and path validation"""
    try:
        # Ensure absolute path
        output_path = Path(output_filename).resolve()

        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))

        if not output_path.exists():
            raise FileNotFoundError(f"Failed to create audio file at {output_path}")

        return str(output_path)
    except Exception as e:
        raise Exception(f"Error generating audio: {str(e)}")
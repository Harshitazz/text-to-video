# from fastapi import FastAPI
# from pydantic import BaseModel
# from model import model_implement  # Import the refactored function
# import os
# from dotenv import load_dotenv
#
# app = FastAPI()
#
# from fastapi.middleware.cors import CORSMiddleware
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # Next.js URL
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# class TextInput(BaseModel):
#     text: str  # Input text to generate the video
#
# # Load environment variables
# load_dotenv()
# file_path = os.getenv("SAMPLE_FILE_NAME")  # Path to the audio file
# video_server = os.getenv("VIDEO_SERVER")  # Video server URL
#
# @app.post("/generate-video")
# async def generate_video(input: TextInput):
#     try:
#         # Call the model_implement function with the input text
#         video_path = await model_implement(input.text, file_path, video_server)
#
#         if video_path:
#             # Return the video URL or path
#             return {"video_url": f"{video_path}"}
#         else:
#             return {"error": "Video generation failed."}
#     except Exception as e:
#         return {"error": str(e)}
#
# from fastapi.staticfiles import StaticFiles
# app.mount("/static", StaticFiles(directory="static"), name="static")





from fastapi import FastAPI, Form, HTTPException, Request, Depends
from pydantic import BaseModel
from model import model_implement  # Import the refactored function
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import Optional, List
import pickle
from sqlalchemy.orm import Session
from db_setup import get_db, VideoMetadata
from datetime import datetime
from typing import Dict

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()
file_path = os.getenv("SAMPLE_FILE_NAME")  # Path to the audio file
video_server = os.getenv("VIDEO_SERVER")  # Video server URL
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
metadata_store = {}

def create_client_secrets_dict(client_id: str, client_secret: str, redirect_uri: str) -> Dict:
    """Create a client secrets dictionary from environment variables."""
    return {
        "web": {
            "client_id": client_id,
            "project_id":"text-to-video-449213",  # This is optional
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": [redirect_uri]
        }
    }

client_secrets = create_client_secrets_dict(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri=GOOGLE_REDIRECT_URI
)

# OAuth Flow
flow = Flow.from_client_config(
    client_config=client_secrets,
    scopes=SCOPES,
    redirect_uri=GOOGLE_REDIRECT_URI
)


class TextInput(BaseModel):
    text: str  # Input text to generate the video
    voice : str
    language: str
    content: str

class VideoMetadataBase(BaseModel):
    title: str
    description: str
    tags: Optional[List[str]] = ["text-to-video", "development"]
    video_url: str
    youtube_video_id: Optional[str] = None

    class Config:
        orm_mode = True

@app.get('/')
def hello():
    return "Hello, World!"
@app.post("/generate-video")
async def generate_video(input: TextInput, db: Session = Depends(get_db)):
    """
    Generate a video using the input text and upload it to the YouTube channel.
    """
    try:
        # Call the model_implement function with the input text
        video_path = await model_implement(input.text, file_path, video_server, input.voice, input.language, input.content)
        print(video_path)
        if not video_path:
            return {"error": "Video generation failed."}

        # Create metadata entry in database
        db_metadata = VideoMetadata(
            title=f"Generated Video - {datetime.utcnow()}",  # Default title
            description="Auto-generated video from text",
            tags=["text-to-video", "development"],
            video_url=video_path
        )
        db.add(db_metadata)
        db.commit()
        db.refresh(db_metadata)

        # Redirect to the authorization endpoint
        auth_url, _ = flow.authorization_url(prompt="consent")
        return {"message": "Video generated successfully!", "video_path": video_path, "auth_url": auth_url
                ,"metadata_id": db_metadata.id}

    except Exception as e:
        return {"error": str(e)}


@app.post("/upload-video")
async def upload_video(input: VideoMetadataBase,
    db: Session = Depends(get_db)):
    try:
        # Store metadata in database
        db_metadata = VideoMetadata(
            title=input.title,
            description=input.description,
            tags=input.tags,
            video_url=input.video_url
        )
        db.add(db_metadata)
        db.commit()
        db.refresh(db_metadata)

        # Generate OAuth URL and redirect user
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            state=str(db_metadata.id),  # Pass metadata_id as state
            access_type="offline",
            include_granted_scopes="true"
        )
        return {"auth_url": auth_url, "metadata_id": db_metadata.id}

    except Exception as e:
        return {"error": str(e)}


@app.get("/oauth2callback")
async def oauth2callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Fetch authorization code from URL
        code = request.query_params.get("code")
        state = request.query_params.get("state") # You'll need to pass this in the auth flow
        if not state:
            raise HTTPException(
                status_code=400,
                detail="State parameter is missing"
            )

            # Convert state to integer (metadata_id)
        try:
            metadata_id = int(state)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid state parameter"
            )

        flow.fetch_token(code=code)

        # Build YouTube API client
        credentials = flow.credentials
        youtube = build("youtube", "v3", credentials=credentials)

        # Retrieve metadata from database
        db_metadata = db.query(VideoMetadata).filter(VideoMetadata.id == metadata_id).first()
        if not db_metadata:
            raise HTTPException(status_code=404, detail="Video metadata not found")

        # Upload video
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": db_metadata.title,
                    "description": db_metadata.description,
                    "tags": db_metadata.tags,
                    "categoryId": "22",
                },
                "status": {"privacyStatus": "public"},
            },
            media_body=MediaFileUpload(db_metadata.video_url, chunksize=-1, resumable=True),
        )

        response = request.execute()
        video_id = response.get("id")

        # Update database with YouTube video ID
        db_metadata.youtube_video_id = video_id
        db.commit()

        return RedirectResponse(url=f"https://www.youtube.com/watch?v={video_id}")

    except Exception as e:
        return {"error": str(e)}

# Mount static files for serving generated videos
app.mount("/static", StaticFiles(directory="static"), name="static")

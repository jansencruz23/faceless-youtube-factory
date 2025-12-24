"""
YouTube API service for handling OAuth and uploads.
"""

import google_auth_oauthlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple

import google_auth_oauthlib.flow
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config import settings
from app.utils.logging import get_logger
from app.services.encryption_service import encryption_service

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


class YouTubeService:
    """Service for YouTube API interactions."""

    def get_auth_url(self) -> Tuple[str, str]:
        """
        Generate OAuth authorization URL.
        Returns (authorization_url, state).
        """
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
        )

        flow.redirect_uri = settings.oauth_redirect_uri

        authorization_url, state = flow.authorization_url(
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for moving to
            # server-side access.
            access_typ="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        return authorization_url, state

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.
        """
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
        )
        flow.redirect_uri = settings.oauth_redirect_uri

        # Fetch token
        flow.fetch_token(code=code)
        credentials = flow.credentials

        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expiry": credentials.expiry,
            "scopes": credentials.scopes,
        }

    async def get_channel_info(self, access_token: str) -> Dict[str, str]:
        """
        Fetch basic channel info using access token.
        """
        credentials = google.oauth2.credentials.Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=credentials)

        request = youtube.channels().list(
            part="snippet,contentDetails,statistics", mine=True
        )
        response = request.execute()

        if not response.get("items"):
            raise ValueError("No channel found for this user")

        item = response["items"][0]
        return {
            "channel_id": item["id"],
            "title": item["snippet"]["title"],
            "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
        }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.
        """
        try:
            creds = google.oauth2.credentials.Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
            )

            # Refresh request
            import google.auth.transport.requests

            request = google.auth.transport.requests.Request()
            creds.refresh(request)

            return {"token": creds.token, "expiry": creds.expiry}

        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            raise

    async def upload_video(
        self, access_token: str, file_path: str, metadata: Dict[str, Any]
    ) -> str:
        """
        Upload video to YouTube.
        Return video ID if successful.
        """
        credentials = google.oauth2.credentials.Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=credentials)

        body = metadata

        # Create media file object
        # chunksize defaults to 100MB, suitable for most needs
        media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True)

        request = youtube.videos().insert(
            part="snippet,status", body=body, media_body=media
        )

        logger.info("Starting YouTube upload", file=file_path)

        # Execute upload
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                # Can implement progress callback here using status.progress()
                logger.debug("Upload progress", progress=int(status.progress() * 100))

        logger.info("Upload complete", video_id=response.get("id"))
        return response.get("id")


# Singleton instance
youtube_service = YouTubeService()

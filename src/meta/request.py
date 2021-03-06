import base64
import json
import logging
from typing import List, Optional

import requests
from pydantic import validator

from src.app.helper.google_interface import GoogleInterface
from src.app.routes.score import Route
from src.app.schemas.score import LabelMessage

logger = logging.getLogger(__name__)


class SentMessage(LabelMessage):
    @validator("images")
    def images_to_bytes(cls, images):
        imgs = []
        if images is not None:
            for image in images:
                if isinstance(image, str):
                    imgs.append(image)
                elif isinstance(image, bytes):
                    imgs.append(base64.b64encode(image).decode("utf8"))
                else:
                    raise NotImplementedError
            return imgs


def http_call_url(host_url: str, api_app_port: Optional[int] = None):
    if "localhost" not in host_url:
        return host_url
    # if localhost and api app runs a specific port then add it to url
    if api_app_port is not None:
        return f"{host_url}:{api_app_port}"


def get_request_data(
    images: Optional[List[str]] = None,
    images_labels: Optional[List[str]] = None,
    images_urls: Optional[List[str]] = None,
):
    return json.dumps(
        SentMessage(
            images=images,
            images_labels=images_labels,
            images_urls=images_urls,
            user_id="dummy_user_id",
            preferences=["environment", "societal", "animal", "health"],
        ).dict()
    )


def build_full_route(router_prefix: str, route: str, api_app_prefix: str = "/v1"):
    return f"{api_app_prefix}{router_prefix}{route}"


# def build_full_route(route: str):
#     return f"/v1/score{route}"


def post_compute_score(
    images: Optional[List[str]] = None,
    images_urls: Optional[List[str]] = None,
    images_labels: Optional[List[str]] = None,
    api_url: str = "http://localhost",
    api_port: int = 8080,
    authorization_token: Optional[str] = None,
    timeout: int = 3600,
):
    if not api_url.startswith("http://localhost") and authorization_token is None:
        authorization_token = GoogleInterface().generate_id_token(audience=api_url)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {authorization_token}",
    }
    request_url = http_call_url(
        host_url=api_url, api_app_port=api_port
    ) + build_full_route(Route.post_compute_score)
    response = requests.request(
        "POST",
        url=request_url,
        headers=headers,
        data=get_request_data(
            images=images, images_labels=images_labels, images_urls=images_urls
        ),
        timeout=timeout,
    )
    if response.status_code != 200:
        logger.error(
            f"Error during post_videos_to_thumbnails at"
            f" {api_url} : {response.content}"
        )
    return response.content

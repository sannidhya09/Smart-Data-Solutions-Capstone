#!/usr/bin/env python3
"""
RED DUKE — SharePoint File Manager
====================================
Download files from and upload files to a SharePoint document library
using the Microsoft Graph API (client-credentials flow).

Standalone:  python sharepoint_files.py
As a module:  from sharepoint_files import download_from_sharepoint, upload_to_sharepoint

Author: Sannidhya Tiwari
"""

import os
import pathlib
import urllib.parse
from typing import Any

import requests
from dotenv import load_dotenv

# Load variables from .env into the environment
load_dotenv()

# =========================
# CONFIG
# =========================
TENANT_ID = os.getenv("MS_TENANT_ID", "")
CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")

SHAREPOINT_HOSTNAME = os.getenv("SP_HOSTNAME", "")
SITE_PATH = os.getenv("SP_SITE_PATH", "")
FOLDER_PATH_UNDER_ROOT = os.getenv("SP_FOLDER_PATH", "")

# Local folder where files will be downloaded
DOWNLOAD_DIR = os.getenv("SP_DOWNLOAD_DIR", "downloads")

# Remote folder where pipeline outputs will be uploaded (optional)
UPLOAD_FOLDER = os.getenv("SP_UPLOAD_FOLDER", "")


# =========================
# AUTH
# =========================
def get_access_token() -> str:
    """Get a Microsoft Graph access token using client credentials flow."""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    response = requests.post(token_url, data=data, timeout=30)
    response.raise_for_status()

    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("Access token was not found in the token response.")

    return token


# =========================
# GRAPH HELPERS
# =========================
def graph_get(url: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send a GET request to Microsoft Graph and return JSON."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def graph_download(url: str, token: str) -> bytes:
    """Download raw file content from Microsoft Graph."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    return response.content


def graph_put(url: str, token: str, data: bytes, content_type: str = "application/octet-stream") -> dict[str, Any]:
    """Upload raw bytes to a Microsoft Graph URL via PUT and return JSON."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": content_type,
    }
    response = requests.put(url, headers=headers, data=data, timeout=120)
    response.raise_for_status()
    return response.json()


# =========================
# SHAREPOINT HELPERS
# =========================
def get_site_id(token: str) -> str:
    """
    Resolve a SharePoint site to its Graph site ID.

    Graph format:
    /sites/{hostname}:{server-relative-path}
    """
    url = f"https://graph.microsoft.com/v1.0/sites/{SHAREPOINT_HOSTNAME}:{SITE_PATH}"
    site = graph_get(url, token)

    site_id = site.get("id")
    if not site_id:
        raise RuntimeError("Could not find site ID in Graph response.")

    return site_id


def get_default_drive_id(site_id: str, token: str) -> str:
    """
    Get the default document library drive ID for the SharePoint site.
    """
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive"
    drive = graph_get(url, token)

    drive_id = drive.get("id")
    if not drive_id:
        raise RuntimeError("Could not find drive ID in Graph response.")

    return drive_id


def list_children(drive_id: str, token: str, folder_path_under_root: str = "") -> list[dict[str, Any]]:
    """
    List items in the drive root, or in a specific folder under the root.
    """
    if folder_path_under_root.strip() == "":
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
        data = graph_get(url, token)
        return data.get("value", [])

    clean_path = folder_path_under_root.strip().lstrip("/")
    encoded_path = "/".join(urllib.parse.quote(segment) for segment in clean_path.split("/"))

    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{encoded_path}:/children"
    data = graph_get(url, token)
    return data.get("value", [])


def list_children_by_item_id(drive_id: str, token: str, item_id: str) -> list[dict[str, Any]]:
    """
    List child items inside a folder by folder item ID.
    """
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/children"
    data = graph_get(url, token)
    return data.get("value", [])


def download_tree(drive_id: str, token: str, items: list[dict[str, Any]], local_dir: str) -> None:
    """
    Recursively download all files in the provided item list.
    If an item is a folder, enter it and download its contents.
    """
    pathlib.Path(local_dir).mkdir(parents=True, exist_ok=True)

    for item in items:
        name = item.get("name", "unknown")

        if "folder" in item:
            sub_local_dir = str(pathlib.Path(local_dir) / name)
            children = list_children_by_item_id(drive_id, token, item["id"])
            print(f"  Entering folder: {name} ({len(children)} item(s))")
            download_tree(drive_id, token, children, sub_local_dir)
        else:
            out_path = pathlib.Path(local_dir) / name
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item['id']}/content"
            content = graph_download(url, token)
            out_path.write_bytes(content)
            print(f"  Downloaded: {out_path}")


# =========================
# UPLOAD HELPERS
# =========================
def upload_file(drive_id: str, token: str, local_path: str, remote_folder: str = "") -> dict[str, Any]:
    """
    Upload a single local file to SharePoint.

    For files up to ~4 MB (Graph simple upload limit).
    The file is placed inside `remote_folder` (relative to drive root).
    If `remote_folder` is empty the file lands in the drive root.
    """
    name = pathlib.Path(local_path).name

    if remote_folder:
        clean = remote_folder.strip().lstrip("/")
        encoded = "/".join(urllib.parse.quote(s) for s in clean.split("/"))
        url = (
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
            f"/root:/{encoded}/{urllib.parse.quote(name)}:/content"
        )
    else:
        url = (
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
            f"/root:/{urllib.parse.quote(name)}:/content"
        )

    with open(local_path, "rb") as fh:
        data = fh.read()

    result = graph_put(url, token, data)
    print(f"  Uploaded: {local_path}  →  {result.get('webUrl', '(no URL returned)')}")
    return result


def upload_tree(drive_id: str, token: str, local_dir: str, remote_folder: str = "") -> list[dict[str, Any]]:
    """
    Upload all files in `local_dir` (non-recursive) to `remote_folder` on SharePoint.
    Returns a list of Graph item responses.
    """
    results = []
    local_path = pathlib.Path(local_dir)
    if not local_path.exists():
        print(f"  Upload skipped — local directory not found: {local_dir}")
        return results

    files = [f for f in local_path.iterdir() if f.is_file()]
    if not files:
        print(f"  Upload skipped — no files in: {local_dir}")
        return results

    for filepath in sorted(files):
        try:
            item = upload_file(drive_id, token, str(filepath), remote_folder)
            results.append(item)
        except Exception as exc:
            print(f"  Upload failed for {filepath.name}: {exc}")

    return results


# =========================
# HIGH-LEVEL HELPERS (used by main.py)
# =========================
def is_sharepoint_configured() -> bool:
    """Return True if all required SP environment variables are present."""
    return all([TENANT_ID, CLIENT_ID, CLIENT_SECRET, SHAREPOINT_HOSTNAME, SITE_PATH])


def download_from_sharepoint(local_dir: str | None = None) -> str:
    """
    Authenticate, find the configured SP folder, and download everything
    into `local_dir` (defaults to DOWNLOAD_DIR from .env).

    Returns the path to the local directory that was populated.
    """
    dest = local_dir or DOWNLOAD_DIR

    print(f"  Connecting to SharePoint: {SHAREPOINT_HOSTNAME}{SITE_PATH}")
    token = get_access_token()
    print("  Access token acquired ✅")

    site_id = get_site_id(token)
    print(f"  Site ID: {site_id}")

    drive_id = get_default_drive_id(site_id, token)
    print(f"  Drive ID: {drive_id}")

    items = list_children(drive_id, token, FOLDER_PATH_UNDER_ROOT)
    folder_label = FOLDER_PATH_UNDER_ROOT or "[root]"
    print(f"  Found {len(items)} item(s) in '{folder_label}'")

    download_tree(drive_id, token, items, dest)
    return dest


def upload_to_sharepoint(local_dir: str, remote_folder: str | None = None) -> list[dict[str, Any]]:
    """
    Upload all files in `local_dir` to `remote_folder` on SharePoint
    (defaults to SP_UPLOAD_FOLDER from .env, or the source folder).

    Returns a list of Graph item responses.
    """
    dest_folder = remote_folder or UPLOAD_FOLDER or FOLDER_PATH_UNDER_ROOT

    print(f"  Connecting to SharePoint for upload...")
    token = get_access_token()

    site_id = get_site_id(token)
    drive_id = get_default_drive_id(site_id, token)

    print(f"  Uploading files from '{local_dir}' → SP folder '{dest_folder or '[root]'}'")
    return upload_tree(drive_id, token, local_dir, dest_folder)


# =========================
# STANDALONE MAIN
# =========================
def main() -> None:
    required = {
        "MS_TENANT_ID": TENANT_ID,
        "MS_CLIENT_ID": CLIENT_ID,
        "MS_CLIENT_SECRET": CLIENT_SECRET,
        "SP_HOSTNAME": SHAREPOINT_HOSTNAME,
        "SP_SITE_PATH": SITE_PATH,
    }

    missing = [key for key, value in required.items() if not value]
    if missing:
        raise SystemExit(
            "Missing required environment variables: "
            + ", ".join(missing)
            + "\nMake sure they are set in your .env file."
        )

    token = get_access_token()
    print("Got access token ✅")

    site_id = get_site_id(token)
    print(f"Site ID: {site_id}")

    drive_id = get_default_drive_id(site_id, token)
    print(f"Drive ID: {drive_id}")

    items = list_children(drive_id, token, FOLDER_PATH_UNDER_ROOT)
    print(f"Found {len(items)} item(s) in folder: '{FOLDER_PATH_UNDER_ROOT or '[root]'}'")

    for item in items:
        if "folder" in item:
            print(f"  Folder: {item.get('name')}")
        else:
            print(f"  File:   {item.get('name')}")

    print("\nDownloading files...")
    download_tree(drive_id, token, items, DOWNLOAD_DIR)
    print("\nDone ✅")


if __name__ == "__main__":
    main()

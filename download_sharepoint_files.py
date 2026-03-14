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
            print(f"Entering folder: {name} ({len(children)} item(s))")
            download_tree(drive_id, token, children, sub_local_dir)
        else:
            out_path = pathlib.Path(local_dir) / name
            url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item['id']}/content"
            content = graph_download(url, token)
            out_path.write_bytes(content)
            print(f"Downloaded: {out_path}")


# =========================
# MAIN
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
            print(f"Folder: {item.get('name')}")
        else:
            print(f"File:   {item.get('name')}")

    print("\nDownloading files...")
    download_tree(drive_id, token, items, DOWNLOAD_DIR)
    print("\nDone ✅")


if __name__ == "__main__":
    main()
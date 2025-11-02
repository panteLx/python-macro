"""Auto-updater module for checking and downloading updates from GitHub."""

import json
import logging
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# GitHub repository information
GITHUB_OWNER = "panteLx"
GITHUB_REPO = "MacroManager"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
CURRENT_VERSION_FILE = Path(__file__).parent.parent.parent.parent / "VERSION"


def get_current_version() -> str:
    """
    Get the current version of the application.

    Returns:
        Current version string (e.g., "1.0.0")
    """
    if CURRENT_VERSION_FILE.exists():
        return CURRENT_VERSION_FILE.read_text().strip()
    return "0.0.0"


def save_version(version: str) -> None:
    """
    Save version to VERSION file.

    Args:
        version: Version string to save
    """
    CURRENT_VERSION_FILE.write_text(version)
    logger.info(f"Updated version file to {version}")


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic version strings.

    Args:
        version1: First version string (e.g., "1.0.0")
        version2: Second version string (e.g., "1.1.0")

    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    # Remove 'v' prefix if present
    v1 = version1.lstrip('v').split('.')
    v2 = version2.lstrip('v').split('.')

    # Pad with zeros if needed
    while len(v1) < 3:
        v1.append('0')
    while len(v2) < 3:
        v2.append('0')

    # Convert to integers and compare
    for i in range(3):
        try:
            n1 = int(v1[i])
            n2 = int(v2[i])
            if n1 < n2:
                return -1
            elif n1 > n2:
                return 1
        except (ValueError, IndexError):
            continue

    return 0


def check_for_updates() -> Optional[Tuple[str, str, str]]:
    """
    Check GitHub for new releases.

    Returns:
        Tuple of (version, download_url, release_notes) if update available, None otherwise
    """
    try:
        logger.info("Checking for updates...")

        # Make request to GitHub API
        req = urllib.request.Request(GITHUB_API_URL)
        req.add_header('User-Agent', 'MacroManager-AutoUpdater')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        latest_version = data.get('tag_name', '').lstrip('v')
        current_version = get_current_version()

        logger.info(
            f"Current version: {current_version}, Latest version: {latest_version}")

        # Check if update is available
        if compare_versions(current_version, latest_version) < 0:
            # Find the zipball URL
            download_url = data.get('zipball_url')
            release_notes = data.get('body', 'No release notes available.')

            logger.info(f"Update available: {latest_version}")
            return (latest_version, download_url, release_notes)
        else:
            logger.info("No updates available")
            return None

    except urllib.error.URLError as e:
        logger.warning(f"Failed to check for updates (network error): {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}", exc_info=True)
        return None


def download_and_install_update(download_url: str, version: str) -> bool:
    """
    Download and install an update.

    Args:
        download_url: URL to download the update from
        version: Version being installed

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading update from {download_url}")

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "update.zip"

            # Download the zip file
            req = urllib.request.Request(download_url)
            req.add_header('User-Agent', 'MacroManager-AutoUpdater')

            with urllib.request.urlopen(req, timeout=60) as response:
                with open(zip_path, 'wb') as f:
                    f.write(response.read())

            logger.info("Download complete, extracting...")

            # Extract the zip file
            extract_path = temp_path / "extracted"
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # Find the extracted folder (GitHub creates a folder inside)
            extracted_folders = list(extract_path.iterdir())
            if not extracted_folders:
                raise Exception("No files found in downloaded archive")

            source_dir = extracted_folders[0]

            # Get the application root directory
            app_root = Path(__file__).parent.parent.parent.parent

            logger.info(f"Installing update to {app_root}")

            # List of files/folders to update
            items_to_update = ['src', 'main.py',
                               'requirements.txt', 'README.md', 'LICENSE']

            # Backup and update each item
            for item_name in items_to_update:
                source_item = source_dir / item_name
                dest_item = app_root / item_name

                if not source_item.exists():
                    logger.warning(f"Item not found in update: {item_name}")
                    continue

                # Backup existing item if it exists
                if dest_item.exists():
                    backup_path = app_root / f"{item_name}.backup"
                    if backup_path.exists():
                        if backup_path.is_dir():
                            shutil.rmtree(backup_path)
                        else:
                            backup_path.unlink()

                    if dest_item.is_dir():
                        shutil.copytree(dest_item, backup_path)
                    else:
                        shutil.copy2(dest_item, backup_path)

                    logger.info(f"Backed up {item_name}")

                # Remove old item
                if dest_item.exists():
                    if dest_item.is_dir():
                        shutil.rmtree(dest_item)
                    else:
                        dest_item.unlink()

                # Copy new item
                if source_item.is_dir():
                    shutil.copytree(source_item, dest_item)
                else:
                    shutil.copy2(source_item, dest_item)

                logger.info(f"Updated {item_name}")

            # Save new version
            save_version(version)

            logger.info("Update installed successfully!")
            return True

    except Exception as e:
        logger.error(f"Failed to install update: {e}", exc_info=True)
        return False


def cleanup_backups() -> None:
    """Clean up backup files created during update."""
    try:
        app_root = Path(__file__).parent.parent.parent.parent
        for item in app_root.glob("*.backup"):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            logger.info(f"Cleaned up backup: {item.name}")
    except Exception as e:
        logger.warning(f"Failed to cleanup backups: {e}")

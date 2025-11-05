"""Auto-updater module for checking and downloading updates from GitHub."""

import json
import logging
import os
import shutil
import subprocess
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
GITHUB_API_URL_LATEST = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
GITHUB_API_URL_ALL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
CURRENT_VERSION_FILE = Path(__file__).resolve(
).parent.parent.parent.parent / "VERSION"


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
    Compare two semantic version strings with support for pre-release versions.

    Args:
        version1: First version string (e.g., "1.0.0", "1.4.0-beta.1")
        version2: Second version string (e.g., "1.1.0", "1.4.0-beta.2")

    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    # Remove 'v' prefix if present
    v1_str = version1.lstrip('v')
    v2_str = version2.lstrip('v')

    # Split version and pre-release parts
    # e.g., "1.4.0-beta.1" -> ["1.4.0", "beta.1"]
    v1_parts = v1_str.split('-', 1)
    v2_parts = v2_str.split('-', 1)

    # Extract base version numbers
    v1_base = v1_parts[0].split('.')
    v2_base = v2_parts[0].split('.')

    # Extract pre-release identifiers if present
    v1_prerelease = v1_parts[1] if len(v1_parts) > 1 else None
    v2_prerelease = v2_parts[1] if len(v2_parts) > 1 else None

    # Pad with zeros if needed
    while len(v1_base) < 3:
        v1_base.append('0')
    while len(v2_base) < 3:
        v2_base.append('0')

    # Compare base version numbers (major.minor.patch)
    for i in range(3):
        try:
            n1 = int(v1_base[i])
            n2 = int(v2_base[i])
            if n1 < n2:
                return -1
            elif n1 > n2:
                return 1
        except (ValueError, IndexError):
            continue

    # Base versions are equal, now compare pre-release versions
    # According to semver: 1.0.0-alpha < 1.0.0
    if v1_prerelease is None and v2_prerelease is None:
        return 0  # Both are release versions and equal
    elif v1_prerelease is None:
        return 1  # v1 is release, v2 is pre-release, so v1 > v2
    elif v2_prerelease is None:
        return -1  # v1 is pre-release, v2 is release, so v1 < v2

    # Both have pre-release versions, compare them
    # Split by dots: "beta.1" -> ["beta", "1"]
    pre1_parts = v1_prerelease.split('.')
    pre2_parts = v2_prerelease.split('.')

    for i in range(max(len(pre1_parts), len(pre2_parts))):
        # Get parts or empty string if one is shorter
        part1 = pre1_parts[i] if i < len(pre1_parts) else ''
        part2 = pre2_parts[i] if i < len(pre2_parts) else ''

        # Try to compare as integers first
        try:
            num1 = int(part1)
            num2 = int(part2)
            if num1 < num2:
                return -1
            elif num1 > num2:
                return 1
        except ValueError:
            # Compare as strings (alphabetically)
            if part1 < part2:
                return -1
            elif part1 > part2:
                return 1

    return 0


def check_for_updates(channel: str = 'stable') -> Optional[Tuple[str, str, str]]:
    """
    Check GitHub for new releases.

    Args:
        channel: Update channel to check ('stable' or 'beta')
                'stable' checks only official releases
                'beta' checks pre-releases as well

    Returns:
        Tuple of (version, download_url, release_notes) if update available, None otherwise
    """
    try:
        logger.info(f"Checking for updates on {channel} channel...")

        # Determine which API endpoint to use
        if channel == 'beta':
            # For beta, get all releases and find the latest (including pre-releases)
            api_url = GITHUB_API_URL_ALL
        else:
            # For stable, get only the latest non-pre-release
            api_url = GITHUB_API_URL_LATEST

        # Make request to GitHub API
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'MacroManager-AutoUpdater')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        # Handle different response formats
        if channel == 'beta' and isinstance(data, list):
            # For beta channel, get the first release (latest, including pre-releases)
            if not data:
                logger.info("No releases found")
                return None
            latest_release = data[0]
        else:
            # For stable channel, data is a single release object
            latest_release = data

        latest_version = latest_release.get('tag_name', '').lstrip('v')
        current_version = get_current_version()

        logger.info(
            f"Current version: {current_version}, Latest version: {latest_version}")

        # Check if update is available
        if compare_versions(current_version, latest_version) < 0:
            # Find the zipball URL
            download_url = latest_release.get('zipball_url')
            release_notes = latest_release.get(
                'body', 'No release notes available.')
            is_prerelease = latest_release.get('prerelease', False)

            # Add channel info to log
            release_type = "pre-release" if is_prerelease else "release"
            logger.info(f"Update available: {latest_version} ({release_type})")
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


def reinstall_requirements(app_root: Path) -> bool:
    """
    Reinstall pip requirements after an update.

    Args:
        app_root: Root directory of the application

    Returns:
        True if successful, False otherwise
    """
    try:
        import subprocess

        requirements_file = app_root / "requirements.txt"
        if not requirements_file.exists():
            logger.warning(
                "requirements.txt not found, skipping dependency installation")
            return True

        # Get the Python executable that's currently running
        python_exe = sys.executable

        logger.info(f"Installing requirements using: {python_exe}")

        # Run pip install
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            logger.info("Requirements installed successfully")
            logger.debug(f"pip output: {result.stdout}")
            return True
        else:
            logger.error(f"Failed to install requirements: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Timeout while installing requirements")
        return False
    except Exception as e:
        logger.error(f"Error installing requirements: {e}", exc_info=True)
        return False


def safe_remove_tree(path: Path, ignore_errors: bool = False) -> bool:
    """
    Safely remove a directory tree, handling locked files.

    Args:
        path: Path to remove
        ignore_errors: If True, continue even if some files can't be deleted

    Returns:
        True if completely successful, False if some files couldn't be deleted
    """
    def handle_remove_error(func, path, exc_info):
        """Error handler for shutil.rmtree."""
        logger.warning(f"Could not remove {path}: {exc_info[1]}")
        if not ignore_errors:
            raise

    try:
        shutil.rmtree(path, onerror=handle_remove_error)
        return True
    except Exception as e:
        logger.error(f"Failed to remove {path}: {e}")
        return False


def clean_directory_except(directory: Path, preserve_dirs: list) -> None:
    """
    Remove all files and subdirectories except specified ones.

    Args:
        directory: Directory to clean
        preserve_dirs: List of directory names to preserve (e.g., ['logs'])
    """
    if not directory.exists():
        return

    for item in directory.iterdir():
        # Skip preserved directories
        if item.is_dir() and item.name in preserve_dirs:
            logger.info(f"Preserving directory: {item.name}")
            continue

        try:
            if item.is_dir():
                # Recursively clean subdirectories
                if item.name != '__pycache__':
                    logger.debug(f"Removing directory: {item}")
                shutil.rmtree(item, ignore_errors=True)
            else:
                # Remove files except .pyc
                if not item.name.endswith('.pyc'):
                    logger.debug(f"Removing file: {item}")
                item.unlink()
        except Exception as e:
            # Log but continue - don't let one locked file stop the update
            logger.warning(f"Could not remove {item}: {e}")


def download_and_install_update(download_url: str, version: str, is_second_pass: bool = False) -> bool:
    """
    Download and install an update.

    Args:
        download_url: URL to download the update from
        version: Version being installed
        is_second_pass: If True, this is the second pass of a double-update migration

    Returns:
        True if successful, False otherwise
    """
    try:
        if is_second_pass:
            logger.info(f"Running second pass update for migration cleanup...")
        else:
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
            # Use resolved absolute path to work when run as admin
            app_root = Path(__file__).resolve().parent.parent.parent.parent

            logger.info(f"Installing update to {app_root}")

            # List of files/folders to update - these will be completely replaced
            # Note: 'logs' directory at root level is never touched by the updater
            items_to_update = [
                'src',
                'main.py',
                'requirements.txt',
                'README.md',
                'LICENSE',
                'VERSION',
                'start_macromanager.bat'
            ]

            # Config items that need special handling
            config_items_to_update = ['config']

            # Define ignore patterns for copying
            def ignore_patterns(directory, contents):
                """Ignore __pycache__ directories during copy."""
                ignored = []
                for item in contents:
                    # Ignore __pycache__
                    if item in ['__pycache__']:
                        ignored.append(item)
                    # Also ignore .pyc files
                    elif item.endswith('.pyc'):
                        ignored.append(item)
                return ignored

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
                            shutil.rmtree(backup_path, ignore_errors=True)
                        else:
                            backup_path.unlink()

                    # Create backup (skip for src to avoid locked file issues)
                    if item_name != 'src':
                        if dest_item.is_dir():
                            shutil.copytree(dest_item, backup_path,
                                            ignore=ignore_patterns)
                        else:
                            shutil.copy2(dest_item, backup_path)
                        logger.info(f"Backed up {item_name}")
                    else:
                        logger.info(
                            f"Skipping backup of {item_name} (will be overlaid)")

                # Completely remove old item before copying new one
                # Special handling for 'src' directory to overlay existing files
                if dest_item.exists() and item_name != 'src':
                    if dest_item.is_dir():
                        logger.info(f"Removing old {item_name} directory...")
                        shutil.rmtree(dest_item)
                    else:
                        logger.info(f"Removing old {item_name} file...")
                        dest_item.unlink()

                # Copy new item
                if source_item.is_dir():
                    if item_name == 'src':
                        # For src directory, use dirs_exist_ok to overlay files
                        # This avoids issues with locked files
                        logger.info(f"Updating {item_name} directory...")
                        shutil.copytree(source_item, dest_item,
                                        ignore=ignore_patterns,
                                        dirs_exist_ok=True)
                    else:
                        shutil.copytree(source_item, dest_item,
                                        ignore=ignore_patterns)
                else:
                    shutil.copy2(source_item, dest_item)

                logger.info(f"Updated {item_name}")

            # Handle config directory - only update _prebuilt__*.json macros and macro_config.json
            for item_name in config_items_to_update:
                source_item = source_dir / item_name
                dest_item = app_root / item_name

                if not source_item.exists():
                    logger.warning(f"Item not found in update: {item_name}")
                    continue

                # Ensure destination config directory exists
                dest_item.mkdir(parents=True, exist_ok=True)

                # Create recorded_macros subdirectory if it doesn't exist
                recorded_macros_dest = dest_item / "recorded_macros"
                recorded_macros_dest.mkdir(parents=True, exist_ok=True)

                # Copy macro_config.json if it exists
                config_json_source = source_item / "macro_config.json"
                config_json_dest = dest_item / "macro_config.json"
                if config_json_source.exists():
                    if config_json_dest.exists():
                        backup_path = app_root / "macro_config.json.backup"
                        shutil.copy2(config_json_dest, backup_path)
                        logger.info("Backed up macro_config.json")
                    shutil.copy2(config_json_source, config_json_dest)
                    logger.info("Updated macro_config.json")

                # Delete any existing macros starting with bf6_ or _prebuilt__
                for pattern in ["bf6_*.json", "_prebuilt__*.json"]:
                    for existing_macro in recorded_macros_dest.glob(pattern):
                        try:
                            existing_macro.unlink()
                            logger.info(
                                f"Deleted old macro: {existing_macro.name}")
                        except Exception as e:
                            logger.warning(
                                f"Could not delete {existing_macro.name}: {e}")

                # Copy all _prebuilt__*.json macros from the update
                recorded_macros_source = source_item / "recorded_macros"
                if recorded_macros_source.exists():
                    for macro_file in recorded_macros_source.glob("_prebuilt__*.json"):
                        dest_macro = recorded_macros_dest / macro_file.name
                        if dest_macro.exists():
                            backup_path = app_root / \
                                f"{macro_file.name}.backup"
                            shutil.copy2(dest_macro, backup_path)
                            logger.info(f"Backed up {macro_file.name}")
                        shutil.copy2(macro_file, dest_macro)
                        logger.info(
                            f"Updated prebuilt macro: {macro_file.name}")

            # Save new version (do this BEFORE second pass so new code sees new version)
            save_version(version)

            # Reinstall pip requirements
            logger.info("Reinstalling pip requirements...")
            if not reinstall_requirements(app_root):
                logger.warning(
                    "Failed to reinstall requirements. Please run 'pip install -r requirements.txt' manually.")

            logger.info("Update installed successfully!")

            # Run second pass: re-import and run the update again with NEW code
            # This ensures the new cleanup logic runs even if old code didn't have it
            if not is_second_pass:
                logger.info("Running second pass with newly installed code...")

                try:
                    # Reload the auto_updater module to get the new code
                    import sys
                    import importlib

                    # Remove module from cache
                    if 'macro_manager.utils.auto_updater' in sys.modules:
                        del sys.modules['macro_manager.utils.auto_updater']

                    # Re-import with new code
                    from macro_manager.utils import auto_updater as new_module

                    # Call the update function again with the NEW code
                    # Pass is_second_pass=True to prevent infinite recursion
                    logger.info("Calling update with newly installed code...")
                    new_module.download_and_install_update(
                        download_url, version, is_second_pass=True)
                    logger.info("Second pass completed!")

                except Exception as e:
                    logger.warning(f"Second pass failed (not critical): {e}")

            return True

    except Exception as e:
        logger.error(f"Failed to install update: {e}", exc_info=True)
        return False


def cleanup_backups() -> None:
    """Clean up backup files created during update."""
    try:
        app_root = Path(__file__).resolve().parent.parent.parent.parent
        for item in app_root.glob("*.backup"):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            logger.info(f"Cleaned up backup: {item.name}")
    except Exception as e:
        logger.warning(f"Failed to cleanup backups: {e}")

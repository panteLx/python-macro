"""Utility for syncing prebuilt macros from GitHub repository."""

import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# GitHub repository information
GITHUB_OWNER = "panteLx"
GITHUB_REPO = "MacroManager"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/master/config/recorded_macros"


def fetch_prebuilt_macro_list() -> Optional[List[str]]:
    """
    Fetch list of prebuilt macro filenames from GitHub.

    Returns:
        List of prebuilt macro filenames if successful, None otherwise.
    """
    try:
        # Use GitHub API to list files in the recorded_macros directory
        api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/config/recorded_macros"

        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'MacroManager-MacroSync')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        # Filter for prebuilt macros (files starting with _prebuilt__)
        prebuilt_files = [
            item['name']
            for item in data
            if isinstance(item, dict)
            and item.get('type') == 'file'
            and item.get('name', '').startswith('_prebuilt__')
            and item.get('name', '').endswith('.json')
        ]

        logger.info(f"Found {len(prebuilt_files)} prebuilt macros on GitHub")
        return prebuilt_files

    except urllib.error.URLError as e:
        logger.warning(
            f"Failed to fetch prebuilt macro list (network error): {e}")
        return None
    except Exception as e:
        logger.error(
            f"Failed to fetch prebuilt macro list: {e}", exc_info=True)
        return None


def download_prebuilt_macro(filename: str) -> Optional[Dict[str, Any]]:
    """
    Download a prebuilt macro from GitHub.

    Args:
        filename: Name of the macro file to download

    Returns:
        Macro data as dictionary if successful, None otherwise.
    """
    try:
        url = f"{GITHUB_RAW_URL}/{filename}"

        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'MacroManager-MacroSync')

        with urllib.request.urlopen(req, timeout=10) as response:
            macro_data = json.loads(response.read().decode())

        logger.debug(f"Downloaded prebuilt macro: {filename}")
        return macro_data

    except urllib.error.URLError as e:
        logger.warning(f"Failed to download {filename} (network error): {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to download {filename}: {e}", exc_info=True)
        return None


def get_macro_hash(macro_data: Dict[str, Any]) -> str:
    """
    Generate a simple hash of macro data for comparison.

    Args:
        macro_data: Macro data dictionary

    Returns:
        Hash string for comparison
    """
    # Use sorted JSON to ensure consistent hashing
    return json.dumps(macro_data, sort_keys=True)


def sync_prebuilt_macros(macros_dir: Path) -> bool:
    """
    Sync prebuilt macros from GitHub to local storage.

    This function:
    1. Fetches the list of prebuilt macros from GitHub
    2. Downloads each prebuilt macro
    3. Updates local macros if they differ from GitHub versions
    4. Removes obsolete prebuilt macros that no longer exist on GitHub

    Args:
        macros_dir: Directory where macros are stored

    Returns:
        True if sync was successful (or skipped due to network), False on error
    """
    try:
        logger.info("Syncing prebuilt macros from GitHub...")

        # Ensure macros directory exists
        macros_dir.mkdir(parents=True, exist_ok=True)

        # Fetch list of prebuilt macros from GitHub
        github_macros = fetch_prebuilt_macro_list()

        if github_macros is None:
            # Network error or GitHub unavailable - skip sync silently
            logger.info("Skipping macro sync (GitHub unavailable)")
            return True

        if not github_macros:
            logger.info("No prebuilt macros found on GitHub")
            return True

        # Track sync statistics
        updated_count = 0
        added_count = 0
        removed_count = 0
        unchanged_count = 0
        successful_downloads = 0

        # Get existing local prebuilt macros (new format)
        local_prebuilt_macros = {
            f.name: f
            for f in macros_dir.glob('_prebuilt__*.json')
        }

        # Also track old bf6_ macros for deletion (only if sync succeeds)
        old_bf6_macros = list(macros_dir.glob('bf6_*.json'))

        # Download and update/add macros from GitHub
        for filename in github_macros:
            github_macro_data = download_prebuilt_macro(filename)

            if github_macro_data is None:
                logger.warning(f"Skipping {filename} (download failed)")
                continue

            # Count successful downloads
            successful_downloads += 1

            local_file = macros_dir / filename

            # Check if local version exists and differs
            needs_update = True
            is_new = not local_file.exists()

            if local_file.exists():
                try:
                    with open(local_file, 'r', encoding='utf-8') as f:
                        local_data = json.load(f)

                    # Compare macro content
                    if get_macro_hash(local_data) == get_macro_hash(github_macro_data):
                        needs_update = False
                        unchanged_count += 1
                except Exception as e:
                    logger.warning(f"Failed to read local {filename}: {e}")

            # Update or create the macro file
            if needs_update:
                try:
                    with open(local_file, 'w', encoding='utf-8') as f:
                        json.dump(github_macro_data, f, indent=2)

                    if is_new:
                        added_count += 1
                        logger.info(f"Added new prebuilt macro: {filename}")
                    else:
                        updated_count += 1
                        logger.info(f"Updated prebuilt macro: {filename}")

                except Exception as e:
                    logger.error(f"Failed to save {filename}: {e}")

            # Remove from local tracking (remaining will be obsolete)
            if filename in local_prebuilt_macros:
                del local_prebuilt_macros[filename]

        # Only remove obsolete macros if we successfully downloaded at least one macro
        # This prevents deletion if GitHub is unavailable or all downloads fail
        if successful_downloads > 0:
            # Remove obsolete prebuilt macros
            for filename, filepath in local_prebuilt_macros.items():
                try:
                    filepath.unlink()
                    removed_count += 1
                    logger.info(f"Removed obsolete prebuilt macro: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to remove {filename}: {e}")

            # Remove old bf6_ format macros
            for filepath in old_bf6_macros:
                try:
                    filepath.unlink()
                    removed_count += 1
                    logger.info(f"Removed old bf6_ macro: {filepath.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove {filepath.name}: {e}")
        else:
            logger.warning(
                "No macros downloaded successfully - skipping cleanup of old macros")
            # Return False to indicate sync failure
            return False

        # Log summary
        if added_count > 0 or updated_count > 0 or removed_count > 0:
            logger.info(
                f"Macro sync complete: {added_count} added, "
                f"{updated_count} updated, {removed_count} removed, "
                f"{unchanged_count} unchanged"
            )
        else:
            logger.info("All prebuilt macros are up to date")

        return True

    except Exception as e:
        logger.error(f"Failed to sync prebuilt macros: {e}", exc_info=True)
        # Return False to indicate sync failure
        return False

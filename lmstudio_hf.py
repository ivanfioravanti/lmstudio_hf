import json
import os
from pathlib import Path  
import sys
import shutil

def select_models(model_choices):
    # Don't pre-select any models
    selected = [False] * len(model_choices)
    idx = 0
    window_size = os.get_terminal_size().lines - 5
    
    while True:
        print("\033[H\033[J", end="")
        print("❯ lm-studio - Hugging Face Model Manager \nAvailable models (↑/↓ to navigate, SPACE to select, ENTER to confirm, Ctrl+C to quit):")
        
        window_start = max(0, min(idx - window_size + 3, len(model_choices) - window_size))
        window_end = min(window_start + window_size, len(model_choices))

        for i in range(window_start, window_end):
            display_name, _, is_imported, _, _ = model_choices[i]
            # Use red color for already imported models
            if is_imported:
                color = "\033[31m"  # Red
                reset = "\033[0m"   # Reset color
                display_text = f"{color}{display_name}{reset}"
            else:
                display_text = display_name
            print(f"{'>' if i == idx else ' '} {'◉' if selected[i] else '○'} {display_text}")

        key = get_key()
        if key == "\x1b[A":  # Up arrow
            idx = max(0, idx - 1)
        elif key == "\x1b[B":  # Down arrow
            idx = min(len(model_choices) - 1, idx + 1)
        elif key == " ":
            selected[idx] = not selected[idx]
        elif key == "\r":  # Enter key
            break
        elif key == "\x03":  # Ctrl+C
            print("\nImport is cancelled. Do nothing.")
            sys.exit(0)

    return [choice for choice, is_selected in zip(model_choices, selected) if is_selected]

def get_key():
    """Get a single keypress from the user."""
    import tty, termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def manage_models():
    "Import models from the Hugging Face cache."
    # Priority: HF_HOME > XDG_CACHE_HOME/huggingface > ~/.cache/huggingface
    if "HF_HOME" in os.environ:
        cache_dir = Path(os.environ["HF_HOME"])
    elif "XDG_CACHE_HOME" in os.environ:
        cache_dir = Path(os.environ["XDG_CACHE_HOME"]) / "huggingface"
    else:
        cache_dir = Path(os.path.expanduser("~/.cache/huggingface"))
    
    # Allow custom LM Studio directory via environment variable
    if "LMSTUDIO_HOME" in os.environ:
        lm_studio_dir = Path(os.environ["LMSTUDIO_HOME"])
    else:
        lm_studio_dir = Path(os.path.expanduser("~/.cache/lm-studio/models"))
    
    found_models = set()
    
    # Look in hub directory if it exists
    hub_dir = cache_dir / "hub"
    search_dirs = [hub_dir] if hub_dir.exists() else []
    search_dirs.append(cache_dir)
    
    for search_dir in search_dirs:
        for root, dirs, _ in os.walk(search_dir):
            for d in dirs:
                # Skip datasets directories
                if d.startswith("datasets--") or "datasets" in Path(root).parts:
                    continue
                    
                # Check for models--org--name pattern
                if d.startswith("models--") and "--" in d:
                    model_dir = Path(root) / d
                    # Extract model name from models--org--name format
                    parts = d.replace("models--", "").split("--")
                    model_name = "/".join(parts)
                elif "--" in d:  # Check for other HF naming patterns
                    model_dir = Path(root) / d
                    parts = d.split("--")
                    model_name = "/".join(parts)
                else:
                    continue
                
                # Look for snapshots directory
                snapshots_dir = model_dir / "snapshots"
                if not snapshots_dir.exists():
                    continue

                # Search for snapshots - with or without config.json
                model_type = "unknown"
                snapshot_path = None
                
                # Walk through snapshots directory
                for config_root, snapshot_dirs, config_files in os.walk(snapshots_dir):
                    # Skip the snapshots directory itself, look in subdirectories
                    if config_root == str(snapshots_dir) and snapshot_dirs:
                        continue
                    
                    # If we found files in a snapshot subdirectory, this is a valid model
                    if config_files or snapshot_dirs:
                        snapshot_path = Path(config_root)
                        
                        # Try to find config.json for model type
                        if "config.json" in config_files:
                            config_path = Path(config_root) / "config.json"
                            try:
                                with open(config_path) as f:
                                    config = json.load(f)
                                    model_type = config.get("model_type", "unknown").lower()
                            except (json.JSONDecodeError, FileNotFoundError):
                                pass
                        break

                if snapshot_path and model_name:
                    # Store model even if no config.json was found
                    found_models.add((model_type, model_name, snapshot_path))

    if not found_models:
        print("No models found in Hugging Face cache")
        return

    # First, scan all existing models in LM Studio directory recursively
    existing_lm_models = {}  # Maps normalized names to actual paths
    if lm_studio_dir.exists():
        # Check for org/model structure (subdirectories)
        for org_dir in lm_studio_dir.iterdir():
            if org_dir.is_dir():
                # Check if this is an org directory with model subdirectories
                has_subdirs = False
                try:
                    for model_dir in org_dir.iterdir():
                        if model_dir.is_dir():
                            has_subdirs = True
                            # This is org/model format
                            model_name = f"{org_dir.name}/{model_dir.name}"
                            existing_lm_models[model_name] = model_dir
                except:
                    pass  # Handle permission errors
                
                # If no subdirectories, this might be a direct model directory
                if not has_subdirs:
                    existing_lm_models[org_dir.name] = org_dir
    
    # Create list of models with their current import status
    model_choices = []
    for model_type, model, snapshot_path in sorted(found_models):
        is_imported = False
        actual_target_path = None
        
        # Check for the exact model path as it would be created
        if model in existing_lm_models:
            is_imported = True
            actual_target_path = existing_lm_models[model]
        
        # If not found, use default path for new imports or removals
        if actual_target_path is None:
            actual_target_path = lm_studio_dir / model
            
        status = " (already imported)" if is_imported else ""
        display_name = f"({model_type}) {model}{status}"
        model_choices.append((display_name, model, is_imported, snapshot_path, actual_target_path))

    # Show interactive selection menu
    selected = select_models(model_choices)
    print("\nImporting models...\n")
    
    for display_name, model_name, is_imported, snapshot_path, target_path in selected:
        
        if is_imported:
            # Remove existing directory or symlink
            if target_path.is_symlink() or target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
            print(f"Removed {model_name}")
        
        else:
            # Create parent directories and target directory
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Create symbolic links for all files in the snapshot directory
            for item in snapshot_path.iterdir():
                link_path = target_path / item.name
                os.symlink(item, link_path)
            
            print(f"Imported {model_name} (symlinked files)")

if __name__ == "__main__":
    manage_models()


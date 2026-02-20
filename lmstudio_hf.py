import json
import os
from pathlib import Path  
import sys
import shutil


def _cache_search_roots(cache_dir: Path):
    """Return candidate roots that may contain Hugging Face cached repos."""
    roots = [cache_dir]
    hub_dir = cache_dir / "hub"
    if hub_dir.exists():
        roots.append(hub_dir)
    return roots


def _discover_hf_models(cache_dir: Path):
    """Discover cached Hugging Face models limited to MLX or GGUF formats."""
    found_models = set()

    for root in _cache_search_roots(cache_dir):
        for repo_dir in root.glob("models--*"):
            if not repo_dir.is_dir():
                continue

            snapshots_dir = repo_dir / "snapshots"
            if not snapshots_dir.exists():
                continue

            snapshot_path = None
            model_type = None

            repo_name = repo_dir.name.removeprefix("models--")
            repo_name_lower = repo_name.lower()

            for snapshot_dir in sorted(snapshots_dir.iterdir()):
                if not snapshot_dir.is_dir():
                    continue

                # GGUF models are identified by .gguf weights in the snapshot tree.
                if any(p.is_file() for p in snapshot_dir.rglob("*.gguf")):
                    snapshot_path = snapshot_dir
                    model_type = "gguf"
                    break

                # MLX models: either repo naming suggests MLX, or snapshot has
                # MLX-like safetensors artifacts with no legacy framework weights.
                config_candidates = [snapshot_dir / "config.json", *snapshot_dir.rglob("config.json")]
                config_data = None
                for config_path in config_candidates:
                    if not config_path.exists():
                        continue
                    try:
                        with open(config_path) as f:
                            config_data = json.load(f)
                        break
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue

                if not config_data:
                    continue

                has_safetensors = any(p.is_file() for p in snapshot_dir.rglob("*.safetensors"))
                has_legacy_weights = any(
                    p.is_file()
                    for ext in ("*.bin", "*.pt", "*.pth", "*.ckpt", "*.h5", "*.msgpack")
                    for p in snapshot_dir.rglob(ext)
                )
                is_mlx_repo = "mlx" in repo_name_lower
                looks_like_mlx = is_mlx_repo or (has_safetensors and not has_legacy_weights)

                if looks_like_mlx:
                    base_type = str(config_data.get("model_type", "")).lower().strip()
                    model_type = f"mlx:{base_type}" if base_type else "mlx"
                    snapshot_path = snapshot_dir
                    break

            if not snapshot_path or not model_type:
                continue

            model_name = repo_name.replace("--", "/")
            if model_name:
                found_models.add((model_type, model_name, snapshot_path))

    return found_models


def _resolve_lm_studio_models_dir() -> Path:
    """Return LM Studio models directory from settings, or fallback default."""
    fallback = Path(os.path.expanduser("~/.cache/lm-studio/models"))
    settings_path = Path(os.path.expanduser("~/.lmstudio/settings.json"))

    try:
        with settings_path.open() as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return fallback

    configured_path = settings.get("downloadsFolder")
    if not isinstance(configured_path, str) or not configured_path.strip():
        return fallback

    return Path(os.path.expanduser(configured_path))

def select_models(model_choices):
    selected = [False] * len(model_choices)
    idx = 0
    window_size = os.get_terminal_size().lines - 5
    
    while True:
        print("\033[H\033[J", end="")
        print("❯ lm-studio - Hugging Face Manage models \nAvailable models (↑/↓ to navigate, SPACE to select, ENTER to confirm, Ctrl+C to quit):")
        
        window_start = max(0, min(idx - window_size + 3, len(model_choices) - window_size))
        window_end = min(window_start + window_size, len(model_choices))

        for i in range(window_start, window_end):
            display_name, _, _, _ = model_choices[i]
            print(f"{'>' if i == idx else ' '} {'◉' if selected[i] else '○'} {display_name}")

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
    "Import MLX and GGUF models from the Hugging Face cache."
    cache_dir = Path(
        os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    )
    lm_studio_dir = _resolve_lm_studio_models_dir()

    found_models = _discover_hf_models(cache_dir)

    if not found_models:
        print("No MLX or GGUF models found in Hugging Face cache")
        return

    # Create list of models with their current import status
    model_choices = []
    for model_type, model, snapshot_path in sorted(found_models):
        target_path = lm_studio_dir / f"{model}"
        is_imported = target_path.exists()
        status = " (already imported)" if is_imported else ""
        display_name = f"({model_type}) {model}{status}"
        model_choices.append((display_name, model, is_imported, snapshot_path))

    # Show interactive selection menu
    selected = select_models(model_choices)
    print("\nImporting models...\n")

    if not selected:
        print("No models selected. Nothing to import.")
        return

    print(f"LM Studio models directory: {lm_studio_dir}")
    
    for display_name, model_name, is_imported, snapshot_path in selected:
        target_path = lm_studio_dir / f"{model_name}"
        
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
            print(f"Importing {model_name}")
            print(f"  HF snapshot source: {snapshot_path}")
            print(f"  LM Studio target:  {target_path}")
            
            # Create symbolic links for all files in the snapshot directory
            for item in snapshot_path.iterdir():
                link_path = target_path / item.name
                print(f"  ln -s {item} {link_path}")
                os.symlink(item, link_path)
            
            print(f"Imported {model_name} (symlinked files)")

def main():
    """Entry point for uvx execution"""
    manage_models()

if __name__ == "__main__":
    main()

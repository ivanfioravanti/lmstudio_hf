# LM Studio - Hugging Face Model Manager

A command-line utility to manage MLX models between your Hugging Face cache and LM Studio. This tool makes it easy to import and manage models you've downloaded from Hugging Face into LM Studio.

## Features

- Interactive model selection interface with keyboard navigation
- Automatic detection of MLX models in your Hugging Face cache
- Smart handling of model imports via symbolic links
- Support for model replacement and removal
- Terminal-based UI with scrolling for large model lists

## Prerequisites

- Python 3.x
- LM Studio installed
- Hugging Face models downloaded locally

## Installation

You can skip this if you are using uvx remote execution (see below).

1. Clone this repository:
```bash
git clone https://github.com/ivanfioravanti/lmstudio_hf.git
cd lmstudio_hf
```

## Usage

Run the script using Python:

```bash
python lmstudio_hf.py
```

Alternatively, you can use uvx remote execution:
```bash
uvx git+https://github.com/ivanfioravanti/lmstudio_hf
```

### Navigation Controls

- ↑/↓ arrows: Navigate through the model list
- SPACE: Select/deselect a model
- ENTER: Confirm selection and proceed with import
- Ctrl+C: Cancel operation

## How It Works

1. The tool scans your Hugging Face cache directory (`~/.cache/huggingface` by default)
2. Identifies MLX-compatible models (excluding specific types like Whisper, LLaVA, etc.)
3. Creates symbolic links in the LM Studio models directory configured in `~/.lmstudio/settings.json` (`downloadsFolder`)
4. Allows for easy management of existing imports

## Environment Variables

- `HF_HOME`: Optional. Set this to customize your Hugging Face cache location.

If `downloadsFolder` is missing or unreadable, the tool falls back to `~/.cache/lm-studio/models`.

## Notes

- Models are imported using symbolic links to save disk space
- Already imported models are marked in the selection interface
- Selecting an already imported model will remove it from LM Studio

## Contributing

Feel free to open issues or submit pull requests for any improvements or bug fixes.

## License

[MIT License](LICENSE) 

# LM Studio - Hugging Face Model Manager

A command-line utility to manage models between your Hugging Face cache and LM Studio. This tool makes it easy to import and manage any models you've downloaded from Hugging Face into LM Studio.

## Features

- Interactive model selection interface with keyboard navigation
- Automatic detection of all models in your Hugging Face cache
- Smart handling of model imports via symbolic links
- Support for model removal and re-import
- Terminal-based UI with scrolling for large model lists
- Shows model type (e.g., llama, bert, gpt2) for easy identification
- Already imported models are pre-selected and clearly marked

## Prerequisites

- Python 3.x
- LM Studio installed
- Hugging Face models downloaded locally

## Installation

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

### Using Custom Directories

You can customize the directories using environment variables:

```bash
# Custom Hugging Face cache directory
export HF_HOME="/path/to/huggingface/cache"
python lmstudio_hf.py

# Custom LM Studio models directory
export LMSTUDIO_HOME="/path/to/lmstudio/models"
python lmstudio_hf.py

# Use XDG cache directory
export XDG_CACHE_HOME="/path/to/cache"
python lmstudio_hf.py

# Combine multiple environment variables
export HF_HOME="/custom/hf/cache"
export LMSTUDIO_HOME="/custom/lmstudio/models"
python lmstudio_hf.py
```

### Navigation Controls

- ↑/↓ arrows: Navigate through the model list
- SPACE: Select/deselect a model
- ENTER: Confirm selection and proceed with import
- Ctrl+C: Cancel operation

## How It Works

1. The tool scans your Hugging Face cache directory (checks `HF_HOME`, `XDG_CACHE_HOME/huggingface`, or `~/.cache/huggingface`)
2. Identifies all downloaded models with valid `config.json` files
3. Creates symbolic links in the LM Studio models directory (`~/.cache/lm-studio/models`)
4. Shows model type and import status for each model
5. Pre-selects already imported models for easy management

## Environment Variables

- `HF_HOME`: Optional. Set this to customize your Hugging Face cache location (highest priority)
- `XDG_CACHE_HOME`: Optional. If set, the tool will look for models in `$XDG_CACHE_HOME/huggingface`
- `LMSTUDIO_HOME`: Optional. Set this to customize your LM Studio models directory (default: `~/.cache/lm-studio/models`)

## Notes

- Models are imported using symbolic links to save disk space
- Already imported models are marked with "(already imported)" and pre-selected
- Deselecting an already imported model and confirming will remove it from LM Studio
- Model types are displayed in parentheses (e.g., `(llama)`, `(bert)`, `(gpt2)`)

## Contributing

Feel free to open issues or submit pull requests for any improvements or bug fixes.

## License

[MIT License](LICENSE) 
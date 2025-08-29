# AI Image Sorter

This Python script automatically sorts images into folders using AI classification. It uses the OpenRouter API with the MistralAI/Mistral-Small-3.2-24B-Instruct:free model to analyze images and determine which folder they should be placed in.

## Features

- Automatically creates input and output folders
- Uses AI to classify images into appropriate categories
- Can create new folders as needed based on AI suggestions
- Supports common image formats (PNG, JPG, JPEG, GIF, BMP, TIFF, WebP)
- Handles API errors gracefully
- Supports loading API key from .env file

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenRouter API key:**
   You can set your OpenRouter API key in one of two ways:
   
   **Option 1: Using a .env file (Recommended)**
   - Copy the `.env.example` file to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit the `.env` file and replace `your_openrouter_api_key_here` with your actual API key
   
   **Option 2: Using environment variables:**
   On Windows:
   ```cmd
   set OPENROUTER_API_KEY=your_api_key_here
   ```
   
   On macOS/Linux:
   ```bash
   export OPENROUTER_API_KEY=your_api_key_here
   ```

## Usage

1. Place images you want to sort into the `in` folder (this folder will be created automatically if it doesn't exist)

2. Run the script:
   ```bash
   python ai_image_sorter.py
   ```

3. The sorted images will be moved to appropriate subfolders within the `sorted` folder (this folder will also be created automatically if it doesn't exist)

## How It Works

1. The script scans the `in` folder for images
2. For each image, it sends the image to the OpenRouter API with the MistralAI/Mistral-Small-3.2-24B-Instruct:free model
3. The AI model analyzes the image and responds with either:
   - A folder name to place the image in (e.g., "image.jpg:cats")
   - A command to create a new folder (e.g., "create_folder:birds")
4. The script creates new folders as needed and moves images to their appropriate folders
5. Images are moved from the `in` folder to the appropriate subfolder in the `sorted` folder

## Folder Structure

```
ai-image-sorter/
├── ai_image_sorter.py    # Main script
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── .env.example          # Example .env file
├── in/                   # Place images here to be sorted (created automatically)
└── sorted/               # Sorted images will be placed here (created automatically)
    ├── cats/             # Example folder
    ├── dogs/             # Example folder
    └── ...               # Other folders created by the AI
```

## Model Response Format

The AI model is expected to respond in one of these formats:
- `image_name:folder_name` - Places the image in the specified folder
- `create_folder:folder_name` - Creates a new folder with the specified name

## Notes

- The script will create the `in` and `sorted` folders automatically if they don't exist
- New folders within the `sorted` directory will be created as needed based on the AI's responses
- Images are moved (not copied) from the `in` folder to the appropriate folder in `sorted`
- The script processes images one at a time
- If the AI suggests creating a new folder, the script will create it and then ask the AI again where to place the image
- The script first looks for the API key in a `.env` file, then falls back to environment variables

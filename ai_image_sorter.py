import os
import base64
import requests
import json
from PIL import Image
import io
import shutil
from typing import List
from dotenv import load_dotenv

# Configuration
MODEL = "mistralai/mistral-small-3.2-24b-instruct:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Folder names
INPUT_FOLDER = "in"
OUTPUT_FOLDER = "sorted"

def create_folders():
    """Create input and output folders if they don't exist"""
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"Created/verified folders: {INPUT_FOLDER}, {OUTPUT_FOLDER}")

def get_image_files() -> List[str]:
    """Get all image files from the input folder"""
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
    image_files = []
    
    for file in os.listdir(INPUT_FOLDER):
        if file.lower().endswith(image_extensions):
            image_files.append(file)
    
    return image_files

def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_available_folders() -> List[str]:
    """Get list of existing folders in the output directory"""
    folders = []
    for item in os.listdir(OUTPUT_FOLDER):
        if os.path.isdir(os.path.join(OUTPUT_FOLDER, item)):
            folders.append(item)
    return folders

def send_to_openrouter(image_path: str) -> str:
    """Send image to OpenRouter API for classification"""
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found. Please set it in your .env file or as an environment variable.")
        return None
    
    # Encode image
    base64_image = encode_image_to_base64(image_path)
    
    # Get available folders
    available_folders = get_available_folders()
    
    # Create prompt based on prompts.md
    folder_list = "\n".join(available_folders) if available_folders else "cats\ndogs"
    prompt = f"""# Main
Below are images you will Sort and put into its respective folders, do not output anything else besides the image name and its output. Here are the available folders for you to put them into. if there is an image that requires a new folder you may create one by outputting this "create_folder:NAME".
The syntax for how you should output the images are below:
image:folder
The available folders are below
{folder_list}

# Sub sort
Below are images you will Sort and put into its respective  subfolders, do not output anything else besides the image name and its output. Here are the available folders for you to put them into. if there is an image that requires a new folder you may create one by outputting this "create_folder:NAME".
The syntax for how you should output the images are below:
image:folder
The available images are below, you are limited to only seeing 5 images for quality, do not be confused if u see 5 or less.

Please classify this image and respond with the appropriate folder or create_folder command."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return None

def create_new_folder(folder_name: str) -> bool:
    """Create a new folder in the output directory"""
    try:
        folder_path = os.path.join(OUTPUT_FOLDER, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        print(f"Created new folder: {folder_path}")
        return True
    except Exception as e:
        print(f"Error creating folder {folder_name}: {e}")
        return False

def move_image_to_folder(image_name: str, folder_name: str) -> bool:
    """Move an image from input folder to the specified folder in output directory"""
    try:
        source_path = os.path.join(INPUT_FOLDER, image_name)
        destination_folder_path = os.path.join(OUTPUT_FOLDER, folder_name)
        destination_path = os.path.join(destination_folder_path, image_name)
        
        # Check if source file exists
        if not os.path.exists(source_path):
            print(f"Source file {source_path} does not exist!")
            return False
        
        # Check if destination folder exists, create if it doesn't
        if not os.path.exists(destination_folder_path):
            print(f"Destination folder {destination_folder_path} does not exist, creating it...")
            os.makedirs(destination_folder_path, exist_ok=True)
        
        print(f"Moving {image_name} from {source_path} to {destination_path}")
        shutil.move(source_path, destination_path)
        print(f"Moved {image_name} to {folder_name}")
        return True
    except Exception as e:
        print(f"Error moving {image_name} to {folder_name}: {e}")
        return False

def process_model_response(image_name: str, response: str) -> bool:
    """Process the model's response and take appropriate action"""
    print(f"Processing response for {image_name}: {response}")
    if not response:
        print(f"No response for {image_name}")
        return False
    
    # Check if response is a create_folder command
    if response.startswith("create_folder:"):
        folder_name = response.split(":", 1)[1].strip()
        print(f"Creating folder: {folder_name}")
        if create_new_folder(folder_name):
            # After creating folder, we need to move the image there
            # For now, we'll just return True and handle this in the main loop
            return True
    
    # Check if response is in image:folder format
    elif ":" in response:
        parts = response.split(":", 1)
        if len(parts) == 2 and parts[0].strip() == image_name:
            folder_name = parts[1].strip()
            print(f"Moving {image_name} to folder: {folder_name}")
            return move_image_to_folder(image_name, folder_name)
        else:
            print(f"Response format not matching image:folder pattern: {response}")
            # Try to handle cases where the model doesn't prefix with image name
            folder_name = parts[1].strip() if len(parts) == 2 else response.strip()
            print(f"Attempting to move {image_name} to folder: {folder_name}")
            return move_image_to_folder(image_name, folder_name)
    
    # If response is just a folder name
    else:
        folder_name = response.strip()
        print(f"Moving {image_name} to folder: {folder_name}")
        return move_image_to_folder(image_name, folder_name)
    
    return False

def main():
    """Main function to process images"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found. Please set it in your .env file or as an environment variable.")
        return
    
    # Create folders
    create_folders()
    
    # Get image files
    image_files = get_image_files()
    
    if not image_files:
        print(f"No image files found in {INPUT_FOLDER} folder")
        return
    
    print(f"Found {len(image_files)} image(s) to process")
    
    # Process each image
    for image_name in image_files:
        print(f"Processing {image_name}...")
        
        # Full path to image
        image_path = os.path.join(INPUT_FOLDER, image_name)
        
        # Send to OpenRouter API
        response = send_to_openrouter(image_path)
        
        if response:
            print(f"Model response for {image_name}: {response}")
            
            # Process the response
            print(f"Processing model response for {image_name}: {response}")
            if response.startswith("create_folder:"):
                folder_name = response.split(":", 1)[1].strip()
                print(f"Model requested creating folder: {folder_name}")
                if create_new_folder(folder_name):
                    # Now we need to ask the model again where to put the image
                    # since we just created a new folder option
                    print(f"Asking model again where to put {image_name} after creating folder {folder_name}")
                    response = send_to_openrouter(image_path)
                    if response and not response.startswith("create_folder:"):
                        print(f"Model's second response for {image_name}: {response}")
                        process_model_response(image_name, response)
                    else:
                        print(f"Model's second response for {image_name} was invalid or missing: {response}")
            else:
                process_model_response(image_name, response)
        else:
            print(f"Failed to get response for {image_name}")
    
    print("Processing complete!")

if __name__ == "__main__":
    main()

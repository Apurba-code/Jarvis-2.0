import os
import requests
import webbrowser
import random
import base64
from time import sleep
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys from .env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def GenerateImage(prompt):
    """Generates a premium 'Nano-Quality' image using professional APIs."""
    print(f"JARVIS: Initializing Nano-Engine for: {prompt}...")
    
    # Clean the prompt
    clean_prompt = prompt.lower().replace("generate", "").replace("image", "").replace("visualize", "").replace("create", "").strip()
    
    if not clean_prompt:
        return "Please provide a description for the image."

    # Nano Quality Boost: Advanced Prompt Engineering
    quality_modifiers = (
        "nano banana style, cinematic lighting, 8k resolution, highly detailed, "
        "photorealistic, sharp focus, masterpiece composition, professional photography"
    )
    full_prompt = f"{clean_prompt}, {quality_modifiers}"

    # Path Setup
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    save_dir = os.path.join(project_root, "Data", "Images")
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    safe_filename = "".join([c for c in clean_prompt[:25] if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not safe_filename: safe_filename = "generated_image"
    file_path = os.path.join(save_dir, f"{safe_filename}.png")

    # Provider Selection Logic
    try:
        # Priority 1: Google Gemini (Nano Banana Engine)
        if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
            print(f"JARVIS: Utilizing Google Nano Engine (Imagen 3/4)...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={GOOGLE_API_KEY}"
            payload = {"instances": [{"prompt": full_prompt}], "parameters": {"sampleCount": 1}}
            
            try:
                response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
                if response.status_code == 200:
                    img_data = base64.b64decode(response.json()["predictions"][0]["bytesBase64Encoded"])
                    with open(file_path, "wb") as f:
                        f.write(img_data)
                elif "billed users" in response.text or response.status_code == 400:
                    print("JARVIS: Google engine restricted (Unbilled). Checking next provider...")
                else:
                    print(f"JARVIS: Google API Status {response.status_code}. Checking fallback...")
            except Exception as e:
                print(f"JARVIS: Google Engine failed: {e}")

        # Priority 2: Hugging Face (FLUX.1) - Official Hub Client
        if not os.path.exists(file_path) and HF_TOKEN and HF_TOKEN != "your_huggingface_token_here":
            print(f"JARVIS: Utilizing Hugging Face (FLUX.1) Engine...")
            try:
                from huggingface_hub import InferenceClient
                client = InferenceClient(token=HF_TOKEN)
                image = client.text_to_image(full_prompt, model="black-forest-labs/FLUX.1-schnell")
                image.save(file_path)
            except Exception as e:
                if "Forbidden" in str(e) or "403" in str(e):
                    print("JARVIS: HF Token missing 'Inference Provider' permissions. Please update your token.")
                else:
                    print(f"JARVIS: Hugging Face failed: {e}")

        # Priority 3: OpenAI (DALL-E 3)
        if not os.path.exists(file_path) and OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_key_here":
            print(f"JARVIS: Utilizing OpenAI (DALL-E 3) Engine...")
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                response = client.images.generate(model="dall-e-3", prompt=full_prompt, size="1024x1024", quality="hd", n=1)
                img_data = requests.get(response.data[0].url).content
                with open(file_path, "wb") as f:
                    f.write(img_data)
            except Exception as e:
                print(f"JARVIS: OpenAI failed: {e}")
        
        # Final Verification
        if os.path.exists(file_path):
            print(f"JARVIS: Nano-Quality Image saved to {file_path}")
            webbrowser.open(os.path.abspath(file_path))
            return f"I have generated the visual for: {clean_prompt}."
        else:
            return ("Image generation failed. Please check if your Google key is billed or "
                    "ensure your Hugging Face token has 'Inference Provider' permissions enabled.")

    except Exception as e:
        return f"Engine Failure: {e}"

if __name__ == "__main__":
    test_prompt = "a modern interior of a hotel room"
    print(GenerateImage(test_prompt))

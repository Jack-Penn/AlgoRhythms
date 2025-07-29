import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, cast
import asyncio
from PIL import Image
from io import BytesIO
import base64

# Load environment variables
load_dotenv(dotenv_path='./secrets.env')
gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)

# Define Pydantic models for structured output
class TargetFeatures(BaseModel):
    energy: float
    valence: float
    danceability: float
    acousticness: float
    instrumentalness: float
    speechiness: float
    liveness: float
    tempo: int
    loudness: int 

class PlaylistExample(BaseModel):
    mood: str
    activity: str
    target_features: TargetFeatures

# Define examples as structured objects
EXAMPLES: List[PlaylistExample] = [
    PlaylistExample(
        mood="calm",
        activity="studying",
        target_features=TargetFeatures(
            acousticness=0.8,
            danceability=0.2,
            energy=0.3,
            instrumentalness=0.7,
            liveness=0.1,
            loudness=-21,
            speechiness=0.1,
            tempo=75,
            valence=0.6
        )
    ),
    PlaylistExample(
        mood="energetic",
        activity="working out",
        target_features=TargetFeatures(
            acousticness=0.1,
            danceability=0.9,
            energy=0.95,
            instrumentalness=0.4,
            liveness=0.2,
            loudness=-5,
            speechiness=0.2,
            tempo=145,
            valence=0.8
        )
    ),
    PlaylistExample(
        mood="melancholic",
        activity="relaxing",
        target_features=TargetFeatures(
            acousticness=0.95,
            danceability=0.1,
            energy=0.2,
            instrumentalness=0.6,
            liveness=0.1,
            loudness=-15,
            speechiness=0.05,
            tempo=65,
            valence=0.3
        )
    )
]

def format_playlist_examples(examples: List[PlaylistExample]) -> str:
    """Converts structured examples into prompt text"""
    formatted = []
    for ex in examples:
        formatted.append(
            f"- Mood: \"{ex.mood}\", Activity: \"{ex.activity}\"\n"
            f"  TargetFeatures: {ex.target_features.model_dump()}"
        )
    return "\n\n".join(formatted)

async def generate_target_features(mood: str, activity: str) -> TargetFeatures:
    """
    Converts mood and activity descriptions into target playlist parameters
    using Gemini's structured JSON output.
    
    Args:
        mood: User's emotional state (e.g., "happy", "melancholic")
        activity: Current activity (e.g., "studying", "working out")
    
    Returns:
        TargetFeatures: Structured tareget features for playlist generation
    """
    
    feature_definitions = """
    - acousticness (0.0-1.0): Confidence measure of acoustic sounds vs electronic elements.
      Higher values (1.0) = more natural/organic sounds, lower values (0.0) = more synthetic.
      
    - danceability (0.0-1.0): How suitable for dancing based on rhythm, beat, and tempo.
      0.0 = not danceable, 1.0 = highly danceable. Considers beat strength and consistency.
      
    - energy (0.0-1.0): Perceived intensity and activity level.
      0.0 = calm/relaxed, 1.0 = intense/energetic. Based on dynamic range, loudness, and entropy.
      
    - instrumentalness (0.0-1.0): Predicts absence of vocals.
      >0.5 = likely instrumental, near 1.0 = high confidence no vocals. "Ooh/aah" = instrumental.
      
    - liveness (0.0-1.0): Probability of live audience presence.
      >0.8 = strong likelihood of live recording, 0.0 = studio production.
      
    - loudness (-60 to 0 dB): Overall average loudness in decibels (dB).
      Typical range: -60dB (quiet) to 0dB (loud). Note: dB is logarithmic scale.
      
    - speechiness (0.0-1.0): Presence of spoken words.
      <0.33 = music, 0.33-0.66 = mixed (e.g., rap), >0.66 = primarily speech (podcast/audiobook).
      
    - tempo (BPM): Estimated beats per minute (actual value).
      Typical range: 60-200 BPM. 60 = slow, 120 = moderate, 200 = very fast.
      
    - valence (0.0-1.0): Emotional positivity.
      0.0 = sad/depressing, 1.0 = happy/euphoric. Musical positiveness measure.
    """
    
    prompt = f"""
    Create appropriate audio features that match this mood and activity for selecting songs for a playlist.
    Mood: "{mood}"
    Activity: "{activity}"

    Use the following definitions for each audio feature:
    {feature_definitions}
    
    Please return actual BPM for tempo and dB for loudness (not normalized values).

    Here are some example feautre outputs:
    {format_playlist_examples(EXAMPLES)}
    """
    
    # Wrap synchronous API call in thread
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-lite-preview-06-17",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": TargetFeatures,
        }
    )
    
    # Handle response
    if response.parsed:
        return cast(TargetFeatures, response.parsed)
    else:
        raise ValueError(f"Failed to parse Gemini response: {response.text}")

async def generate_emoji(term: str) -> str:
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-lite-preview-06-17",
        contents=f"please generate a single emoji that most closely represents the given input. Only generate one emoji character. input: {term}",
        config={}
    )
    if response.text:
        if len(response.text) > 2:
            raise ValueError("Gemini did not respond with a single emoji")
        return response.text
    else:
        raise ValueError("Gemini did not respond error")

async def generate_playlist_image(quality=85):
    """
    Generates an image, fixes type errors, converts it to Base64 JPEG,
    and checks if it's under the size limit.
    """

    prompt = ('Hi, can you create a photorealistic image of a pig '
                'with wings and a top hat flying over a happy '
                'futuristic scifi city with lots of greenery?')

    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
        )
    )

    MAX_PAYLOAD_SIZE_KB = 256
    MAX_PAYLOAD_SIZE_BYTES = MAX_PAYLOAD_SIZE_KB * 1024

    base64_jpeg_data = None
    jpeg_bytes = None

    if response and response.candidates:
        candidate = response.candidates[0]
        if candidate and candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    try:
                        image_bytes = part.inline_data.data
                        print(f"Original image size from API (PNG): {len(image_bytes) / 1024:.2f} KB")

                        image = Image.open(BytesIO(image_bytes))

                        # Convert to JPEG and save to an in-memory buffer
                        jpeg_buffer = BytesIO()
                        # Convert to RGB if it's RGBA (JPEG doesn't support alpha)
                        if image.mode == 'RGBA':
                            image = image.convert('RGB')
                        image.save(jpeg_buffer, "JPEG", quality=quality) # Adjust quality as needed
                        jpeg_bytes = jpeg_buffer.getvalue()

                        # Encode the JPEG bytes to Base64
                        base64_encoded_bytes = base64.b64encode(jpeg_bytes)
                        base64_jpeg_data = base64_encoded_bytes.decode('utf-8')
                        
                        # --- Check that the size does not exceed the limit ---
                        payload_size_bytes = len(base64_jpeg_data)
                        payload_size_kb = payload_size_bytes / 1024

                        print(f"Generated Base64 JPEG data.")
                        print(f"Final Base64 JPEG payload size: {payload_size_kb:.2f} KB")

                        if payload_size_bytes <= MAX_PAYLOAD_SIZE_BYTES:
                            print(f"✅ Size is within the {MAX_PAYLOAD_SIZE_KB} KB limit.")
                        else:
                            print(f"❌ Warning: Size exceeds the {MAX_PAYLOAD_SIZE_KB} KB limit.")
                        
                        # Print a snippet of the Base64 string
                        print(f"Base64 Snippet: {base64_jpeg_data[:80]}...")

                        # We found and processed an image, so we can exit the loop
                        break 
                    
                    except Exception as e:
                        print(f"An error occurred during image processing: {e}")

    if not base64_jpeg_data:
        print("Could not find or process image data in the response.")
    
    return base64_jpeg_data, jpeg_bytes


# Async main function
async def test_target_features():
    test_cases = [
        ("focused", "coding session"),
        # ("relaxed", "evening wind down"),
        # ("upbeat", "morning routine")
    ]
    
    for mood, activity in test_cases:
        print(f"\n{'='*50}")
        print(f"Mood: {mood.upper()}, Activity: {activity.upper()}")
        target_features = await generate_target_features(mood, activity)
        
        print("\nTargetFeatures:")
        print(f"- acousticness: {target_features.acousticness:.2f}")
        print(f"- danceability: {target_features.danceability:.2f}")
        print(f"- energy: {target_features.energy:.2f}")
        print(f"- instrumentalness: {target_features.instrumentalness:.2f}")
        print(f"- liveness: {target_features.liveness:.2f}")
        print(f"- loudness: {target_features.loudness:.1f} dB")
        print(f"- speechiness: {target_features.speechiness:.2f}")
        print(f"- tempo: {target_features.tempo} BPM")
        print(f"- valence: {target_features.valence:.2f}")

async def test_image():
    """
    Tests the image generation, saves the result locally, and opens it.
    """
    test_quality = 100
    b64_data, img_bytes = await generate_playlist_image(quality=test_quality)
    
    if img_bytes:
        file_name = f"test_generated_image_quality_{test_quality}.jpeg"
        with open(file_name, "wb") as f:
            f.write(img_bytes)
        print(f"\nImage saved locally as '{file_name}'")

        try:
            os.startfile(file_name)
        except Exception as e:
            print(f"Could not automatically display the image: {e}")
            print(f"Please open '{file_name}' manually to view it.")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(test_image())
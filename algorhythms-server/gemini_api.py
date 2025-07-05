import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, cast
import asyncio

# Load environment variables
load_dotenv(dotenv_path='./secrets.env')
gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)

# Define Pydantic models for structured output
class Weights(BaseModel):
    acousticness: float
    danceability: float
    energy: float
    instrumentalness: float
    liveness: float
    loudness: float
    speechiness: float
    tempo: float  # Actual BPM value
    valence: float

class PlaylistExample(BaseModel):
    mood: str
    activity: str
    weights: Weights

# Define examples as structured objects
EXAMPLES: List[PlaylistExample] = [
    PlaylistExample(
        mood="calm",
        activity="studying",
        weights=Weights(
            acousticness=0.8,
            danceability=0.2,
            energy=0.3,
            instrumentalness=0.7,
            liveness=0.1,
            loudness=-20.5,
            speechiness=0.1,
            tempo=75,
            valence=0.6
        )
    ),
    PlaylistExample(
        mood="energetic",
        activity="working out",
        weights=Weights(
            acousticness=0.1,
            danceability=0.9,
            energy=0.95,
            instrumentalness=0.4,
            liveness=0.2,
            loudness=-5.2,
            speechiness=0.2,
            tempo=145,
            valence=0.8
        )
    ),
    PlaylistExample(
        mood="melancholic",
        activity="relaxing",
        weights=Weights(
            acousticness=0.95,
            danceability=0.1,
            energy=0.2,
            instrumentalness=0.6,
            liveness=0.1,
            loudness=-15.0,
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
            f"  Weights: {ex.weights.model_dump()}"
        )
    return "\n\n".join(formatted)

async def generate_weights(mood: str, activity: str) -> Weights:
    """
    Converts mood and activity descriptions into weighted playlist parameters
    using Gemini's structured JSON output.
    
    Args:
        mood: User's emotional state (e.g., "happy", "melancholic")
        activity: Current activity (e.g., "studying", "working out")
    
    Returns:
        Weights: Structured weights for playlist generation
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
    Convert this mood and activity combination into audio feature weights for playlist generation.
    Use the following definitions for each audio feature:
    {feature_definitions}
    
    Return actual BPM for tempo and dB for loudness (not normalized values).

    Mood: "{mood}"
    Activity: "{activity}"

    Examples:
    {format_playlist_examples(EXAMPLES)}
    """
    
    # Wrap synchronous API call in thread
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-lite-preview-06-17",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": Weights,
        }
    )
    
    # Handle response
    if response.parsed:
        return cast(Weights, response.parsed)
    else:
        raise ValueError(f"Failed to parse Gemini response: {response.text}")

# Async main function
async def main():
    test_cases = [
        ("focused", "coding session"),
        # ("relaxed", "evening wind down"),
        # ("upbeat", "morning routine")
    ]
    
    for mood, activity in test_cases:
        print(f"\n{'='*50}")
        print(f"Mood: {mood.upper()}, Activity: {activity.upper()}")
        weights = await generate_weights(mood, activity)
        
        print("\nWeights:")
        print(f"- acousticness: {weights.acousticness:.2f}")
        print(f"- danceability: {weights.danceability:.2f}")
        print(f"- energy: {weights.energy:.2f}")
        print(f"- instrumentalness: {weights.instrumentalness:.2f}")
        print(f"- liveness: {weights.liveness:.2f}")
        print(f"- loudness: {weights.loudness:.1f} dB")
        print(f"- speechiness: {weights.speechiness:.2f}")
        print(f"- tempo: {weights.tempo} BPM")
        print(f"- valence: {weights.valence:.2f}")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
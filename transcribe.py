#!/usr/bin/env python3
"""Minimal podcast transcription using whisper.cpp"""

import json
import os
import subprocess
import urllib.request
from pathlib import Path

# Constants
EXPORT_FILE = "export_20250626_122426.json"
PROCESSED_FILE = "processed_transcripts.json"
TRANSCRIPTS_DIR = Path("transcripts")
WHISPER_CLI = "/Users/douglasvonkohorn/whisper.cpp/build/bin/whisper-cli"
MODEL_PATH = "/Users/douglasvonkohorn/whisper.cpp/models/ggml-medium.en.bin"

def load_episodes():
    """Load unprocessed episodes from export file, sorted chronologically."""
    from datetime import datetime
    
    # Load all episodes
    with open(EXPORT_FILE, 'r') as f:
        all_episodes = json.load(f)
    
    # Parse dates and sort chronologically
    for episode in all_episodes:
        episode['_parsed_date'] = datetime.strptime(
            episode['published_date'], 
            "%a, %d %b %Y %H:%M:%S %z"
        )
    all_episodes.sort(key=lambda x: x['_parsed_date'])
    
    # Load processed episodes
    try:
        with open(PROCESSED_FILE, 'r') as f:
            data = json.load(f)
            processed_guids = {e['guid'] for e in data.get('transcribed', [])}
    except FileNotFoundError:
        processed_guids = set()
    
    # Filter unprocessed episodes with audio URLs (GUID-based only)
    unprocessed = []
    episode_positions = {}  # Track chronological position
    
    for i, episode in enumerate(all_episodes, 1):
        if episode['guid'] not in processed_guids and episode.get('audio_url'):
            unprocessed.append(episode)
            episode_positions[episode['guid']] = i  # Store chronological position
    
    return unprocessed, episode_positions

def transcribe_episode(episode, episode_number):
    """Download and transcribe a single episode."""
    guid = episode['guid']
    title = episode['title']
    audio_url = episode['audio_url']
    
    # Create filename for new episodes (743+)
    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    transcript_name = f"{episode_number}_{clean_title[:100]}.txt"
    
    mp3_file = Path(f"temp_{guid[:8]}.mp3")
    txt_file = TRANSCRIPTS_DIR / transcript_name
    
    try:
        # Download MP3
        print(f"Downloading: {title[:60]}...")
        urllib.request.urlretrieve(audio_url, mp3_file)
        
        # Transcribe with whisper
        print(f"Transcribing: {title[:60]}...")
        # Remove .txt extension from transcript_name for whisper output
        output_base = str(TRANSCRIPTS_DIR / transcript_name.replace('.txt', ''))
        cmd = [
            WHISPER_CLI,
            "-m", MODEL_PATH,
            "-f", str(mp3_file),
            "-otxt",
            "-of", output_base
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and txt_file.exists():
            print(f"✓ Completed: {title[:60]}")
            
            # Update processed file with new entry
            with open(PROCESSED_FILE, 'r') as f:
                data = json.load(f)
            data['transcribed'].append({
                "guid": guid,
                "title": title,
                "transcript_file": transcript_name
            })
            with open(PROCESSED_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        else:
            print(f"✗ Failed: {title[:60]}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Error with {title[:60]}: {e}")
        return False
    
    finally:
        # Clean up MP3
        if mp3_file.exists():
            mp3_file.unlink()

def main():
    """Main transcription loop."""
    # Ensure directories exist
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    
    # Check whisper.cpp exists
    if not Path(WHISPER_CLI).exists():
        print(f"Error: whisper-cli not found at {WHISPER_CLI}")
        return
    
    # Load unprocessed episodes
    episodes, episode_positions = load_episodes()
    print(f"\nFound {len(episodes)} episodes to transcribe")
    
    if not episodes:
        print("All episodes have been transcribed!")
        return
    
    # Process episodes
    success = 0
    failed = 0
    
    for i, episode in enumerate(episodes, 1):
        # Use the chronological position from the full sorted list
        episode_number = episode_positions[episode['guid']]
        print(f"\nProcessing {i}/{len(episodes)} (Episode #{episode_number}):")
        if transcribe_episode(episode, episode_number):
            success += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Transcription complete!")
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    print(f"Total processed: {success + failed}/{len(episodes)}")

if __name__ == "__main__":
    main()
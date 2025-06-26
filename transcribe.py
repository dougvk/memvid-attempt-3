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
    """Load unprocessed episodes from export file."""
    # Load all episodes
    with open(EXPORT_FILE, 'r') as f:
        all_episodes = json.load(f)
    
    # Load processed episodes
    try:
        with open(PROCESSED_FILE, 'r') as f:
            data = json.load(f)
            processed_guids = {e['guid'] for e in data.get('transcribed', [])}
    except FileNotFoundError:
        processed_guids = set()
    
    # Filter unprocessed episodes with audio URLs
    unprocessed = []
    for episode in all_episodes:
        if episode['guid'] not in processed_guids and episode.get('audio_url'):
            # Double-check that transcript doesn't already exist
            guid = episode['guid']
            title = episode['title']
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            
            # Check for existing transcript file
            possible_files = [
                TRANSCRIPTS_DIR / f"{guid}_{clean_title}.txt",
                # Also check for files that might have been created with different naming
            ]
            
            transcript_exists = any(f.exists() for f in possible_files)
            if not transcript_exists:
                unprocessed.append(episode)
            else:
                print(f"Skipping {title[:50]}... (transcript already exists)")
    
    return unprocessed

def transcribe_episode(episode):
    """Download and transcribe a single episode."""
    guid = episode['guid']
    title = episode['title']
    audio_url = episode['audio_url']
    
    # Create clean filename
    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    mp3_file = Path(f"temp_{guid[:8]}.mp3")
    txt_file = TRANSCRIPTS_DIR / f"{guid}_{clean_title}.txt"
    
    try:
        # Download MP3
        print(f"Downloading: {title[:60]}...")
        urllib.request.urlretrieve(audio_url, mp3_file)
        
        # Transcribe with whisper
        print(f"Transcribing: {title[:60]}...")
        cmd = [
            WHISPER_CLI,
            "-m", MODEL_PATH,
            "-f", str(mp3_file),
            "-otxt",
            "-of", str(TRANSCRIPTS_DIR / f"{guid}_{clean_title}")
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and txt_file.exists():
            print(f"✓ Completed: {title[:60]}")
            
            # Update processed file
            with open(PROCESSED_FILE, 'r') as f:
                data = json.load(f)
            data['transcribed'].append({
                "guid": guid,
                "title": title,
                "transcript_file": txt_file.name
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
    episodes = load_episodes()
    print(f"\nFound {len(episodes)} episodes to transcribe")
    
    if not episodes:
        print("All episodes have been transcribed!")
        return
    
    # Process episodes
    success = 0
    failed = 0
    
    for i, episode in enumerate(episodes, 1):
        print(f"\nProcessing {i}/{len(episodes)}:")
        if transcribe_episode(episode):
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
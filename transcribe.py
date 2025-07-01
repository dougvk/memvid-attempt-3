#!/usr/bin/env python3
"""Minimal podcast transcription using whisper.cpp"""

import argparse
import json
import os
import subprocess
import urllib.request
from pathlib import Path

# Default constants
DEFAULT_WHISPER_CLI = "/Users/douglasvonkohorn/whisper.cpp/build/bin/whisper-cli"
DEFAULT_MODEL_PATH = "/Users/douglasvonkohorn/whisper.cpp/models/ggml-medium.bin"

def load_episodes(export_file, processed_file):
    """Load unprocessed episodes from export file, sorted chronologically."""
    from datetime import datetime
    
    # Load all episodes
    with open(export_file, 'r') as f:
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
        with open(processed_file, 'r') as f:
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

def transcribe_episode(episode, episode_number, transcripts_dir, processed_file, whisper_cli, model_path):
    """Download and transcribe a single episode."""
    guid = episode['guid']
    title = episode['title']
    audio_url = episode['audio_url']
    
    # Create filename for new episodes
    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    transcript_name = f"{episode_number}_{clean_title[:100]}.txt"
    
    mp3_file = Path(f"temp_{guid[:8]}.mp3")
    txt_file = transcripts_dir / transcript_name
    
    try:
        # Download MP3
        print(f"Downloading: {title[:60]}...")
        urllib.request.urlretrieve(audio_url, mp3_file)
        
        # Transcribe with whisper
        print(f"Transcribing: {title[:60]}...")
        # Remove .txt extension from transcript_name for whisper output
        output_base = str(transcripts_dir / transcript_name.replace('.txt', ''))
        cmd = [
            whisper_cli,
            "-m", model_path,
            "-f", str(mp3_file),
            "-l", "auto",  # Force auto-detection
            "-otxt",
            "-of", output_base
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and txt_file.exists():
            print(f"✓ Completed: {title[:60]}")
            
            # Update processed file with new entry
            with open(processed_file, 'r') as f:
                data = json.load(f)
            data['transcribed'].append({
                "guid": guid,
                "title": title,
                "transcript_file": transcript_name
            })
            with open(processed_file, 'w') as f:
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
    parser = argparse.ArgumentParser(description="Transcribe podcast episodes using whisper.cpp")
    parser.add_argument('--export-file', required=True, help='Export JSON file from rss_manager')
    parser.add_argument('--output-dir', default='transcripts', help='Output directory for transcripts')
    parser.add_argument('--processed-file', help='Track processed episodes (auto-generated if not specified)')
    parser.add_argument('--whisper-cli', default=DEFAULT_WHISPER_CLI, help='Path to whisper-cli executable')
    parser.add_argument('--model-path', default=DEFAULT_MODEL_PATH, help='Path to whisper model file')
    
    args = parser.parse_args()
    
    # Set up paths
    export_file = Path(args.export_file)
    transcripts_dir = Path(args.output_dir)
    
    # Auto-generate processed file name if not specified
    if args.processed_file:
        processed_file = Path(args.processed_file)
    else:
        # Use output dir name as base
        processed_file = Path(f"{transcripts_dir.name}_processed.json")
    
    # Ensure directories exist
    transcripts_dir.mkdir(exist_ok=True)
    
    # Check whisper.cpp exists
    if not Path(args.whisper_cli).exists():
        print(f"Error: whisper-cli not found at {args.whisper_cli}")
        return
    
    # Check export file exists
    if not export_file.exists():
        print(f"Error: Export file not found: {export_file}")
        return
    
    # Initialize processed file if it doesn't exist
    if not processed_file.exists():
        with open(processed_file, 'w') as f:
            json.dump({"transcribed": []}, f, indent=2)
        print(f"Created new processed file: {processed_file}")
    
    # Load unprocessed episodes
    episodes, episode_positions = load_episodes(export_file, processed_file)
    print(f"\nFound {len(episodes)} episodes to transcribe")
    print(f"Output directory: {transcripts_dir}")
    print(f"Tracking file: {processed_file}")
    
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
        if transcribe_episode(episode, episode_number, transcripts_dir, processed_file, 
                            args.whisper_cli, args.model_path):
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
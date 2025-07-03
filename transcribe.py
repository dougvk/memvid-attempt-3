#!/usr/bin/env python3
"""Minimal podcast transcription using whisper.cpp"""

import argparse
import json
import os
import subprocess
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

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

def transcribe_episode(episode, episode_number, transcripts_dir, processed_file, whisper_cli, model_path, args):
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
        original_size = mp3_file.stat().st_size
        print(f"  Downloaded: {original_size/1024/1024:.1f}MB")
        
        # Pre-process: silence removal + 2x speed + mono, 16kHz, 64kbps
        print(f"Processing: {title[:60]}...")
        print(f"  Applying: silence removal + 2x speed + mono 16kHz 64kbps")
        processed = mp3_file.with_suffix('.processed.mp3')
        result = subprocess.run([
            'ffmpeg', '-i', str(mp3_file),
            '-map', '0:a',  # Only process audio streams (ignore embedded artwork)
            '-af', (
                'silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB:'
                'stop_periods=-1:stop_duration=0.02:stop_threshold=-50dB,'
                'apad=pad_dur=0.02,'
                'atempo=2.0'
            ),
            '-ac', '1', '-ar', '16000',
            '-c:a', 'libmp3lame', '-b:a', '64k',
            '-y', str(processed)
        ], capture_output=True)
        if result.returncode != 0:
            raise Exception(f"ffmpeg preprocessing failed: {result.stderr.decode()[:500]}")
        
        processed_size = processed.stat().st_size
        reduction = (1 - processed_size/original_size) * 100
        print(f"  Processed: {processed_size/1024/1024:.1f}MB ({reduction:.0f}% reduction)")
        
        # Transcribe
        print(f"Transcribing: {title[:60]}...")
        
        if args.use_openai_transcribe:
            # OpenAI path
            try:
                import openai
                import tiktoken
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
                # Check processed file size
                file_size = processed.stat().st_size
                if file_size > 24 * 1024 * 1024:  # 24MB threshold
                    print(f"  File still large ({file_size/1024/1024:.1f}MB), chunking...")
                    
                    # Get bitrate and calculate safe segment duration
                    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 
                                          'format=bit_rate', '-of', 'csv=p=0', str(processed)],
                                         capture_output=True, text=True, check=True)
                    bitrate = int(probe.stdout.strip())
                    segment_duration = (24 * 1024 * 1024 * 8) // bitrate - 2  # 24MB in bits, minus 2s margin
                    
                    # Segment without overlap (we'll handle context via prompts)
                    chunk_pattern = str(processed.with_suffix('')) + '_%03d.mp3'
                    result = subprocess.run([
                        'ffmpeg', '-i', str(processed), '-f', 'segment',
                        '-segment_time', str(segment_duration),
                        '-reset_timestamps', '1', '-c', 'copy', chunk_pattern
                    ], capture_output=True)
                    if result.returncode != 0:
                        raise Exception(f"ffmpeg segmentation failed: {result.stderr.decode()[:500]}")
                    
                    # Transcribe chunks with context passing
                    chunks = sorted(processed.parent.glob(f"{processed.stem}_*.mp3"))
                    print(f"  Created {len(chunks)} chunks (~{segment_duration}s each)")
                    transcriptions = []
                    last_tail = ""
                    
                    # Initialize tokenizer for whisper model (uses gpt2 encoding)
                    enc = tiktoken.get_encoding("gpt2")
                    
                    for i, chunk in enumerate(chunks, 1):
                        print(f"  Transcribing chunk {i}/{len(chunks)}...")
                        try:
                            with open(chunk, 'rb') as f:
                                # Pass last 200 tokens as prompt (not characters)
                                if last_tail:
                                    tail_tokens = enc.encode(last_tail)[-200:]
                                    prompt = enc.decode(tail_tokens)
                                else:
                                    prompt = ""
                                
                                response = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=f,
                                    prompt=prompt
                                )
                            transcriptions.append(response.text)
                            last_tail = response.text  # Save for next chunk's prompt
                        finally:
                            chunk.unlink()
                    
                    # Write successful transcription
                    txt_file.write_text(' '.join(transcriptions))
                    transcription_success = True
                else:
                    # File is small enough, process normally
                    print(f"  Using OpenAI Whisper API directly")
                    with open(processed, 'rb') as audio_file:
                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )
                    txt_file.write_text(response.text)
                    transcription_success = True
                    
            except Exception as e:
                print(f"  OpenAI Error: {str(e)[:200]}")
                transcription_success = False
        else:
            # Local whisper.cpp code  
            print(f"  Using local whisper.cpp")
            print(f"  Model: {model_path.split('/')[-1]}")
            output_base = str(transcripts_dir / transcript_name.replace('.txt', ''))
            cmd = [
                whisper_cli,
                "-m", model_path,
                "-f", str(processed),  # Use preprocessed file
                "-l", "auto",  # Force auto-detection
                "-otxt",
                "-of", output_base
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            transcription_success = result.returncode == 0 and txt_file.exists()
            if not transcription_success and result.stderr:
                print(f"  Error: {result.stderr[:200]}")
        
        if transcription_success:
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
            return False
            
    except Exception as e:
        print(f"✗ Error with {title[:60]}: {e}")
        return False
    
    finally:
        # Clean up files
        if mp3_file.exists():
            mp3_file.unlink()
        if 'processed' in locals() and processed.exists():
            processed.unlink()

def main():
    """Main transcription loop."""
    parser = argparse.ArgumentParser(description="Transcribe podcast episodes using whisper.cpp")
    parser.add_argument('--export-file', required=True, help='Export JSON file from rss_manager')
    parser.add_argument('--output-dir', default='transcripts', help='Output directory for transcripts')
    parser.add_argument('--processed-file', help='Track processed episodes (auto-generated if not specified)')
    parser.add_argument('--whisper-cli', default=DEFAULT_WHISPER_CLI, help='Path to whisper-cli executable')
    parser.add_argument('--model-path', default=DEFAULT_MODEL_PATH, help='Path to whisper model file')
    parser.add_argument('--use-openai-transcribe', action='store_true', help='Use OpenAI API instead of local whisper')
    
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
    
    # Check requirements based on mode
    if args.use_openai_transcribe:
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not set in environment")
            return
    else:
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
                            args.whisper_cli, args.model_path, args):
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
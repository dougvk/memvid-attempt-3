#!/usr/bin/env python3
"""Minimal RSS feed manager for podcast processing."""

import os
import sys
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
STATE_FILE = "state.json"

# Taxonomy - exact copy from original codebase
TAXONOMY = {
    "Format": [
        "Series Episodes",
        "Standalone Episodes",
        "RIHC Series"
    ],
    "Theme": [
        "Ancient & Classical Civilizations",
        "Medieval & Renaissance Europe",
        "Empire, Colonialism & Exploration",
        "Modern Political History & Leadership",
        "Military History & Battles",
        "Cultural, Social & Intellectual History",
        "Science, Technology & Economic History",
        "Religious, Ideological & Philosophical History",
        "Historical Mysteries, Conspiracies & Scandals",
        "Regional & National Histories"
    ],
    "Track": [
        "Roman Track",
        "Medieval & Renaissance Track",
        "Colonialism & Exploration Track",
        "American History Track",
        "Military & Battles Track",
        "Modern Political History Track",
        "Cultural & Social History Track",
        "Science, Technology & Economic History Track",
        "Religious & Ideological History Track",
        "Historical Mysteries & Conspiracies Track",
        "British History Track",
        "Global Empires Track",
        "World Wars Track",
        "Ancient Civilizations Track",
        "Regional Spotlight: Latin America Track",
        "Regional Spotlight: Asia & the Middle East Track",
        "Regional Spotlight: Europe Track",
        "Regional Spotlight: Africa Track",
        "Historical Figures Track",
        "The RIHC Bonus Track",
        "Archive Editions Track",
        "Contemporary Issues Through History Track"
    ]
}


def load_state() -> Dict[str, Any]:
    """Load state from JSON file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"episodes": {}}


def save_state(state: Dict[str, Any]) -> None:
    """Save state to JSON file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def ingest() -> None:
    """Fetch RSS feed and merge new episodes with existing state."""
    if not RSS_FEED_URL:
        print("Error: RSS_FEED_URL not set in environment")
        sys.exit(1)
    
    print(f"Fetching feed from {RSS_FEED_URL}...")
    response = requests.get(RSS_FEED_URL, timeout=30)
    response.raise_for_status()
    
    # Parse RSS feed
    root = ET.fromstring(response.content)
    channel = root.find('.//channel')
    if channel is None:
        print("Error: No channel found in RSS feed")
        sys.exit(1)
    
    # Load existing state
    state = load_state()
    episodes = state.get("episodes", {})
    
    # Process episodes
    new_count = 0
    for item in channel.findall('item'):
        guid_elem = item.find('guid')
        if guid_elem is None or not guid_elem.text:
            continue
        
        guid = guid_elem.text.strip()
        
        # Skip if already ingested
        if guid in episodes:
            continue
        
        # Extract episode data
        title = item.find('title')
        description = item.find('description')
        pub_date = item.find('pubDate')
        
        episodes[guid] = {
            "guid": guid,
            "title": title.text if title is not None else "",
            "description": description.text if description is not None else "",
            "published_date": pub_date.text if pub_date is not None else "",
            "cleaned_description": None,
            "tags": None,
            "ingested_at": datetime.now().isoformat()
        }
        new_count += 1
    
    # Save updated state
    state["episodes"] = episodes
    save_state(state)
    
    print(f"Ingested {new_count} new episodes. Total: {len(episodes)}")


def clean() -> None:
    """Clean HTML from episode descriptions."""
    state = load_state()
    episodes = state.get("episodes", {})
    
    cleaned_count = 0
    for guid, episode in episodes.items():
        # Skip if already cleaned
        if episode.get("cleaned_description") is not None:
            continue
        
        # Simple HTML cleaning
        text = episode.get("description", "")
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', text)
        # Decode HTML entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        # Clean whitespace
        text = ' '.join(text.split())
        
        episode["cleaned_description"] = text
        episode["cleaned_at"] = datetime.now().isoformat()
        cleaned_count += 1
    
    save_state(state)
    print(f"Cleaned {cleaned_count} episodes")


def construct_prompt(title: str, description: str) -> str:
    """Construct prompt for OpenAI - exact copy from original."""
    taxonomy_text = "\nValid tags by category (an episode can have multiple tags from each category):\n"
    for category, tags in TAXONOMY.items():
        taxonomy_text += f"\n{category}:\n"
        taxonomy_text += "\n".join(f"- {tag}" for tag in tags) + "\n"
    
    prompt = f"""You are a history podcast episode tagger. Your task is to analyze this episode and assign ALL relevant tags from the taxonomy below.

Episode Title: {title}
Episode Description: {description}

IMPORTANT RULES:
1. An episode MUST be tagged as "Series Episodes" if ANY of these are true:
   - The title contains "(Ep X)" or "(Part X)" where X is any number
   - The title contains "Part" followed by a number
   - The episode is part of a named series (e.g. "Young Churchill", "The French Revolution")
2. An episode MUST be tagged as "RIHC Series" if the title starts with "RIHC:"
   - RIHC episodes should ALWAYS have both "RIHC Series" and "Series Episodes" in their Format tags
3. An episode can and should have multiple tags from each category if applicable
4. If none of the above rules apply, tag it as "Standalone Episodes"
5. For series episodes, you MUST extract the episode number:
   - Look for patterns like "(Ep X)", "(Part X)", "Part X", where X is a number
   - Include the number in your response as "episode_number"
   - If no explicit number is found, use null for episode_number

{taxonomy_text}

IMPORTANT:
1. You MUST ONLY use tags EXACTLY as they appear in the taxonomy above
2. You MUST include Format, Theme, Track, and episode_number in your response
3. Make sure themes and tracks are from their correct categories (don't use track names as themes)
4. For Theme and Track:
   - Apply ALL relevant themes and tracks that match the content
   - It's common for an episode to have 2-3 themes and 2-3 tracks
   - Make sure themes and tracks are from their correct categories (don't use track names as themes)

Example responses:

For a RIHC episode about ancient Rome and military history:
{{"Format": ["RIHC Series", "Series Episodes"], "Theme": ["Ancient & Classical Civilizations", "Military History & Battles"], "Track": ["Roman Track", "Military & Battles Track", "The RIHC Bonus Track"], "episode_number": null}}

For a standalone episode about British history:
{{"Format": ["Standalone Episodes"], "Theme": ["Regional & National Histories", "Modern Political History & Leadership"], "Track": ["British History Track", "Modern Political History Track"], "episode_number": null}}

For part 3 of a series about Napoleon:
{{"Format": ["Series Episodes"], "Theme": ["Modern Political History & Leadership", "Military History & Battles"], "Track": ["Modern Political History Track", "Military & Battles Track", "Historical Figures Track"], "episode_number": 3}}

Return tags in this exact JSON format:
{{"Format": ["tag1", "tag2"], "Theme": ["tag1", "tag2"], "Track": ["tag1", "tag2"], "episode_number": number_or_null}}
"""
    return prompt


def tag() -> None:
    """Tag episodes using OpenAI."""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not set in environment")
        sys.exit(1)
    
    try:
        import openai
    except ImportError:
        print("Error: openai package not installed. Run: pip install openai")
        sys.exit(1)
    
    state = load_state()
    episodes = state.get("episodes", {})
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    tagged_count = 0
    for guid, episode in episodes.items():
        # Skip if already tagged or not cleaned
        if episode.get("tags") is not None:
            continue
        if episode.get("cleaned_description") is None:
            continue
        
        title = episode.get("title", "")
        description = episode.get("cleaned_description", "")
        
        print(f"Tagging: {title[:60]}...")
        
        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a history podcast episode tagger."},
                    {"role": "user", "content": construct_prompt(title, description)}
                ],
                temperature=0.0,
                timeout=30
            )
            
            content = response.choices[0].message.content
            if content:
                # Parse JSON response
                tags = json.loads(content)
                episode["tags"] = tags
                episode["tagged_at"] = datetime.now().isoformat()
                tagged_count += 1
                
        except Exception as e:
            print(f"Error tagging episode: {e}")
            continue
    
    save_state(state)
    print(f"Tagged {tagged_count} episodes")


def export() -> None:
    """Export tagged episodes to JSON."""
    state = load_state()
    episodes = state.get("episodes", {})
    
    # Filter tagged episodes
    tagged_episodes = []
    for episode in episodes.values():
        if episode.get("tags") is not None:
            tagged_episodes.append({
                "guid": episode["guid"],
                "title": episode["title"],
                "published_date": episode["published_date"],
                "tags": episode["tags"],
                "cleaned_description": episode["cleaned_description"]
            })
    
    # Sort by published date
    tagged_episodes.sort(key=lambda x: x["published_date"], reverse=True)
    
    # Export to JSON
    output_file = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(tagged_episodes, f, indent=2)
    
    print(f"Exported {len(tagged_episodes)} episodes to {output_file}")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python rss_manager.py [ingest|clean|tag|export]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "ingest":
        ingest()
    elif command == "clean":
        clean()
    elif command == "tag":
        tag()
    elif command == "export":
        export()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: ingest, clean, tag, export")
        sys.exit(1)


if __name__ == "__main__":
    main()
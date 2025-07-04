#!/usr/bin/env python3
"""Minimal RSS feed manager for podcast processing."""

import os
import sys
import json
import re
import random
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
OPENAI_MODEL = "gpt-4.1-mini"
STATE_FILE = "state.json"

# Taxonomy - exact copy from original codebase
# Default taxonomy for The Rest is History podcast
DEFAULT_TAXONOMY = {
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


def load_taxonomy() -> Dict[str, List[str]]:
    """Load taxonomy from file or use default."""
    if os.path.exists("taxonomy.json"):
        with open("taxonomy.json", 'r') as f:
            return json.load(f)
    return DEFAULT_TAXONOMY


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
        
        # Get audio URL from enclosure
        audio_url = None
        enclosure = item.find('enclosure')
        if enclosure is not None and 'url' in enclosure.attrib:
            audio_url = enclosure.attrib['url']
        
        episodes[guid] = {
            "guid": guid,
            "title": title.text if title is not None else "",
            "description": description.text if description is not None else "",
            "published_date": pub_date.text if pub_date is not None else "",
            "audio_url": audio_url,
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
    """Clean episode descriptions using OpenAI."""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not set in environment")
        sys.exit(1)
    
    try:
        import openai
        from concurrent.futures import ThreadPoolExecutor, as_completed
    except ImportError:
        print("Error: openai package not installed. Run: pip install openai")
        sys.exit(1)
    
    state = load_state()
    episodes = state.get("episodes", {})
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    # Collect episodes to clean
    to_clean = []
    for guid, episode in episodes.items():
        if episode.get("cleaned_description") is None:
            to_clean.append(guid)
    
    if not to_clean:
        print("No episodes to clean")
        return
    
    print(f"Cleaning {len(to_clean)} episodes...")
    
    def clean_episode(guid):
        episode = episodes[guid]
        title = episode.get("title", "")
        description = episode.get("description", "")
        
        # First do basic HTML cleaning
        text = re.sub('<[^<]+?>', '', description)
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        text = ' '.join(text.split())
        
        try:
            # Call OpenAI API for intelligent cleaning
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": """You are a content cleaner for podcast episode descriptions. 
                Remove all promotional content, advertisements, social media links, and production credits.
                Keep only the historical content and episode summary.
                Preserve the original writing style and tone.
                Do not add any new content or modify the historical information.
                Pay special attention to content that matches or relates to the episode title."""},
                    {"role": "user", "content": f"Clean this episode description for episode titled '{title}':\n\n{text}"}
                ],
                temperature=0.0,
                timeout=30
            )
            
            cleaned_text = response.choices[0].message.content.strip()
            return (guid, cleaned_text, None)
            
        except Exception as e:
            return (guid, text, e)
    
    cleaned_count = 0
    
    # Process in batches of 10
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(0, len(to_clean), 10):
            batch = to_clean[i:i+10]
            
            # Submit batch
            futures = {executor.submit(clean_episode, guid): guid for guid in batch}
            
            # Collect results
            for future in as_completed(futures):
                guid, cleaned_text, error = future.result()
                episode = episodes[guid]
                title = episode.get("title", "")[:60]
                
                if error:
                    print(f"✗ {title}: {error}")
                else:
                    print(f"✓ {title}")
                
                episode["cleaned_description"] = cleaned_text
                episode["cleaned_at"] = datetime.now().isoformat()
                cleaned_count += 1
            
            # Save after each batch
            state["episodes"] = episodes
            save_state(state)
            print(f"  Batch saved ({cleaned_count}/{len(to_clean)})")
    
    print(f"Total cleaned: {cleaned_count} episodes")


def construct_prompt(title: str, description: str) -> str:
    """Construct prompt for OpenAI - exact copy from original."""
    taxonomy = load_taxonomy()
    taxonomy_text = "\nValid tags by category (an episode can have multiple tags from each category):\n"
    for category, tags in taxonomy.items():
        taxonomy_text += f"\n{category}:\n"
        taxonomy_text += "\n".join(f"- {tag}" for tag in tags) + "\n"
    
    prompt = f"""You are a history podcast episode tagger. Your task is to analyze this episode and assign ALL relevant tags from the taxonomy below.

IMPORTANT: All tags must be in the same language as the episode title and description. Do not translate tags to English.

Episode Title: {title}
Episode Description: {description}

IMPORTANT RULES:
1. Select 1-3 Format tags based on the episode structure
2. Select 1-3 Theme tags that best describe the main subjects
3. Select 1-3 Track tags for specific topics covered
4. If the episode is part of a numbered series, extract the episode number
5. ONLY use tags that exist in the taxonomy below

{taxonomy_text}

CATEGORY GUIDELINES:
- Format: The structure or type of the episode (e.g., discussion, interview, tasting)
- Theme: Broad subject areas and general topics (what the episode is broadly about)
- Track: Specific topics, grape varieties, or detailed subjects covered

Be careful not to confuse Theme and Track - use the exact category each tag appears in above.

WARNING: You MUST NOT create or invent any tags. If a grape variety, topic, or format is not listed in the taxonomy above, DO NOT use it. Only use tags that EXACTLY match those in the taxonomy.

LANGUAGE: The taxonomy tags are in the same language as the podcast. Use these tags exactly as written - do not translate them to another language.

IMPORTANT:
1. You MUST ONLY use tags EXACTLY as they appear in the taxonomy above
2. You MUST include Format, Theme, Track, and episode_number in your response
3. You MUST select at least 1 tag from each category (Format, Theme, Track) - never return empty arrays
4. If no tags seem perfectly relevant, choose the closest/most general option from that category
5. Make sure themes and tracks are from their correct categories (don't use track names as themes)
6. For Theme and Track:
   - Apply ALL relevant themes and tracks that match the content
   - It's common for an episode to have 2-3 themes and 2-3 tracks
   - Make sure themes and tracks are from their correct categories (don't use track names as themes)

Example format:
{{"Format": ["format_tag1"], "Theme": ["theme_tag1", "theme_tag2"], "Track": ["track_tag1", "track_tag2"], "episode_number": null}}

BEFORE OUTPUTTING: Double-check that:
- Every Format tag exists in the Format category above
- Every Theme tag exists in the Theme category above  
- Every Track tag exists in the Track category above
- You have NOT invented any new tags

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
        from concurrent.futures import ThreadPoolExecutor, as_completed
    except ImportError:
        print("Error: openai package not installed. Run: pip install openai")
        sys.exit(1)
    
    state = load_state()
    episodes = state.get("episodes", {})
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    # Collect episodes to tag
    to_tag = []
    for guid, episode in episodes.items():
        if episode.get("tags") is None and episode.get("cleaned_description") is not None:
            to_tag.append(guid)
    
    if not to_tag:
        print("No episodes to tag")
        return
    
    print(f"Tagging {len(to_tag)} episodes...")
    
    def tag_episode(guid):
        episode = episodes[guid]
        title = episode.get("title", "")
        description = episode.get("cleaned_description", "")
        
        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a podcast episode tagger. Always use tags exactly as they appear in the provided taxonomy."},
                    {"role": "user", "content": construct_prompt(title, description)}
                ],
                temperature=0.0,
                timeout=30
            )
            
            content = response.choices[0].message.content
            if content:
                # Parse JSON response
                tags = json.loads(content)
                return (guid, tags, None)
            return (guid, None, "Empty response")
                
        except Exception as e:
            return (guid, None, e)
    
    tagged_count = 0
    
    # Process in batches of 10
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(0, len(to_tag), 10):
            batch = to_tag[i:i+10]
            
            # Submit batch
            futures = {executor.submit(tag_episode, guid): guid for guid in batch}
            
            # Collect results
            for future in as_completed(futures):
                guid, tags, error = future.result()
                episode = episodes[guid]
                title = episode.get("title", "")[:60]
                
                if error:
                    print(f"✗ {title}: {error}")
                else:
                    print(f"✓ {title}")
                    episode["tags"] = tags
                    episode["tagged_at"] = datetime.now().isoformat()
                    tagged_count += 1
            
            # Save after each batch
            state["episodes"] = episodes
            save_state(state)
            print(f"  Batch saved ({tagged_count}/{len(to_tag)})")
    
    print(f"Total tagged: {tagged_count} episodes")


def validate_episode_tags(tags: Dict[str, Any], taxonomy: Dict[str, List[str]]) -> List[str]:
    """Validate tags for a single episode. Returns list of errors."""
    errors = []
    
    # Check required fields
    required = {"Format", "Theme", "Track", "episode_number"}
    missing = required - set(tags.keys())
    if missing:
        errors.append(f"Missing fields: {missing}")
    
    # Validate each category
    for category in ["Format", "Theme", "Track"]:
        if category in tags:
            cat_tags = tags[category]
            if not isinstance(cat_tags, list):
                errors.append(f"{category} must be a list")
            else:
                invalid_tags = set(cat_tags) - set(taxonomy[category])
                if invalid_tags:
                    errors.append(f"Invalid {category} tags: {invalid_tags}")
                if not cat_tags:  # Empty list
                    errors.append(f"{category} cannot be empty")
    
    # Validate episode_number
    if "episode_number" in tags:
        num = tags["episode_number"]
        if num is not None and not isinstance(num, int):
            errors.append("episode_number must be int or null")
    
    return errors


def validate() -> None:
    """Validate tags against taxonomy rules."""
    state = load_state()
    episodes = state.get("episodes", {})
    taxonomy = load_taxonomy()
    
    valid_count = 0
    invalid_count = 0
    errors = []
    
    for guid, episode in episodes.items():
        tags = episode.get("tags")
        if tags is None:
            continue
        
        title = episode.get("title", "")[:60]
        episode_errors = validate_episode_tags(tags, taxonomy)
        
        if episode_errors:
            errors.append(f"{title}: {'; '.join(episode_errors)}")
            invalid_count += 1
        else:
            valid_count += 1
    
    print(f"Valid episodes: {valid_count}")
    print(f"Invalid episodes: {invalid_count}")
    if errors:
        print("\nValidation errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")


def fix() -> None:
    """Fix common validation errors in tags."""
    state = load_state()
    episodes = state.get("episodes", {})
    taxonomy = load_taxonomy()
    
    fixed_count = 0
    fixes_made = []
    
    for guid, episode in episodes.items():
        tags = episode.get("tags")
        if tags is None:
            continue
        
        title = episode.get("title", "")[:60]
        episode_fixes = []
        
        # Fix missing required fields
        if "episode_number" not in tags:
            tags["episode_number"] = None
            episode_fixes.append("added episode_number")
        
        for category in ["Format", "Theme", "Track"]:
            if category not in tags:
                tags[category] = []
                episode_fixes.append(f"added empty {category}")
        
        # Fix Format issues
        if "Format" in tags:
            formats = tags["Format"]
            if not isinstance(formats, list):
                formats = [formats] if isinstance(formats, str) else ["Standalone Episodes"]
                tags["Format"] = formats
                episode_fixes.append("converted Format to list")
            
            # Multiple formats are now allowed - no fix needed
            
            # Remove invalid Format tags
            valid_formats = [f for f in formats if f in taxonomy["Format"]]
            if len(valid_formats) != len(formats):
                tags["Format"] = valid_formats if valid_formats else ["Standalone Episodes"]
                episode_fixes.append("removed invalid Format tags")
        
        # Fix Theme and Track
        for category in ["Theme", "Track"]:
            if category in tags:
                cat_tags = tags[category]
                if not isinstance(cat_tags, list):
                    tags[category] = [cat_tags] if isinstance(cat_tags, str) else []
                    episode_fixes.append(f"converted {category} to list")
                else:
                    # Remove invalid tags
                    valid_tags = [t for t in cat_tags if t in taxonomy[category]]
                    if len(valid_tags) != len(cat_tags):
                        tags[category] = valid_tags
                        episode_fixes.append(f"removed invalid {category} tags")
        
        # Fix episode_number type
        if "episode_number" in tags:
            num = tags["episode_number"]
            if isinstance(num, str) and num.isdigit():
                tags["episode_number"] = int(num)
                episode_fixes.append("converted episode_number to int")
            elif num is not None and not isinstance(num, int):
                tags["episode_number"] = None
                episode_fixes.append("reset invalid episode_number")
        
        # After all fixes, validate and delete if still invalid
        if tags:
            validation_errors = validate_episode_tags(tags, taxonomy)
            if validation_errors:
                episode.pop("tags", None)
                episode.pop("tagged_at", None)
                episode_fixes = ["DELETED ALL TAGS - validation failed after fixes: " + "; ".join(validation_errors)]
        
        if episode_fixes:
            fixes_made.append(f"{title}: {', '.join(episode_fixes)}")
            fixed_count += 1
    
    save_state(state)
    
    print(f"Fixed {fixed_count} episodes")
    if fixes_made:
        print("\nFixes applied:")
        for fix in fixes_made[:10]:
            print(f"  - {fix}")
        if len(fixes_made) > 10:
            print(f"  ... and {len(fixes_made) - 10} more")


def generate_taxonomy() -> None:
    """Generate taxonomy for this podcast using OpenAI."""
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
    
    # Collect all cleaned descriptions
    descriptions = []
    for episode in episodes.values():
        if desc := episode.get("cleaned_description"):
            descriptions.append({
                "title": episode.get("title", ""),
                "description": desc
            })
    
    if not descriptions:
        print("Error: No cleaned descriptions found. Run 'clean' command first.")
        sys.exit(1)
    
    print(f"Found {len(descriptions)} episodes with cleaned descriptions")
    
    # Randomly shuffle to ensure diverse sampling
    random.shuffle(descriptions)
    
    # Build episodes text while tracking tokens
    episodes_text = ""
    token_count = 0
    episodes_included = 0
    
    # Reserve ~20k tokens for prompt template and response
    MAX_CONTENT_TOKENS = 400000
    
    for ep in descriptions:
        # Format episode
        episode_entry = f"Title: {ep['title']}\nDescription: {ep['description']}\n\n"
        
        # Rough token estimate (1 token ≈ 4 characters)
        entry_tokens = len(episode_entry) // 4
        
        # Check if adding this would exceed limit
        if token_count + entry_tokens > MAX_CONTENT_TOKENS:
            break
            
        episodes_text += episode_entry
        token_count += entry_tokens
        episodes_included += 1
    
    print(f"Including {episodes_included} episodes (~{token_count:,} tokens) in taxonomy generation")
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""Analyze these podcast episodes to create a MINIMAL but COMPREHENSIVE taxonomy.

IMPORTANT: Generate all category values in the same language as the podcast episodes.

YOUR TASK:
1. Read ALL episodes carefully
2. Identify the core patterns and recurring topics
3. Create the SMALLEST possible set of tags that can categorize EVERY episode
4. Avoid overly specific tags - prefer broader categories that can cover multiple related topics

TAXONOMY REQUIREMENTS:
- Format: 3-7 types (how episodes are structured - interviews, discussions, solo, series, etc.)
- Theme: 5-8 broad subject areas that capture the main topics of this podcast
- Track: 8-15 specific recurring topics or subtopics

QUALITY CRITERIA:
✓ Every episode MUST fit into at least one tag from each category
✓ Prefer fewer, broader tags over many specific ones
✓ Merge similar concepts into single tags
✓ Ensure tags are mutually exclusive where possible
✓ Tags should be reusable across many episodes
✓ Include a general/catch-all option if needed for outlier episodes

PROCESS:
1. First, identify ALL topics and formats across the episodes
2. Group similar topics together
3. Create broader categories that encompass these groups
4. Verify that EVERY episode can be tagged with your taxonomy
5. Consolidate and remove redundant tags
6. Ensure no episode would be left without appropriate tags

PODCAST EPISODES ({episodes_included} of {len(descriptions)} total):
{episodes_text}

Based on this analysis, return a MINIMAL taxonomy where EVERY episode can be properly categorized.

Return ONLY a JSON object in this exact format:
{{
    "Format": ["format1", "format2", ...],
    "Theme": ["theme1", "theme2", ...],
    "Track": ["track1", "track2", ...]
}}"""
    
    print("Calling OpenAI to generate taxonomy...")
    
    try:
        # Call OpenAI with a better model for this task
        response = client.chat.completions.create(
            model="o3-mini",  # Use thinking model for better taxonomy generation
            messages=[
                {"role": "system", "content": "You are an expert at creating minimal, efficient taxonomies for any type of podcast. Your goal is to create the smallest possible set of categories that can accurately classify 100% of the episodes. Think strategically about grouping and consolidation. Every episode must fit somewhere."},
                {"role": "user", "content": prompt}
            ],
            timeout=300  # 5 minutes for thinking model
        )
        
        content = response.choices[0].message.content
        if content:
            # Strip markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()
            
            # Parse JSON response
            taxonomy = json.loads(content)
            
            # Save to file
            with open("taxonomy.json", "w") as f:
                json.dump(taxonomy, f, indent=2)
            
            print(f"✓ Taxonomy generated and saved to taxonomy.json")
            print("\nGenerated Taxonomy:")
            for category, tags in taxonomy.items():
                print(f"\n{category}:")
                for tag in tags:
                    print(f"  - {tag}")
        else:
            print("Error: Empty response from OpenAI")
            
    except json.JSONDecodeError as e:
        print(f"Error parsing OpenAI response as JSON: {e}")
        print(f"Response: {content[:500]}...")
    except Exception as e:
        print(f"Error generating taxonomy: {e}")


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
                "audio_url": episode.get("audio_url"),
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
        print("Usage: python rss_manager.py [ingest|clean|generate-taxonomy|tag|validate|fix|export]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "ingest":
        ingest()
    elif command == "clean":
        clean()
    elif command == "generate-taxonomy":
        generate_taxonomy()
    elif command == "tag":
        tag()
    elif command == "validate":
        validate()
    elif command == "fix":
        fix()
    elif command == "export":
        export()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: ingest, clean, generate-taxonomy, tag, validate, fix, export")
        sys.exit(1)


if __name__ == "__main__":
    main()
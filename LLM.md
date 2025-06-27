# LLM Integration Guide for Memvid

This guide covers how to use Large Language Models (LLMs) with memvid for chatting with your video-encoded knowledge base.

## Quick Start

```bash
# Set your API key
export OPENAI_API_KEY="sk-your-api-key-here"

# Chat with existing memory
python3 file_chat.py --load-existing output/your_memory --provider openai --model gpt-4o
```

## Supported LLM Providers

Memvid supports three major LLM providers:

| Provider | Default Model | Environment Variable |
|----------|--------------|---------------------|
| OpenAI | gpt-4o | OPENAI_API_KEY |
| Google | gemini-2.0-flash-exp | GOOGLE_API_KEY |
| Anthropic | claude-3-5-sonnet-20241022 | ANTHROPIC_API_KEY |

## Setting API Keys

### Method 1: Environment Variables (Recommended)

```bash
# OpenAI
export OPENAI_API_KEY="sk-your-api-key-here"

# Google
export GOOGLE_API_KEY="your-google-api-key-here"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"

# Add to shell profile for persistence
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Method 2: Direct in Python Code

```python
from memvid import MemvidChat

chat = MemvidChat(
    video_file="output/your_video.mkv",
    index_file="output/your_index.json",
    llm_provider="openai",
    llm_api_key="sk-your-api-key-here"  # Pass directly
)
```

## Available Models

### OpenAI
- `gpt-4o` - Latest GPT-4 optimized (default)
- `gpt-4-turbo-preview` - GPT-4 Turbo
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - Faster, cheaper option
- `gpt-4o-mini` - Smallest GPT-4 variant

### Google (Gemini)
- `gemini-2.0-flash-exp` - Latest experimental (default)
- `gemini-1.5-pro` - Long context window (up to 1M tokens)
- `gemini-1.5-flash` - Faster variant
- `gemini-1.0-pro` - Stable version

### Anthropic (Claude)
- `claude-3-5-sonnet-20241022` - Latest Sonnet (default)
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fastest

## Command Line Usage

### Basic Commands

```bash
# Create memory and chat (uses default model)
python3 file_chat.py --input-dir documents/ --chat --provider openai

# Load existing memory with specific model
python3 file_chat.py --load-existing output/my_memory --provider anthropic --model claude-3-opus-20240229

# Just create memory (no chat)
python3 file_chat.py --input-dir documents/ --workers 8
```

### Complete Options

```bash
python3 file_chat.py \
    --load-existing output/my_memory \
    --provider openai \
    --model gpt-4-turbo-preview \
    --chat
```

## Python API Usage

### Basic Chat

```python
from memvid import MemvidChat

# Initialize with defaults
chat = MemvidChat(
    video_file="output/video.mkv",
    index_file="output/index.json"
)

# Single query
response = chat.chat("What is The Canterbury Tales about?")

# Interactive session
chat.interactive_chat()
```

### Advanced Configuration

```python
# Custom provider and model
chat = MemvidChat(
    video_file="output/video.mkv",
    index_file="output/index.json",
    llm_provider="anthropic",
    llm_model="claude-3-opus-20240229",
    llm_api_key="sk-ant-..."  # Optional if env var set
)

# Streaming responses
chat.chat("Tell me about medieval literature", stream=True)

# Export conversation
chat.export_conversation("conversation.json")
```

### Direct Retrieval (No LLM)

```python
from memvid import MemvidRetriever

# Just search, no LLM needed
retriever = MemvidRetriever("video.mkv", "index.json")
chunks = retriever.search("Canterbury Tales", top_k=5)
```

## Implementation Locations

### Core Files
- **Chat Interface**: `memvid-env/lib/python3.13/site-packages/memvid/chat.py`
  - `MemvidChat` class - Main chat interface
  - `interactive_chat()` - CLI chat loop
  - `_get_context()` - Retrieval integration

- **LLM Client**: `memvid-env/lib/python3.13/site-packages/memvid/llm_client.py`
  - `LLMClient` - Unified interface
  - `OpenAIProvider`, `GoogleProvider`, `AnthropicProvider` - Provider implementations
  - Message format conversion logic

- **CLI Script**: `file_chat.py`
  - Command line argument parsing
  - `start_chat_session()` function (line 462)
  - Integration with memory creation

- **Configuration**: `memvid-env/lib/python3.13/site-packages/memvid/config.py`
  - Default models and parameters
  - Chat configuration settings

## Chat Features

### During Chat Session
- `quit` or `exit` - End session and save conversation
- `clear` - Clear conversation history
- `stats` - Show session statistics

### Configuration Parameters
- **Context chunks**: 5 (chunks retrieved per query)
- **Max history**: 10 messages (conversation memory)
- **Temperature**: 0.1 (low for factual responses)
- **Max tokens**: 8192 (response length limit)

## Troubleshooting

### API Key Issues
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Test with simple query
python3 -c "from memvid import MemvidChat; print(MemvidChat.check_api_keys())"
```

### Model Errors
- Ensure model name is exact (case-sensitive)
- Check provider documentation for deprecated models
- Some models require specific API access

### No LLM Available
If no API key is set, memvid falls back to context-only mode:
```
Based on the knowledge base, here's what I found:
1. [First matching chunk]
2. [Second matching chunk]
...
```

## Cost Optimization

- **Development/Testing**: Use `gpt-3.5-turbo` or `claude-3-haiku-20240307`
- **Quality Responses**: Use `gpt-4o` or `claude-3-5-sonnet-20241022`
- **Long Context**: Use `gemini-1.5-pro` (up to 1M token context)
- **Fast Responses**: Use provider's "flash" or "turbo" variants

## Example Workflow

```bash
# 1. Set up API key
export OPENAI_API_KEY="sk-..."

# 2. Create memory from documents
python3 file_chat.py --input-dir ~/Documents/books --workers 8

# 3. Chat with the memory
python3 file_chat.py --load-existing output/dir_books_* --provider openai --model gpt-4o --chat

# 4. Try different models
python3 file_chat.py --load-existing output/dir_books_* --provider anthropic --model claude-3-haiku-20240307 --chat
```

## Security Notes

- Never commit API keys to git
- Use environment variables or secure key management
- The `.gitignore` file should exclude any files containing keys
- API keys are not stored in conversation exports
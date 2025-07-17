# Song Context Analysis

The AI Light Show system can generate intelligent lighting context based on song audio analysis, using AI to understand the mood, energy, and structure of the music.

## Overview

Song context analysis works in two main stages:

1. **Audio Analysis**: The song is analyzed to extract stems, audio features, and structural elements
2. **Context Generation**: The SongContextAgent uses AI to interpret these features and generate appropriate lighting suggestions

## Usage

### Direct Command

The simplest way to generate context for the current song is to use the direct command in the chat:

```
#analyze context
```

This will process the current song and generate a timeline of lighting actions based on the song's audio characteristics.

### Prerequisites

Before using context analysis:

1. A song must be loaded
2. The song must have been analyzed with the `#analyze` command first

### Process

The context analysis follows these steps:

1. Loads the song analysis data (created by the `#analyze` command)
2. Processes each chunk of the analysis data
3. Builds AI prompts based on the audio features
4. Sends these prompts to the LLM for interpretation
5. Collects responses and assembles them into a timeline
6. Saves the results to a file for further use

### Output

The output is saved to a file at `songs/data/<song_name>.context.json` and contains a timeline of lighting actions that are synchronized with the music.

## Integration

The context data can be used to:

- Provide intelligent starting points for light show design
- Automatically generate basic lighting effects that match the music
- Enhance the manual design process with AI-suggested lighting moments

## Technical Details

The SongContextAgent class uses the song_context LLM model specifically trained for this purpose, which understands audio features and can translate them into appropriate lighting instructions.

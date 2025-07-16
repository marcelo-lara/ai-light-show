# Backlog

## Feature: UI Assistant
let's call "Direct Commands" to the messages received in "handle_user_prompt" in "ai_handler" when the string starts with "#".
- parse the input in the backend (handle_user_prompt in ai_handler)
- when a message is a command, don't send it to the llm-server.
- remove old implementations in the frontend (ChatAssistant.jsx)
- accepted time formats are: "1m23.45s" (1 minute 23.05 seconds) and "2b" (duration of 2 beats at the BPM of the current song)
- use "backend/services/utils/time_conversion.py" to convert time to seconds.
- update the "docs/direct_commands.md" document to reflect these changes.

valid commands should be:
- `#help` - show a list of available commands
- `#clear all actions` - Clear all actions from the current song
- `#clear action <action_id>` - Clear a specific action by ID
- `#clear group <group_id>` - Clear all actions with a specific group ID
- `#add <action> to <fixture> at <start_time> duration <duration_time>` - Add a new action. duration is optional, with a default value of 1 beat.
- `#render` - Render all actions to the DMX canvas




  ```javascript
  export function parseTimeString(input) {
      const pattern = /^(?:(?<minutes>\d+)m)?(?:(?<seconds>\d+\.?\d*)s)?$/;
      const match = input.match(pattern);
      if (!match || !(match.groups.minutes || match.groups.seconds)) {
          return null;
      }
      
      const minutes = parseInt(match.groups.minutes || 0, 10);
      const seconds = parseFloat(match.groups.seconds || 0);
      
      if (isNaN(minutes) || isNaN(seconds) || (minutes === 0 && seconds === 0)) {
          return null;
      }
      
      return minutes * 60 + seconds;
  }
  ```

## Improve LLM Creativity

### ChatGPT Suggestions

- Use model chaining, where each model contributes a piece of the reasoning pipeline:

  | Layer                 | Role                                                                              | Recommended Model                         |
  | --------------------- | --------------------------------------------------------------------------------- | ----------------------------------------- |
  | **Context Builder**   | Extracts or interprets song context (e.g. `"this section is intense and rising"`) | `Mistral`, `Phi-3`, `Mixtral`             |
  | **Lighting Planner**  | Proposes creative, mood-aligned lighting effects                                  | `GPT-4`, `Claude Sonnet`, `Yi-34B`        |
  | **Effect Translator** | Converts symbolic actions into JSON/DMX format                                    | `Mistral`, `Code LLM`, or hardcoded logic |

- try these local models

  | Model                  | Strength                                                              |
  | ---------------------- | --------------------------------------------------------------------- |
  | `Yi-34B`               | Open-ended creative language generation                               |
  | `Qwen-1.5-32B-Chat`    | Emotionally rich, good at visual metaphor                             |
  | `Command-R`            | Good for following task-specific instructions (e.g., generate 3 cues) |
  | `LLaVA` + spectrograms | Add vision input if you extract song visuals or waveform sections     |


- Train or use a model like MusicLM, CLAP, or jukebox to embed the song section and retrieve matching lighting prompts from a database using similarity search (e.g., FAISS or ChromaDB).

# Backlog

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

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


Use Essentia to extract time series → feed compact summaries into LLM to label moments.

🧩 Pipeline Sketch

1. Preprocess audio with Essentia (or similar):
  - Compute sliding-window features (e.g., every 1s):
  - RMS (loudness)
  - Spectral centroid (brightness)
  - Onset rate (percussiveness)
  - MFCC variance (texture)
  - Silence ratio
  - Vocal energy (from stems)
  - Drum/bass/vocal stem levels

2. Identify candidate windows:
  - Local peaks, valleys, or change deltas in features.
  - Heuristics like:
    ```python
    if energy[t+1] - energy[t-1] > threshold and vocals[t] < 0.2:
        candidate = t
    ```

3. For each candidate window (e.g. 4s around t), prepare a natural language summary:
    ```
    From 96s to 100s:
    - Drums increase in energy
    - Vocals are absent
    - Brightness (spectral centroid) increases
    - Tempo stays constant
    ```
    
4. Prompt LLM:

    ```
    What kind of musical event is happening here?
    ```

    Expected reply:

    ```
    “Possible Drop or Instrumental Break”
    ```

5. Collect answers into draft key_moments json



### ⬜ Refactor `song_analysis` pipeline using LangGraph for modular LLM-driven analysis

**Goal**: Enable a step-by-step, modular audio analysis pipeline that supports LLM-based segment labeling and lighting cue suggestions.

**Why**: Current pipeline is procedural. Using LangGraph allows easier debugging, customization, and reasoning over each step.

---

#### 🧠 Implementation Plan

**Create a LangGraph-based pipeline** inside `song_analysis/langgraph_pipeline.py` with these steps:

1. **Node: stem_split**
   - Input: `mp3_path`
   - Uses: existing `demucs_split.py`
   - Output: dict of stem paths `{ vocals, drums, bass, other }`

2. **Node: beat_detect**
   - Input: full track path (or drums stem)
   - Uses: `essentia_analysis.py`
   - Output: list of beat timestamps

3. **Node: pattern_analysis**
   - Input: stems + beat list
   - Uses: `pattern_finder.py`
   - Output: sections, repeating parts

4. **Node: segment_labeler (LLM)**
   - Input: raw segment info
   - Model: local Ollama client or remote Claude/GPT
   - Output: list of sections with names, e.g. `"Intro"`, `"Chorus"`  
     Use existing prompt patterns from `born_slippy.meta.json`

5. **Node: lighting_hint_generator (LLM)**
   - Input: labeled segments
   - Output: per-section lighting notes, to be consumed later by backend AI

---

🔧 In song_analysis/langgraph_pipeline.py
Add this utility function:

```python
import json, os
from pathlib import Path

def log_node_output(node_name: str, data: dict):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    with open(log_dir / f"{node_name}.json", "w") as f:
        json.dump(data, f, indent=2)
```

Then inside each LangGraph node function, log like this:

```python
def beat_detect_node(inputs):
    # Your existing beat detection logic here
    beats = detect_beats(inputs["audio"])
    
    log_node_output("beat_detect", {"beats": beats})
    return {"beats": beats}
```

Do the same for all nodes: stem_split, pattern_analysis, segment_labeler, lighting_hint_generator.

#### 📦 File layout

- `song_analysis/langgraph_pipeline.py`: LangGraph flow + nodes
- `song_analysis/test_pipeline_run.py`: Run pipeline against test song
- Reuse existing logic from `services/` as subfunctions if needed

---

#### 💡 Tips

- Use `langgraph.Graph()` with named steps
- Each node gets a single input/output; make it LLM-friendly JSON
- Test using `songs/born_slippy.mp3`

---

#### ✅ Success Criteria

- Given a song file, LangGraph produces a traceable output JSON:
  ```json
  {
    "sections": [
      { "name": "Intro", "start": 0.0, "end": 12.0 },
      { "name": "Drop", "start": 34.2, "end": 36.7 }
    ],
    "lighting_hints": [
      { "section": "Drop", "suggestion": "Flash red with strobe" }
    ]
  }

All steps run end-to-end with one run_pipeline(song_path) function
import torch
from CLAPWrapper import CLAPWrapper
import torchaudio

model = CLAPWrapper(device='cpu')  # or 'cuda' if you have GPU

# Load 10-second clip from your Born Slippy audio
waveform, sr = torchaudio.load("songs/born_slippy.mp3")
waveform = torchaudio.functional.resample(waveform, orig_freq=sr, new_freq=48000)

# Segment audio (10s chunks at 48kHz = 480000 samples)
chunk_size = 480000
segments = [waveform[:, i:i+chunk_size] for i in range(0, waveform.shape[1], chunk_size)]

moods = ["ambient", "intense", "chill", "electronic"]
mood_embeddings = model.get_text_embeddings(moods)

for i, segment in enumerate(segments):
    if segment.shape[1] < chunk_size:
        continue  # skip partial segments

    audio_embedding = model.get_audio_embeddings_from_data(segment)
    similarity = torch.nn.functional.cosine_similarity(audio_embedding, mood_embeddings)
    
    best_mood = moods[similarity.argmax().item()]
    print(f"Segment {i}: Mood = {best_mood}")

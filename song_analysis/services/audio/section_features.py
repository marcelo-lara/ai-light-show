import os
import json
import essentia.standard as es
import essentia
import logging
import numpy as np
essentia.log.infoActive = False
logger = logging.getLogger(__name__)


def extract_section_features(
    audio_path,
    section_start,
    section_end,
    frame_size=1024, #Frame size for FFT / Frequency resolution (1024)
    hop_size=256, #Time resolution (512)
    sample_rate=44100,
    max_mfcc=5
):
    loader = es.MonoLoader(filename=audio_path, sampleRate=sample_rate)
    audio = loader()

    start_sample = int(section_start * sample_rate)
    end_sample = int(section_end * sample_rate)
    segment = audio[start_sample:end_sample]

    window = es.Windowing(type="hann")
    spectrum = es.Spectrum()
    rms = es.RMS()
    mfcc = es.MFCC(numberCoefficients=max_mfcc, highFrequencyBound=8000)

    timestamps = []
    rms_list = []
    flux_list = []
    mfcc_bands = {f"mfcc_{i}": [] for i in range(max_mfcc)}

    prev_spec = None
    for i, frame in enumerate(es.FrameGenerator(segment, frameSize=frame_size, hopSize=hop_size, startFromZero=True)):
        t = section_start + (i * hop_size / sample_rate)
        win = window(frame)
        spec = spectrum(win)

        rms_val = rms(frame)
        _, mfcc_coeffs = mfcc(spec)

        if prev_spec is not None:
            flux_val = np.sum(np.clip(spec - prev_spec, 0, None))
        else:
            flux_val = 0.0
        prev_spec = spec

        timestamps.append(round(t, 3))
        rms_list.append(round(float(rms_val), 6))
        flux_list.append(round(float(flux_val), 6))
        for j, coeff in enumerate(mfcc_coeffs):
            mfcc_bands[f"mfcc_{j}"].append(round(float(coeff), 6))

    return {
        "timestamps": timestamps,
        "rms": rms_list,
        "flux": flux_list,
        **mfcc_bands
    }


def extract_features_from_stems(stems_dir, start, end, sample_rate=44100):
    result = {}
    for fname in os.listdir(stems_dir):
        if fname.endswith(".wav"):
            stem_name = fname.replace(".wav", "")
            path = os.path.join(stems_dir, fname)
            features = extract_section_features(path, section_start=start, section_end=end, sample_rate=sample_rate)
            result[stem_name] = features
    return result


def extract_song_features(stems_dir, chunk_size=4.0, hop=2.0, sample_rate=44100, save_file:bool=True, output_json_path=None):
    # Use any stem to estimate duration
    stem_example = next(f for f in os.listdir(stems_dir) if f.endswith(".wav"))
    duration = es.MonoLoader(filename=os.path.join(stems_dir, stem_example), sampleRate=sample_rate)().size / sample_rate

    chunks = []
    start = 0.0
    while start < duration:
        end = min(start + chunk_size, duration)
        chunk_features = extract_features_from_stems(stems_dir, start=start, end=end, sample_rate=sample_rate)

        chunks.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "stems": chunk_features
        })

        start += hop

    if output_json_path is not None:
        with open(output_json_path, "w") as f:
            json.dump(chunks, f, indent=2)
        logger.info(f"✅ All chunks saved to: {output_json_path}")

    return chunks

if __name__ == "__main__":
    # Example usage
    audio_file = "/home/darkangel/ai-light-show/songs/born_slippy.mp3"

    # Extract features for the entire song
    print(extract_song_features(
        stems_dir="/home/darkangel/ai-light-show/songs/temp/htdemucs/born_slippy"
    ))
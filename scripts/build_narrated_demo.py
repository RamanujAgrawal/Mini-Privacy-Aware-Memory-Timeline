import os
import sys
import asyncio
import subprocess
import edge_tts
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "en-US-GuyNeural"  # Professional, crisp, articulate male voice

# Target schedule: (start_timestamp_seconds, transcript_text)
SCHEDULE = [
    (0.5, "Welcome to Chronis — a production-grade, privacy-aware memory timeline designed for wearable AI companions."),
    (10.0, "Chronis continuously ingests multi-modal user streams and strictly enforces privacy boundaries directly at the backend API layer."),
    (20.5, "Wearables capture four sensitive streams: ambient conversations, GPS coordinates, physiological biometrics, and personal notes."),
    (30.5, "Client-side privacy masking is fatal. Chronis eliminates unpermitted data at the database layer before it ever reaches server memory."),
    (40.5, "Here is the live Chronis Timeline interface. Events are ingested chronologically with exact Indian Standard Time timestamps."),
    (51.0, "The background wearable simulator streams live sensor updates, while the user has instantaneous visibility into their memory history."),
    (62.5, "Users can dynamically toggle any category on or off. An API call immediately updates the privacy permission table."),
    (73.0, "Subsequent collection queries execute SQL-level filtering where restricted categories are completely omitted from the query result."),
    (84.5, "Our built-in Security Probe allows direct testing of single-resource retrieval. If a category is off, lookups trigger an immediate 403 Forbidden."),
    (95.0, "The backend halts execution, rejects the request, and atomically logs a forensic DENIED entry in the audit database."),
    (106.5, "The Audit Trail provides complete transparency. Every sensitive operation—creation, deletion, permission update, and blocked access—is logged."),
    (117.0, "The audit trail is strictly immutable and read-only, preventing any tampering or deletion of security logs."),
    (128.5, "We have also implemented four advanced enterprise architectures: JWT multi-tenancy, date-range and full-text keyword search,"),
    (138.0, "Automated granular privacy rules with keyword redactions, and GDPR data export in both JSON and CSV formats."),
    (148.5, "All 16 unit tests and 11 end-to-end verification steps pass in under 2 seconds. Chronis is complete and ready for evaluation.")
]

TOTAL_DURATION = 155.0  # 2 minutes 35 seconds

TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_temp")
os.makedirs(TEMP_DIR, exist_ok=True)


async def generate_speech_clips():
    print(f"Synthesizing {len(SCHEDULE)} narration clips with male neural voice '{VOICE}'...")
    tasks = []
    for i, (ts, text) in enumerate(SCHEDULE):
        mp3_path = os.path.join(TEMP_DIR, f"clip_{i:02d}.mp3")
        comm = edge_tts.Communicate(text, VOICE)
        tasks.append(comm.save(mp3_path))
    await asyncio.gather(*tasks)
    print("All speech clips synthesized successfully.")


def get_audio_duration(file_path):
    cmd = [
        FFMPEG_EXE, "-i", file_path,
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    for line in res.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def build_full_audio_track():
    print("Converting clips to standard 44.1kHz stereo WAV and building timeline track...")
    concat_list_file = os.path.join(TEMP_DIR, "concat_list.txt")
    
    current_time = 0.0
    wav_entries = []

    for i, (target_start, text) in enumerate(SCHEDULE):
        raw_mp3 = os.path.join(TEMP_DIR, f"clip_{i:02d}.mp3")
        norm_wav = os.path.join(TEMP_DIR, f"norm_{i:02d}.wav")

        # Convert to 44.1kHz stereo WAV
        subprocess.run([
            FFMPEG_EXE, "-y", "-i", raw_mp3,
            "-ar", "44100", "-ac", "2", norm_wav
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        clip_dur = get_audio_duration(norm_wav)

        # Calculate silence needed before this clip
        silence_needed = target_start - current_time
        if silence_needed > 0.05:
            silence_wav = os.path.join(TEMP_DIR, f"silence_{i:02d}.wav")
            subprocess.run([
                FFMPEG_EXE, "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", f"{silence_needed:.3f}",
                silence_wav
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            wav_entries.append(silence_wav)
            current_time += silence_needed

        wav_entries.append(norm_wav)
        current_time += clip_dur
        print(f"  Clip {i+1:02d} @ {current_time - clip_dur:.1f}s - {current_time:.1f}s: \"{text[:45]}...\"")

    # Final silence pad to 155s
    if current_time < TOTAL_DURATION:
        final_silence_dur = TOTAL_DURATION - current_time
        final_silence_wav = os.path.join(TEMP_DIR, "silence_final.wav")
        subprocess.run([
            FFMPEG_EXE, "-y", "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", f"{final_silence_dur:.3f}",
            final_silence_wav
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        wav_entries.append(final_silence_wav)
        current_time += final_silence_dur

    with open(concat_list_file, "w", encoding="utf-8") as f:
        for entry in wav_entries:
            safe_entry = entry.replace("\\", "/")
            f.write(f"file '{safe_entry}'\n")

    full_audio_path = os.path.join(TEMP_DIR, "full_narration.wav")
    print("Concatenating audio segments into final narration track...")
    subprocess.run([
        FFMPEG_EXE, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_file, "-c", "copy", full_audio_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"Final audio track ready: {full_audio_path} (Duration: {get_audio_duration(full_audio_path):.2f}s)")
    return full_audio_path


def mux_video_and_audio(audio_path):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_video = os.path.join(root_dir, "demo_video.mp4")
    temp_narrated_video = os.path.join(TEMP_DIR, "demo_video_narrated.mp4")

    print(f"Multiplexing audio track with 1080p video stream...")
    # Mux video with audio
    subprocess.run([
        FFMPEG_EXE, "-y",
        "-i", input_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        temp_narrated_video
    ], check=True)

    # Overwrite the original demo_video.mp4 with the narrated version
    os.replace(temp_narrated_video, input_video)
    file_size_mb = os.path.getsize(input_video) / (1024 * 1024)
    print(f"SUCCESS: Narrated video created at {input_video} ({file_size_mb:.2f} MB)")

    # Also copy to artifacts directory
    artifact_dir = r"C:\Users\raman\.gemini\antigravity\brain\a9088756-0cd8-4e9c-9453-d21e6e6c3479"
    artifact_video = os.path.join(artifact_dir, "demo_video.mp4")
    if os.path.exists(artifact_dir):
        import shutil
        shutil.copy2(input_video, artifact_video)
        print(f"SUCCESS: Copied narrated video to artifacts directory at {artifact_video}")


def main():
    asyncio.run(generate_speech_clips())
    audio_path = build_full_audio_track()
    mux_video_and_audio(audio_path)
    print("All tasks completed successfully!")


if __name__ == "__main__":
    main()

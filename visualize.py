import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

# --- Configuration ---
INPUT_VIDEO_FILE = 'input_cyberpunk_2077.mp4' 
WINDOW_SECONDS = 0.5
SLIDE_SECONDS = 0.1
WINDOW_VARIANCE_THRESHOLD = 0.02

def analyze_video_brightness(video_path):
    print("--- Pass 1: Analyzing video brightness... ---")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return [], 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    brightness_levels = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray) / 255.0
        brightness_levels.append(brightness)
    cap.release()
    print(f"Analysis complete.")
    return brightness_levels, fps

def plan_windowed_dimming(brightness_levels, fps, window_seconds, slide_seconds, variance_threshold):
    print("--- Gathering variance data for plotting... ---")
    num_frames = len(brightness_levels)
    variance_log = []
    for i in range(0, num_frames - int(window_seconds * fps) + 1, int(slide_seconds * fps) if int(slide_seconds * fps) > 0 else 1):
        window_start = i
        window_end = i + int(window_seconds * fps)
        window_brightness = brightness_levels[window_start:window_end]
        if len(window_brightness) > 1:
            avg_diff = np.mean(np.abs(np.diff(window_brightness)))
            variance_log.append({'window_start_frame': window_start, 'variance': avg_diff})
    return variance_log

def main():
    if not os.path.exists(INPUT_VIDEO_FILE):
        print(f"Error: Input video file '{INPUT_VIDEO_FILE}' not found.")
        return
    brightness_data, fps = analyze_video_brightness(INPUT_VIDEO_FILE)
    if fps == 0: return
    variance_data = plan_windowed_dimming(
        brightness_data, fps, WINDOW_SECONDS, SLIDE_SECONDS, WINDOW_VARIANCE_THRESHOLD
    )
    
    print(f"\n--- Generating variance plot... ---")
    start_frames = [entry['window_start_frame'] for entry in variance_data]
    variances = [entry['variance'] for entry in variance_data]
    time_in_seconds = [frame / fps for frame in start_frames]

    plt.figure(figsize=(15, 6))
    plt.plot(time_in_seconds, variances, label='Frame-to-Frame Variance')
    plt.axhline(y=WINDOW_VARIANCE_THRESHOLD, color='r', linestyle='--', label=f'Variance Threshold')
    
    plt.title('Video Brightness Variance Analysis')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Average Brightness Difference')
    plt.legend()
    plt.grid(True)
    
    plt.savefig('variance_plot.png')
    print(f"Plot saved successfully as 'variance_plot.png'")

if __name__ == "__main__":
    main()
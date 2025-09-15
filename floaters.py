import cv2
import numpy as np
import os

# --- Configuration ---
INPUT_VIDEO_FILE = 'input.mp4'  # <--- CHANGE THIS to your video file
OUTPUT_VIDEO_FILE = 'output.mp4'
# --- Window-Based Configuration ---
WINDOW_SECONDS = 3.0  # Duration of the analysis window in seconds
SLIDE_SECONDS = 1.0   # How often to slide the window forward
# --- Detection & Effect Configuration ---
# This value makes the detection more sensitive to smaller fluctuations in brightness.
WINDOW_VARIANCE_THRESHOLD = 0.02 # Trigger effect if avg. frame-to-frame change exceeds 2%

# --- NEW: Inverse Blend Configuration ---
# When high variance is detected, the frame will be blended with its inverse.
# 0.0 = original frame (no effect)
# 0.5 = 50% original, 50% inverse (makes bright/dark areas gray)
# 1.0 = fully inverted frame
INVERSE_BLEND_FACTOR = 0.45

# This is a marker value used by the planning function to "flag" a frame.
# It no longer directly controls brightness. Any value < 1.0 will work.
EFFECT_FLAG_VALUE = 0.1

def create_dummy_video(video_path, width=640, height=480, frames=300, fps=30.0):
    """Creates a dummy video with a high-variance (flashing) section."""
    print(f"Creating a dummy video at '{video_path}'...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    
    # Define the start and end of the flashing section to be in the middle
    flash_start = int(frames * 0.4)
    flash_end = int(frames * 0.6)

    for i in range(frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Create a high variance (flashing) section in the middle
        if flash_start < i < flash_end:
            if i % 4 < 2: # Flash on and off rapidly
                frame[:] = (200, 200, 200) # Bright
            else:
                frame[:] = (25, 25, 25)   # Dark
        else:
            frame[:] = (25, 25, 25)   # Constant dark background
        out.write(frame)
    out.release()
    print("Dummy video created. Please run the script again.")

def analyze_video_brightness(video_path):
    """
    Analyzes a video's brightness frame by frame.
    
    Args:
        video_path (str): The path to the input video file.

    Returns:
        tuple: A tuple containing (list of brightness levels, video fps).
    """
    print("--- Pass 1: Analyzing video brightness... ---")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    brightness_levels = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray) / 255.0
        brightness_levels.append(brightness)
    cap.release()
    print(f"Analysis complete. Found {len(brightness_levels)} frames at {fps:.2f} FPS.")
    return brightness_levels, fps

def plan_windowed_dimming(brightness_levels, fps, window_seconds, slide_seconds, variance_threshold, dim_factor):
    """
    Plans dimming factors based on brightness variance within sliding time windows.

    Args:
        brightness_levels (list): A list of frame brightness values.
        fps (float): The frames per second of the video.
        window_seconds (float): The duration of the analysis window.
        slide_seconds (float): The duration of each slide step.
        variance_threshold (float): The variance threshold to trigger dimming.
        dim_factor (float): The brightness multiplier for dimmed windows.

    Returns:
        tuple: A tuple containing (dim_factors array, list of variance logs).
    """
    print("--- Planning windowed dimming effects... ---")
    num_frames = len(brightness_levels)
    dim_factors = np.ones(num_frames)
    variance_log = [] # List to store variance data
    
    # Convert seconds to frame counts
    window_size = int(window_seconds * fps)
    slide_step = int(slide_seconds * fps)
    if slide_step < 1: # Ensure the loop progresses
        slide_step = 1

    # Iterate through the video using a sliding window
    for i in range(0, num_frames - window_size + 1, slide_step):
        window_start = i
        window_end = i + window_size
        window_brightness = brightness_levels[window_start:window_end]

        if len(window_brightness) < 2:
            continue

        # Calculate the average absolute difference between consecutive frames
        diffs = np.abs(np.diff(window_brightness))
        avg_diff = np.mean(diffs)

        # Log the variance for this window
        variance_log.append({'window_start_frame': window_start, 'variance': avg_diff})

        # If the average difference (variance) is too high, tag the whole window for dimming
        if avg_diff > variance_threshold:
            print(f"High variance detected in window starting at frame {window_start}. Avg diff: {avg_diff:.3f}")
            dim_factors[window_start:window_end] = dim_factor
            
    return dim_factors, variance_log

def apply_effects_and_save(input_path, output_path, dim_factors):
    """
    Applies the planned inverse blending effect and saves the new video.

    Args:
        input_path (str): The path to the original video file.
        output_path (str): The path to save the processed video file.
        dim_factors (np.ndarray): The array of factors for each frame.
                                  A value < 1.0 flags the frame for the effect.
    """
    print("\n--- Pass 2: Applying effects and saving video... ---")
    cap = cv2.VideoCapture(input_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    frame_index = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Check if the current frame was flagged for an effect
        factor = dim_factors[frame_index]
        
        if factor < 1.0:
            # 1. Invert the frame's colors (e.g., black becomes white)
            inverted_frame = cv2.bitwise_not(frame)
            
            # 2. Blend the original frame with its inverse.
            # The formula is: output = frame * (1 - alpha) + inverted * alpha + 0
            # An alpha of 0.5 results in a 50/50 mix, effectively making
            # very bright and very dark areas move towards middle gray.
            processed_frame = cv2.addWeighted(
                src1=frame,
                alpha=(1 - INVERSE_BLEND_FACTOR),
                src2=inverted_frame,
                beta=INVERSE_BLEND_FACTOR,
                gamma=0
            )
        else:
            # No effect needed, use the original frame
            processed_frame = frame
        
        out.write(processed_frame)
        
        if frame_index % 100 == 0:
            print(f"Processed {frame_index} frames...")
        frame_index += 1

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("\n--- Processing complete! ---")
    print(f"Your new video has been saved as '{output_path}'")

def main():
    """Main function to orchestrate the video processing."""
    if not os.path.exists(INPUT_VIDEO_FILE):
        print(f"Error: Input video file not found at '{INPUT_VIDEO_FILE}'")
        create_dummy_video(INPUT_VIDEO_FILE)
        return

    # Step 1: Analyze the video to get brightness levels and FPS
    brightness_data, fps = analyze_video_brightness(INPUT_VIDEO_FILE)
    
    # Step 2: Plan the dimming effects and get the variance log
    dimming_plan, variance_data = plan_windowed_dimming(
        brightness_data, fps, WINDOW_SECONDS, SLIDE_SECONDS, WINDOW_VARIANCE_THRESHOLD, EFFECT_FLAG_VALUE
    )
    
    # Print the collected variance data
    print("\n--- Variance Log ---")
    for entry in variance_data:
        print(f"Window starting at frame {entry['window_start_frame']}: Variance = {entry['variance']:.4f}")
    
    # Step 3: Apply the plan and create the final video
    apply_effects_and_save(INPUT_VIDEO_FILE, OUTPUT_VIDEO_FILE, dimming_plan)

if __name__ == "__main__":
    main()

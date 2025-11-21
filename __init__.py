from typing import List, Dict, Any, Tuple, Union
from pathlib import Path


class VideoOutputBridge:
    """Expose VHS video filenames as standard image outputs.

    Purpose-built for RunPod's worker-comfyui stack, this bridge makes the
    worker's S3 uploader (configured through the environment variables in
    https://github.com/runpod-workers/worker-comfyui/blob/main/docs/configuration.md)
    see VHS renders as standard images.

    Some serverless runners (e.g., RunPod) only look for items in the `images`
    array when collecting artifacts. VHS_VideoCombine emits its metadata under
    the `gifs` key, so those outputs are ignored.

    This node simply takes the list of VHS filenames and returns a UI payload
    that mimics the structure ComfyUI uses for images, allowing downstream
    tooling to treat rendered videos as if they were standard image outputs.
    """

    CATEGORY = "Utility/Bridges"
    RETURN_TYPES: tuple = ()
    RETURN_NAMES: tuple = ()
    FUNCTION = "forward"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filenames": ("VHS_FILENAMES",),
                "label": (
                    "STRING",
                    {
                        "default": "video-output",
                        "multiline": False,
                        "tooltip": "Used as the filename prefix when metadata is missing.",
                    },
                ),
            }
        }

    def forward(self, filenames, label: str):
        images = []

        # Diagnostic: Log the raw input for debugging
        print(f"VideoOutputBridge: Raw input type={type(filenames).__name__}, value={filenames}")

        # VHS_FILENAMES is a tuple of (save_output_bool, list_of_files)
        # Extract the actual list of files from the tuple
        if isinstance(filenames, tuple) and len(filenames) == 2:
            save_output, file_list = filenames
            print(f"VideoOutputBridge: Unpacked tuple - save_output={save_output}, files={file_list}")
            filenames = file_list

        # Handle edge cases: booleans, None, or other non-list types
        if isinstance(filenames, bool) or filenames is None:
            print(f"VideoOutputBridge: Received {type(filenames).__name__} instead of expected list")
            filenames = []

        # Normalize to list if we got a single item
        if not isinstance(filenames, list):
            filenames = [filenames]

        # VHS returns [metadata.png, video.mp4, ...] - first file is metadata PNG
        # Filter out .png files to only process actual video outputs
        video_files = [f for f in filenames if not (isinstance(f, str) and f.lower().endswith('.png'))]

        if len(video_files) < len(filenames):
            print(f"VideoOutputBridge: Filtered out {len(filenames) - len(video_files)} metadata PNG file(s)")

        # Process each entry - VHS can return strings (paths) or dicts
        for idx, entry in enumerate(video_files):
            # Handle string paths (the common VHS format)
            if isinstance(entry, str):
                p = Path(entry)
                images.append({
                    "filename": p.name,
                    "subfolder": str(p.parent) if p.parent != Path('.') else "",
                    "type": "output"
                })
                continue

            # Handle dictionary format (alternative VHS format)
            if isinstance(entry, dict):
                filename = entry.get("filename") or f"{label}_{idx}.mp4"
                images.append({
                    "filename": filename,
                    "subfolder": entry.get("subfolder", ""),
                    "type": entry.get("type", "output"),
                })
                continue

            # Skip booleans and other unexpected types
            print(f"VideoOutputBridge: Skipping unsupported type at index {idx}: {type(entry).__name__}")

        if not images:
            # Create an empty placeholder entry so downstream tooling knows a
            # video was expected (RunPod's S3 uploader uses this signal).
            print(f"VideoOutputBridge: No video files found, creating placeholder")
            images.append(
                {
                    "filename": f"{label}_missing.mp4",
                    "subfolder": "",
                    "type": "output",
                }
            )

        # Final diagnostic: Show what we're returning
        print(f"VideoOutputBridge: Returning {len(images)} image(s): {images}")

        return {"ui": {"images": images}}


NODE_CLASS_MAPPINGS = {
    "VideoOutputBridge": VideoOutputBridge,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoOutputBridge": "Video Output Bridge",
}

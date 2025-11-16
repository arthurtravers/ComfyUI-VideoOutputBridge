from typing import List, Dict, Any


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

    def forward(self, filenames: List[Dict[str, Any]], label: str):
        images = []

        # Handle case where VHS_VideoCombine returns a boolean (error state)
        # or other unexpected types
        if not isinstance(filenames, list):
            print(f"VideoOutputBridge: Expected list of filenames, got {type(filenames).__name__}: {filenames}")
            # If we got a boolean False or other non-list, treat it as empty
            filenames = []

        for idx, entry in enumerate(filenames):
            # Ensure each entry is a dictionary
            if not isinstance(entry, dict):
                print(f"VideoOutputBridge: Skipping non-dict entry at index {idx}: {entry}")
                continue

            filename = entry.get("filename") or f"{label}_{idx}.mp4"
            images.append(
                {
                    "filename": filename,
                    "subfolder": entry.get("subfolder", ""),
                    "type": entry.get("type", "output"),
                }
            )

        if not images:
            # Create an empty placeholder entry so downstream tooling knows a
            # video was expected (RunPod's S3 uploader uses this signal).
            images.append(
                {
                    "filename": f"{label}_missing.mp4",
                    "subfolder": "",
                    "type": "output",
                }
            )

        return {"ui": {"images": images}}


NODE_CLASS_MAPPINGS = {
    "VideoOutputBridge": VideoOutputBridge,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoOutputBridge": "Video Output Bridge",
}

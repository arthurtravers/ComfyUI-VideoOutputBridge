# Video Output Bridge

A tiny ComfyUI custom node built to unblock RunPod's [`worker-comfyui`](https://github.com/runpod-workers/worker-comfyui)
deployments. It converts `VHS_VideoCombine` outputs into the standard `images`
payload so serverless runners (RunPod, Modal, etc.) can pick up rendered
MP4/WebP files automatically.

## Why?

Some providers only inspect the `images` field in the workflow history when
collecting artifacts. `VHS_VideoCombine` writes its metadata under `gifs`, which
means otherwise successful jobs return `success_no_images`. This node simply
maps those filenames back into the `images` list without touching the actual
video files.

## Usage

1. Install the node (either from the Comfy registry or by copying this folder
   into your `custom_nodes` directory).
2. Connect the `VHS_FILENAMES` output from `VHS_VideoCombine` into the
   `filenames` input on `VideoOutputBridge`.
3. Trigger the node as the final output. The workflow history will now contain
   the video filenames under `images`, allowing external tooling to upload or
   download the MP4 files.

## RunPod Worker configuration

If you are using RunPod's `worker-comfyui`, make sure the worker is configured
to upload artifacts to your S3 bucket; otherwise the registry sees the filenames
but nothing is exported. Follow the environment variable guide in the official
[Configuration Guide](https://github.com/runpod-workers/worker-comfyui/blob/main/docs/configuration.md)
to set the required S3 bucket, access key, and upload toggles.

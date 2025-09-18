"""
Tests for vggt_extract_video_frames in demo_gradio.py that reproduce the tutorial exactly.

Tutorial: VGGT_Agent/notebooks/demo_gradio/demo_gradio_execution_final.ipynb
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os
import pandas as pd
import cv2
from PIL import Image
import imagehash

# Add project root to Python path to enable src imports
project_root = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ========= Fixtures =========
@pytest.fixture
def server(test_directories):
    """FastMCP server fixture with the demo_gradio tool."""
    # Force module reload
    module_name = 'src.tools.demo_gradio'
    if module_name in sys.modules:
        del sys.modules[module_name]

    import src.tools.demo_gradio
    return src.tools.demo_gradio.demo_gradio_mcp

@pytest.fixture
def test_directories():
    """Setup test directories and environment variables."""
    test_input_dir = pathlib.Path(__file__).parent.parent.parent / "data" / "demo_gradio"
    test_output_dir = pathlib.Path(__file__).parent.parent.parent / "results" / "demo_gradio"

    test_input_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)

    # Environment variable management
    old_input_dir = os.environ.get("DEMO_GRADIO_INPUT_DIR")
    old_output_dir = os.environ.get("DEMO_GRADIO_OUTPUT_DIR")

    os.environ["DEMO_GRADIO_INPUT_DIR"] = str(test_input_dir.resolve())
    os.environ["DEMO_GRADIO_OUTPUT_DIR"] = str(test_output_dir.resolve())

    yield {"input_dir": test_input_dir, "output_dir": test_output_dir}

    # Cleanup
    if old_input_dir is not None:
        os.environ["DEMO_GRADIO_INPUT_DIR"] = old_input_dir
    else:
        os.environ.pop("DEMO_GRADIO_INPUT_DIR", None)

    if old_output_dir is not None:
        os.environ["DEMO_GRADIO_OUTPUT_DIR"] = old_output_dir
    else:
        os.environ.pop("DEMO_GRADIO_OUTPUT_DIR", None)

# ========= Input Fixtures (Tutorial Values) =========
@pytest.fixture
def vggt_extract_video_frames_inputs(test_directories) -> dict:
    """Use exact tutorial video example."""
    # Copy a sample video to test input directory for testing
    import shutil
    source_video = pathlib.Path("/Users/speed/Downloads/Paper2Agent/VGGT_Agent/repo/vggt/examples/videos/room.mp4")
    test_video = test_directories["input_dir"] / "test_room.mp4"

    if source_video.exists():
        shutil.copy2(source_video, test_video)

    return {
        "video_path": str(test_video),
        "frame_interval_seconds": 1.0,  # Tutorial default
        "out_prefix": "test_video_frames"
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_vggt_extract_video_frames(server, vggt_extract_video_frames_inputs, test_directories):
    async with Client(server) as client:
        result = await client.call_tool("vggt_extract_video_frames", vggt_extract_video_frames_inputs)
        result_data = result.data

        # 1. File Output Verification (tutorial creates CSV summary and frame images)
        expected_files = ["test_video_frames_frame_summary.csv"]
        artifacts = result_data.get("artifacts", [])

        # Check summary file exists
        summary_file_found = False
        frames_dir_found = False

        for artifact in artifacts:
            artifact_path = pathlib.Path(artifact["path"])
            if artifact["description"] == "Frame extraction summary":
                summary_file_found = artifact_path.exists()
                assert summary_file_found, f"Summary file not found: {artifact_path}"
            elif artifact["description"] == "Extracted frames directory":
                frames_dir_found = artifact_path.exists()
                assert frames_dir_found, f"Frames directory not found: {artifact_path}"

        assert summary_file_found, "Frame extraction summary file not found in artifacts"
        assert frames_dir_found, "Extracted frames directory not found in artifacts"

        # 2. Data Structure Verification (CSV file structure)
        summary_file_path = None
        for artifact in artifacts:
            if artifact["description"] == "Frame extraction summary":
                summary_file_path = pathlib.Path(artifact["path"])
                break

        assert summary_file_path is not None, "Could not find summary file path"

        # Load and verify CSV structure
        summary_df = pd.read_csv(summary_file_path)
        expected_columns = ['frame_number', 'frame_path', 'original_frame_index']
        actual_columns = summary_df.columns.tolist()
        assert all(col in actual_columns for col in expected_columns), f"Missing expected columns: {set(expected_columns) - set(actual_columns)}"

        # 3. Frame count verification (based on video length and interval)
        # Get video info for verification
        video_path = vggt_extract_video_frames_inputs["video_path"]
        vs = cv2.VideoCapture(video_path)
        fps = vs.get(cv2.CAP_PROP_FPS)
        frame_count = int(vs.get(cv2.CAP_PROP_FRAME_COUNT))
        vs.release()

        frame_interval_seconds = vggt_extract_video_frames_inputs["frame_interval_seconds"]
        frame_interval = int(fps * frame_interval_seconds)
        expected_extracted_frames = frame_count // frame_interval

        actual_extracted_frames = len(summary_df)

        # Allow some tolerance for frame extraction variations
        assert abs(actual_extracted_frames - expected_extracted_frames) <= 2, f"Expected approximately {expected_extracted_frames} frames, got {actual_extracted_frames}"

        # 4. Message verification
        expected_message_pattern = "Extracted"
        assert expected_message_pattern in result_data.get("message", ""), f"Expected message containing '{expected_message_pattern}', got: {result_data.get('message', '')}"

        # 5. Verify frame files actually exist
        frames_dir_path = None
        for artifact in artifacts:
            if artifact["description"] == "Extracted frames directory":
                frames_dir_path = pathlib.Path(artifact["path"])
                break

        frame_files = list(frames_dir_path.glob("*.png"))
        assert len(frame_files) == len(summary_df), f"Number of frame files ({len(frame_files)}) doesn't match CSV entries ({len(summary_df)})"

        # 6. Verify frame paths in CSV match actual files
        for _, row in summary_df.iterrows():
            frame_path = pathlib.Path(row['frame_path'])
            assert frame_path.exists(), f"Frame file not found: {frame_path}"
            assert frame_path.suffix == '.png', f"Expected PNG file, got: {frame_path.suffix}"

        # 7. Image Verification (no tutorial figures to compare, skip image comparison)
        # Tutorial doesn't show specific figure outputs for video frame extraction
        pass
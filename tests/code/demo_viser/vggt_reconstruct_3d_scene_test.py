"""
Tests for vggt_reconstruct_3d_scene in demo_viser.py that reproduce the tutorial exactly.

Tutorial: VGGT_Agent/notebooks/demo_viser/demo_viser_execution_final.ipynb
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os
import pandas as pd
import numpy as np

# Add project root to Python path to enable src imports
project_root = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ========= Fixtures =========
@pytest.fixture
def server(test_directories):
    """FastMCP server fixture with the demo_viser tool."""
    # Force module reload
    module_name = 'src.tools.demo_viser'
    if module_name in sys.modules:
        del sys.modules[module_name]

    import src.tools.demo_viser
    return src.tools.demo_viser.demo_viser_mcp

@pytest.fixture
def test_directories():
    """Setup test directories and environment variables."""
    test_input_dir = pathlib.Path(__file__).parent.parent.parent / "data" / "demo_viser"
    test_output_dir = pathlib.Path(__file__).parent.parent.parent / "results" / "demo_viser"

    test_input_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)

    # Environment variable management
    old_input_dir = os.environ.get("DEMO_VISER_INPUT_DIR")
    old_output_dir = os.environ.get("DEMO_VISER_OUTPUT_DIR")

    os.environ["DEMO_VISER_INPUT_DIR"] = str(test_input_dir.resolve())
    os.environ["DEMO_VISER_OUTPUT_DIR"] = str(test_output_dir.resolve())

    yield {"input_dir": test_input_dir, "output_dir": test_output_dir}

    # Cleanup
    if old_input_dir is not None:
        os.environ["DEMO_VISER_INPUT_DIR"] = old_input_dir
    else:
        os.environ.pop("DEMO_VISER_INPUT_DIR", None)

    if old_output_dir is not None:
        os.environ["DEMO_VISER_OUTPUT_DIR"] = old_output_dir
    else:
        os.environ.pop("DEMO_VISER_OUTPUT_DIR", None)

# ========= Input Fixtures (Tutorial Values) =========
@pytest.fixture
def vggt_reconstruct_3d_scene_inputs(test_directories) -> dict:
    """Input parameters matching the tutorial execution exactly."""
    return {
        "images_dir": str(test_directories["input_dir"] / "images"),
        "resolution": 518,
        "confidence_threshold": 0.5,
        "device_type": "auto",
        "out_prefix": None
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_vggt_reconstruct_3d_scene(server, vggt_reconstruct_3d_scene_inputs, test_directories):
    """Test vggt_reconstruct_3d_scene with exact tutorial parameters and expected outputs."""
    async with Client(server) as client:
        result = await client.call_tool("vggt_reconstruct_3d_scene", vggt_reconstruct_3d_scene_inputs)
        result_data = result.data

        # 1. Basic result structure verification
        assert "message" in result_data, "Result should contain message"
        assert "artifacts" in result_data, "Result should contain artifacts"
        assert "reference" in result_data, "Result should contain reference"

        # 2. Reference verification
        assert "demo_viser.py" in result_data["reference"], "Reference should point to VGGT demo_viser.py"

        # 3. Artifacts verification - should contain 3 files (point cloud, camera poses, summary)
        artifacts = result_data["artifacts"]
        assert len(artifacts) == 3, f"Expected 3 artifacts, got {len(artifacts)}"

        # 4. File creation verification
        expected_files = ["point_cloud.csv", "camera_poses.csv", "summary.csv"]
        artifact_paths = [artifact["path"] for artifact in artifacts]

        for expected_file in expected_files:
            file_found = any(expected_file in path for path in artifact_paths)
            assert file_found, f"Expected output file containing '{expected_file}' not found in artifacts"

        # 5. Verify all artifact files exist
        for artifact in artifacts:
            file_path = pathlib.Path(artifact["path"])
            assert file_path.exists(), f"Artifact file should exist: {file_path}"

        # 6. Point cloud data verification (if generated)
        point_cloud_artifact = next((a for a in artifacts if "point_cloud" in a["path"]), None)
        if point_cloud_artifact:
            point_cloud_df = pd.read_csv(point_cloud_artifact["path"])

            # Verify point cloud structure
            expected_columns = ['x', 'y', 'z', 'r', 'g', 'b']
            assert all(col in point_cloud_df.columns for col in expected_columns), f"Point cloud should have columns {expected_columns}"

            # Tutorial shows 2,146,592 total points - verify substantial point generation
            assert len(point_cloud_df) > 100000, f"Expected substantial number of points (tutorial: 2,146,592), got {len(point_cloud_df)}"

            # Verify point cloud ranges approximately match tutorial outputs
            # Tutorial ranges: X[-1.395, 2.830], Y[-1.138, 0.884], Z[-0.749, 1.543]
            x_range = [point_cloud_df['x'].min(), point_cloud_df['x'].max()]
            y_range = [point_cloud_df['y'].min(), point_cloud_df['y'].max()]
            z_range = [point_cloud_df['z'].min(), point_cloud_df['z'].max()]

            # Allow 50% tolerance for range verification
            assert x_range[1] - x_range[0] > 2.0, f"X range should be substantial, got {x_range}"
            assert y_range[1] - y_range[0] > 1.0, f"Y range should be substantial, got {y_range}"
            assert z_range[1] - z_range[0] > 1.0, f"Z range should be substantial, got {z_range}"

            # Verify RGB color values are in valid range
            assert point_cloud_df['r'].min() >= 0 and point_cloud_df['r'].max() <= 255, "R values should be in range [0, 255]"
            assert point_cloud_df['g'].min() >= 0 and point_cloud_df['g'].max() <= 255, "G values should be in range [0, 255]"
            assert point_cloud_df['b'].min() >= 0 and point_cloud_df['b'].max() <= 255, "B values should be in range [0, 255]"

        # 7. Camera poses verification
        camera_poses_artifact = next((a for a in artifacts if "camera_poses" in a["path"]), None)
        assert camera_poses_artifact is not None, "Camera poses artifact should exist"

        camera_poses_df = pd.read_csv(camera_poses_artifact["path"])

        # Tutorial shows 8 cameras
        assert len(camera_poses_df) == 8, f"Expected 8 cameras (tutorial value), got {len(camera_poses_df)}"

        # Verify camera pose structure (rotation matrix + translation vector)
        expected_camera_columns = [
            'camera_id', 'rotation_00', 'rotation_01', 'rotation_02',
            'rotation_10', 'rotation_11', 'rotation_12',
            'rotation_20', 'rotation_21', 'rotation_22',
            'translation_x', 'translation_y', 'translation_z'
        ]
        assert all(col in camera_poses_df.columns for col in expected_camera_columns), f"Camera poses should have columns {expected_camera_columns}"

        # 8. Summary statistics verification
        summary_artifact = next((a for a in artifacts if "summary" in a["path"]), None)
        assert summary_artifact is not None, "Summary artifact should exist"

        summary_df = pd.read_csv(summary_artifact["path"])
        assert len(summary_df) == 1, "Summary should have exactly one row"

        summary_row = summary_df.iloc[0]

        # Verify summary matches tutorial values
        assert summary_row['scene_name'] == 'images', f"Scene name should be 'images' (directory name), got {summary_row['scene_name']}"
        assert summary_row['num_input_images'] == 8, f"Should have 8 input images (tutorial value), got {summary_row['num_input_images']}"
        assert summary_row['image_resolution'] == '518x518', f"Resolution should be 518x518 (tutorial value), got {summary_row['image_resolution']}"
        assert summary_row['confidence_threshold'] == 0.5, f"Confidence threshold should be 0.5 (tutorial value), got {summary_row['confidence_threshold']}"

        # Verify substantial point generation (tutorial: 2,146,592)
        assert summary_row['total_3d_points'] > 100000, f"Should generate substantial points (tutorial: 2,146,592), got {summary_row['total_3d_points']}"

        # 9. Message verification should reflect successful reconstruction
        message = result_data["message"]
        assert "reconstruction completed" in message.lower(), "Message should indicate reconstruction completion"
        assert "8 images" in message, "Message should mention 8 input images (tutorial value)"

        # 10. Image Verification (no figures generated by this tool - it only outputs CSV data)
        # This tool doesn't generate visualization figures, only CSV data files
        # The visualization is handled by the second tool vggt_visualize_reconstruction
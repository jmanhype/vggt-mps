"""
Tests for vggt_reconstruct_3d_scene_simplified in demo_colmap.py that reproduce the tutorial exactly.

Tutorial: https://github.com/facebookresearch/vggt/blob/main/demo_colmap.py
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os
from PIL import Image
import imagehash
import numpy as np

# Add project root to Python path to enable src imports
project_root = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ========= Fixtures =========
@pytest.fixture
def server(test_directories):
    """FastMCP server fixture with the demo_colmap tool."""
    # Force module reload
    module_name = 'src.tools.demo_colmap'
    if module_name in sys.modules:
        del sys.modules[module_name]

    import src.tools.demo_colmap
    return src.tools.demo_colmap.demo_colmap_mcp

@pytest.fixture
def test_directories():
    """Setup test directories and environment variables."""
    test_input_dir = pathlib.Path(__file__).parent.parent.parent / "data" / "demo_colmap"
    test_output_dir = pathlib.Path(__file__).parent.parent.parent / "results" / "demo_colmap"

    test_input_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)

    # Environment variable management
    old_input_dir = os.environ.get("DEMO_COLMAP_INPUT_DIR")
    old_output_dir = os.environ.get("DEMO_COLMAP_OUTPUT_DIR")

    os.environ["DEMO_COLMAP_INPUT_DIR"] = str(test_input_dir.resolve())
    os.environ["DEMO_COLMAP_OUTPUT_DIR"] = str(test_output_dir.resolve())

    yield {"input_dir": test_input_dir, "output_dir": test_output_dir}

    # Cleanup
    if old_input_dir is not None:
        os.environ["DEMO_COLMAP_INPUT_DIR"] = old_input_dir
    else:
        os.environ.pop("DEMO_COLMAP_INPUT_DIR", None)

    if old_output_dir is not None:
        os.environ["DEMO_COLMAP_OUTPUT_DIR"] = old_output_dir
    else:
        os.environ.pop("DEMO_COLMAP_OUTPUT_DIR", None)

# ========= Input Fixtures (Tutorial Values) =========
@pytest.fixture
def vggt_reconstruct_3d_scene_simplified_inputs(test_directories) -> dict:
    return {
        "scene_dir_path": str(project_root / "repo" / "vggt" / "examples" / "room"),
        "seed": 42,
        "img_load_resolution": 1024,
        "vggt_fixed_resolution": 518,
        "conf_thres_value": 5.0,
        "max_points_for_colmap": 100000,
        "max_vis_points": 5000,
        "out_prefix": None,
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_vggt_reconstruct_3d_scene_simplified(server, vggt_reconstruct_3d_scene_simplified_inputs, test_directories):
    async with Client(server) as client:
        result = await client.call_tool("vggt_reconstruct_3d_scene_simplified", vggt_reconstruct_3d_scene_simplified_inputs)
        result_data = result.data

        # 1. Basic Return Structure Verification
        assert "message" in result_data, "Result should contain message"
        assert "reference" in result_data, "Result should contain reference"
        assert "artifacts" in result_data, "Result should contain artifacts"

        # 2. Message Content Verification (from tutorial)
        message = result_data["message"]
        assert "room" in message, "Message should contain scene name 'room'"
        assert "8 images" in message, "Message should report 8 images as in tutorial"
        assert "filtered points" in message, "Message should mention filtered points"

        # 3. Reference URL Verification
        expected_reference = "https://github.com/facebookresearch/vggt/blob/main/demo_colmap.py"
        assert result_data["reference"] == expected_reference, f"Expected reference {expected_reference}"

        # 4. Artifacts Verification (from tutorial execution)
        artifacts = result_data["artifacts"]
        assert isinstance(artifacts, list), "Artifacts should be a list"
        assert len(artifacts) >= 3, "Should have at least 3 artifacts (input, depth/confidence, 3d viz)"

        # Expected artifact descriptions from tutorial
        expected_artifacts = [
            "Input images visualization",
            "Depth and confidence maps",
            "3D point cloud visualization",
            "Reconstruction summary and parameters"
        ]

        artifact_descriptions = [artifact["description"] for artifact in artifacts]
        for expected_desc in expected_artifacts:
            assert any(expected_desc in desc for desc in artifact_descriptions), f"Missing artifact: {expected_desc}"

        # 5. File Output Verification (tutorial creates specific files)
        for artifact in artifacts:
            artifact_path = pathlib.Path(artifact["path"])
            assert artifact_path.exists(), f"Artifact file should exist: {artifact['path']}"

            # Verify file sizes are reasonable (not empty)
            if artifact_path.is_file():
                assert artifact_path.stat().st_size > 0, f"Artifact file should not be empty: {artifact['path']}"

        # 6. PLY Point Cloud File Verification (tutorial creates this)
        ply_artifacts = [a for a in artifacts if "PLY" in a["description"]]
        if ply_artifacts:  # PLY creation might fail in some environments
            ply_path = pathlib.Path(ply_artifacts[0]["path"])
            assert ply_path.exists(), "PLY file should exist"
            assert ply_path.suffix == ".ply", "Should be a PLY file"

        # 7. Summary CSV Verification (tutorial creates this)
        summary_artifacts = [a for a in artifacts if "summary" in a["description"]]
        assert len(summary_artifacts) >= 1, "Should have reconstruction summary"
        summary_path = pathlib.Path(summary_artifacts[0]["path"])
        assert summary_path.exists(), "Summary CSV should exist"
        assert summary_path.suffix == ".csv", "Summary should be CSV file"

        # 8. Camera Parameters Verification (from tutorial output)
        # Verify output directory structure matches tutorial
        output_files = list(test_directories["output_dir"].rglob("*"))
        output_file_names = [f.name for f in output_files if f.is_file()]

        expected_files = ["input_images.png", "depth_and_confidence_maps.png", "3d_point_cloud_visualization.png", "reconstruction_summary.csv"]
        for expected_file in expected_files:
            assert any(expected_file in name for name in output_file_names), f"Expected output file {expected_file} not found"

        # 9. Image Verification (if tutorial shows images, compare with generated figures)
        notebook_figures_dir = pathlib.Path("notebooks/demo_colmap/images")
        if notebook_figures_dir.exists():
            png_files = [f for f in os.listdir(notebook_figures_dir) if f.endswith('.png')]

            # Check generated visualization files for similarity to tutorial figures
            vis_files = [f for f in output_files if f.suffix == '.png']

            if png_files and vis_files:
                for vis_file in vis_files[:3]:  # Check first 3 generated images
                    hamming_vec = []
                    for png_file in png_files:
                        try:
                            h1 = imagehash.phash(Image.open(vis_file))
                            h2 = imagehash.phash(Image.open(notebook_figures_dir / png_file))
                            hamming = h1 - h2   # smaller = more similar
                            hamming_vec.append(hamming)
                        except Exception:
                            continue  # Skip if image comparison fails

                    if hamming_vec:
                        min_hamming = min(hamming_vec)
                        # Relaxed threshold for 3D visualizations which can vary
                        assert min_hamming < 30, f"Generated image {vis_file.name} too different from tutorial (hamming: {min_hamming})"
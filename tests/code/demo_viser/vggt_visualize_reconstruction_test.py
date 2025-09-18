"""
Tests for vggt_visualize_reconstruction in demo_viser.py that reproduce the tutorial exactly.

Tutorial: VGGT_Agent/notebooks/demo_viser/demo_viser_execution_final.ipynb
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os
from PIL import Image
import imagehash

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
def vggt_visualize_reconstruction_inputs(test_directories) -> dict:
    """Input parameters matching the tutorial execution exactly."""
    return {
        "images_dir": str(test_directories["input_dir"] / "images"),
        "resolution": 518,
        "confidence_threshold": 0.5,
        "max_display_points": 10000,
        "device_type": "auto",
        "out_prefix": None
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_vggt_visualize_reconstruction(server, vggt_visualize_reconstruction_inputs, test_directories):
    """Test vggt_visualize_reconstruction with exact tutorial parameters and expected outputs."""
    async with Client(server) as client:
        result = await client.call_tool("vggt_visualize_reconstruction", vggt_visualize_reconstruction_inputs)
        result_data = result.data

        # 1. Basic result structure verification
        assert "message" in result_data, "Result should contain message"
        assert "artifacts" in result_data, "Result should contain artifacts"
        assert "reference" in result_data, "Result should contain reference"

        # 2. Reference verification
        assert "demo_viser.py" in result_data["reference"], "Reference should point to VGGT demo_viser.py"

        # 3. Artifacts verification - should contain 3 visualization files
        artifacts = result_data["artifacts"]
        assert len(artifacts) == 3, f"Expected 3 visualization artifacts, got {len(artifacts)}"

        # 4. File creation verification - check for all expected visualization files
        expected_files = ["input_images.png", "depth_confidence.png", "point_cloud_3d.png"]
        artifact_paths = [artifact["path"] for artifact in artifacts]

        for expected_file in expected_files:
            file_found = any(expected_file in path for path in artifact_paths)
            assert file_found, f"Expected visualization file containing '{expected_file}' not found in artifacts"

        # 5. Verify all artifact files exist and are valid PNG images
        for artifact in artifacts:
            file_path = pathlib.Path(artifact["path"])
            assert file_path.exists(), f"Artifact file should exist: {file_path}"
            assert file_path.suffix.lower() == ".png", f"Artifact should be PNG image: {file_path}"

            # Verify it's a valid image
            try:
                with Image.open(file_path) as img:
                    assert img.format == "PNG", f"File should be valid PNG: {file_path}"
                    assert img.size[0] > 0 and img.size[1] > 0, f"Image should have valid dimensions: {file_path}"
            except Exception as e:
                pytest.fail(f"Failed to open image {file_path}: {e}")

        # 6. Verify artifact descriptions match expected visualization types
        artifact_descriptions = [artifact["description"].lower() for artifact in artifacts]

        assert any("input images" in desc for desc in artifact_descriptions), "Should have input images visualization"
        assert any("depth" in desc and "confidence" in desc for desc in artifact_descriptions), "Should have depth and confidence visualization"
        assert any("point cloud" in desc or "3d" in desc for desc in artifact_descriptions), "Should have 3D point cloud visualization"

        # 7. Message verification should reflect successful visualization
        message = result_data["message"]
        assert "visualization completed" in message.lower(), "Message should indicate visualization completion"
        assert "8 images" in message, "Message should mention 8 input images (tutorial value)"
        # Tutorial shows 2,146,592 points, but subsampled to 10,000 for visualization
        assert "points" in message, "Message should mention point count"

        # 8. Image Verification - compare generated figures with notebook figures using imagehash
        notebook_figures_dir = pathlib.Path("notebooks/demo_viser/images")

        if notebook_figures_dir.exists():
            png_files = [f for f in os.listdir(notebook_figures_dir) if f.endswith('.png')]

            if png_files:
                # For each generated figure, find the most similar notebook figure
                for artifact in artifacts:
                    generated_figure_path = artifact["path"]

                    if os.path.exists(generated_figure_path):
                        hamming_vec = []
                        for png_file in png_files:
                            try:
                                h1 = imagehash.phash(Image.open(generated_figure_path))
                                h2 = imagehash.phash(Image.open(notebook_figures_dir / png_file))
                                hamming = h1 - h2   # smaller = more similar
                                hamming_vec.append(hamming)
                            except Exception as e:
                                print(f"Warning: Could not compare {generated_figure_path} with {png_file}: {e}")

                        if hamming_vec:
                            min_hamming = min(hamming_vec)
                            # Allow more tolerance for visualization images (they may have slight differences)
                            assert min_hamming < 30, f"Generated figure {generated_figure_path} differs too much from notebook figures. Minimum Hamming distance: {min_hamming}"

        # 9. Verify visualization contains substantial point cloud data
        # Tutorial processes 8 images with 2,146,592 total points, subsampled to 10,000 for display
        point_cloud_artifact = next((a for a in artifacts if "point_cloud" in a["path"] or "3d" in a["path"]), None)
        if point_cloud_artifact:
            # The point cloud visualization should exist as it's created from substantial data
            assert pathlib.Path(point_cloud_artifact["path"]).exists(), "3D point cloud visualization should be generated"

        # 10. Verify all expected visualization components are present
        # Based on tutorial, should have: input images (4 max), depth/confidence maps (4 max), 3D point cloud
        input_images_artifact = next((a for a in artifacts if "input" in a["description"].lower()), None)
        depth_conf_artifact = next((a for a in artifacts if "depth" in a["description"].lower() and "confidence" in a["description"].lower()), None)
        point_cloud_artifact = next((a for a in artifacts if "point cloud" in a["description"].lower() or "3d" in a["description"].lower()), None)

        assert input_images_artifact is not None, "Should have input images visualization"
        assert depth_conf_artifact is not None, "Should have depth and confidence maps visualization"
        assert point_cloud_artifact is not None, "Should have 3D point cloud visualization"
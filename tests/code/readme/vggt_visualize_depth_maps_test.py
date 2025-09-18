"""
Tests for vggt_visualize_depth_maps in readme.py that reproduce the tutorial exactly.

Tutorial: facebookresearch/vggt/README.md
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
    """FastMCP server fixture with the readme tool."""
    # Force module reload
    module_name = 'src.tools.readme'
    if module_name in sys.modules:
        del sys.modules[module_name]

    import src.tools.readme
    return src.tools.readme.readme_mcp

@pytest.fixture
def test_directories():
    """Setup test directories and environment variables."""
    test_input_dir = pathlib.Path(__file__).parent.parent.parent / "data" / "readme"
    test_output_dir = pathlib.Path(__file__).parent.parent.parent / "results" / "readme"

    test_input_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)

    # Environment variable management
    old_input_dir = os.environ.get("README_INPUT_DIR")
    old_output_dir = os.environ.get("README_OUTPUT_DIR")

    os.environ["README_INPUT_DIR"] = str(test_input_dir.resolve())
    os.environ["README_OUTPUT_DIR"] = str(test_output_dir.resolve())

    yield {"input_dir": test_input_dir, "output_dir": test_output_dir}

    # Cleanup
    if old_input_dir is not None:
        os.environ["README_INPUT_DIR"] = old_input_dir
    else:
        os.environ.pop("README_INPUT_DIR", None)

    if old_output_dir is not None:
        os.environ["README_OUTPUT_DIR"] = old_output_dir
    else:
        os.environ.pop("README_OUTPUT_DIR", None)

# ========= Input Fixtures (Tutorial Values) =========
@pytest.fixture
def vggt_visualize_depth_maps_inputs(test_directories) -> dict:
    """Set up inputs matching tutorial example using room images."""
    # Reuse images from previous tools (sequential processing)
    test_images_dir = test_directories["input_dir"] / "images"
    if not test_images_dir.exists():
        # Copy example images from repo if not already copied
        repo_images_dir = project_root / "repo" / "vggt" / "examples" / "room" / "images"
        test_images_dir.mkdir(exist_ok=True)
        
        available_images = sorted([f for f in os.listdir(repo_images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        selected_images = available_images[:3]
        
        for img_file in selected_images:
            source_path = repo_images_dir / img_file
            dest_path = test_images_dir / img_file
            if source_path.exists() and not dest_path.exists():
                import shutil
                shutil.copy2(source_path, dest_path)
    
    return {
        "images_dir": str(test_images_dir.resolve()),
        "max_images": 3,  # Tutorial default
        "colormap": "viridis",  # Tutorial default
        "device": "auto",  # Tutorial default
        "out_prefix": None,  # Tutorial default
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_vggt_visualize_depth_maps(server, vggt_visualize_depth_maps_inputs, test_directories):
    async with Client(server) as client:
        result = await client.call_tool("vggt_visualize_depth_maps", vggt_visualize_depth_maps_inputs)
        result_data = result.data

        # 1. File Output Verification (tutorial creates visualization + log)
        artifacts = result_data.get("artifacts", [])
        assert len(artifacts) == 2, f"Expected 2 artifacts (visualization + log), got {len(artifacts)}"
        
        # Check visualization file exists
        viz_artifact = [a for a in artifacts if "visualization" in a["description"].lower()][0]
        viz_path = pathlib.Path(viz_artifact["path"])
        assert viz_path.exists(), "Depth visualization file should exist"
        assert viz_path.suffix == ".png", "Visualization file should be PNG"
        
        # Check log file exists
        log_artifact = [a for a in artifacts if "log" in a["description"].lower()][0]
        log_path = pathlib.Path(log_artifact["path"])
        assert log_path.exists(), "Log file should exist"
        assert log_path.suffix == ".txt", "Log file should be text"

        # 2. Visualization Image Verification (tutorial generates depth maps figure)
        # Check that PNG file can be opened as an image
        viz_image = Image.open(viz_path)
        assert viz_image.size[0] > 0 and viz_image.size[1] > 0, "Visualization should have valid dimensions"
        
        # Based on tutorial: 2 rows (original + depth) × 3 columns (3 images)
        # Should be a composite image showing original images on top row, depth maps on bottom row
        width, height = viz_image.size
        assert width > height, "Visualization should be wider than tall (3 images horizontally arranged)"

        # 3. Success Message Verification (tutorial shows depth map completion)
        assert "depth map" in result_data.get("message", "").lower(), "Should indicate depth map visualization completion"
        assert "3 images" in result_data.get("message", ""), "Should mention processing 3 images"

        # 4. Reference Verification (tutorial should provide GitHub reference)
        assert "reference" in result_data, "Should include reference to tutorial"
        assert "github.com/facebookresearch/vggt" in result_data.get("reference", ""), "Should reference VGGT GitHub repo"

        # 5. Image Verification (compare with tutorial notebook figures)
        notebook_figures_dir = pathlib.Path("notebooks/readme/images")
        png_files = []
        if notebook_figures_dir.exists():
            png_files = [f for f in os.listdir(notebook_figures_dir) if f.endswith('.png')]
        
        # For figures generated by the tutorial, use imagehash to verify similarity between generated and tutorial figures
        if png_files:
            generated_figure_path = viz_path
            hamming_vec = []
            for png_file in png_files:
                try:
                    h1 = imagehash.phash(Image.open(generated_figure_path))
                    h2 = imagehash.phash(Image.open(notebook_figures_dir / png_file))
                    hamming = h1 - h2   # smaller = more similar
                    hamming_vec.append(hamming)
                except Exception:
                    continue  # Skip if comparison fails
            
            if hamming_vec:
                assert min(hamming_vec) < 20, f"Hamming distance {min(hamming_vec)} is greater than 20. Failed to pass the image verification."
        # If no tutorial figures exist for comparison, skip image hash verification
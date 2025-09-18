"""
Tests for vggt_quick_start_inference in readme.py that reproduce the tutorial exactly.

Tutorial: VGGT Basic Inference - from notebooks/readme/readme_execution_final.ipynb
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
    test_input_dir = pathlib.Path(__file__).parent.parent.parent/ "data" / "readme"
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
def vggt_quick_start_inference_inputs(test_directories) -> dict:
    return {
        "images_dir": str(test_directories["input_dir"] / "images"),  # From tutorial data setup
        "max_images": 3,  # Tutorial default: "Use first 3 images (or all if less than 3)"
        "device": "auto",  # Tutorial default
        "out_prefix": None,  # Tutorial default - uses timestamp
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_vggt_quick_start_inference(server, vggt_quick_start_inference_inputs, test_directories):
    async with Client(server) as client:
        result = await client.call_tool("vggt_quick_start_inference", vggt_quick_start_inference_inputs)
        result_data = result.data

        # 1. Basic result structure verification
        assert "message" in result_data, "Result should contain message"
        assert "artifacts" in result_data, "Result should contain artifacts"
        assert "reference" in result_data, "Result should contain reference"

        # 2. Message verification (tutorial shows successful completion)
        expected_message_part = "VGGT inference completed on 3 images successfully"
        assert expected_message_part in result_data["message"], f"Expected message containing '{expected_message_part}'"

        # 3. Reference verification (tutorial shows GitHub reference)
        assert "github.com/facebookresearch/vggt" in result_data["reference"], "Should reference VGGT GitHub repository"

        # 4. File Output Verification (tutorial creates results and log files)
        artifacts = result_data.get("artifacts", [])
        assert len(artifacts) == 2, f"Expected 2 artifacts (results + log), got {len(artifacts)}"

        # Check for results file
        results_artifact = next((a for a in artifacts if "results" in a["description"].lower()), None)
        assert results_artifact is not None, "Should have results artifact"
        results_path = pathlib.Path(results_artifact["path"])
        assert results_path.exists(), f"Results file should exist: {results_path}"
        assert results_path.suffix == ".csv", "Results should be CSV file"

        # Check for log file
        log_artifact = next((a for a in artifacts if "log" in a["description"].lower()), None)
        assert log_artifact is not None, "Should have log artifact"
        log_path = pathlib.Path(log_artifact["path"])
        assert log_path.exists(), f"Log file should exist: {log_path}"
        assert log_path.suffix == ".txt", "Log should be text file"

        # 5. Results file content verification (tutorial shows specific prediction keys)
        import pandas as pd
        results_df = pd.read_csv(results_path)

        # Tutorial shows 3 images processed
        assert len(results_df) == 3, f"Expected 3 rows for 3 images, got {len(results_df)}"

        # Tutorial shows specific columns in results
        expected_columns = ['image_index', 'image_filename', 'pose_enc_shape', 'depth_shape', 'world_points_shape']
        for col in expected_columns:
            assert col in results_df.columns, f"Expected column '{col}' in results"

        # 6. Results content verification (tutorial shows specific prediction structure)
        # Tutorial shows predictions with keys: ['pose_enc', 'pose_enc_list', 'depth', 'depth_conf', 'world_points', 'world_points_conf']
        for i in range(3):
            row = results_df.iloc[i]
            assert row['image_index'] == i, f"Row {i} should have image_index {i}"
            # Check that filename contains image extension (actual files from VGGT examples)
            assert any(ext in row['image_filename'].lower() for ext in ['.png', '.jpg', '.jpeg']), f"Row {i} should reference image file"

            # Verify shape strings contain expected dimensions (from tutorial output)
            assert 'torch.Size' in row['pose_enc_shape'], "pose_enc should have torch.Size format"
            assert 'torch.Size' in row['depth_shape'], "depth should have torch.Size format"
            assert 'torch.Size' in row['world_points_shape'], "world_points should have torch.Size format"

        # 7. Log file content verification (tutorial shows specific log messages)
        with open(log_path, 'r') as f:
            log_content = f.read()

        # Tutorial shows these key log messages
        expected_log_messages = [
            "Using device:",
            "Using dtype:",
            "Found 3 images:",
            "Loading VGGT model...",
            "Model loaded successfully!",
            "Loading and preprocessing images...",
            "Running VGGT inference...",
            "Inference completed!",
            "Predictions keys:"
        ]

        for expected_msg in expected_log_messages:
            assert expected_msg in log_content, f"Expected log message: '{expected_msg}'"

        # 8. Image Verification (when tutorial shows images, need to skip as this is basic inference without image output)
        # This tool only processes images for inference, no figure generation, so skip image verification section
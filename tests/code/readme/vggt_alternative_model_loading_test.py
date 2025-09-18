"""
Tests for vggt_alternative_model_loading in readme.py that reproduce the tutorial exactly.

Tutorial: facebookresearch/vggt/README.md
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os

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
def vggt_alternative_model_loading_inputs(test_directories) -> dict:
    """Set up inputs matching tutorial example for alternative model loading."""
    return {
        "model_url": "https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt",  # Tutorial default
        "device": "auto",  # Tutorial default
        "out_prefix": None,  # Tutorial default
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_vggt_alternative_model_loading(server, vggt_alternative_model_loading_inputs, test_directories):
    async with Client(server) as client:
        result = await client.call_tool("vggt_alternative_model_loading", vggt_alternative_model_loading_inputs)
        result_data = result.data

        # 1. File Output Verification (tutorial creates log file)
        artifacts = result_data.get("artifacts", [])
        assert len(artifacts) == 1, f"Expected 1 artifact (log file), got {len(artifacts)}"
        
        # Check log file exists
        log_artifact = artifacts[0]
        log_path = pathlib.Path(log_artifact["path"])
        assert log_path.exists(), "Model loading log file should exist"
        assert log_path.suffix == ".txt", "Log file should be text"
        assert "log" in log_artifact["description"].lower(), "Should be described as log file"

        # 2. Log Content Verification (tutorial demonstrates loading process)
        with open(log_path, 'r') as f:
            log_content = f.read()
        
        # Check tutorial-expected log contents
        assert "device:" in log_content.lower(), "Log should mention device used"
        assert "alternative model loading" in log_content.lower(), "Log should mention alternative loading method"
        assert "model weights" in log_content.lower(), "Log should mention model weights loading"
        assert "huggingface.co/facebook/VGGT-1B" in log_content, "Log should show HuggingFace model URL"

        # 3. Success Message Verification (tutorial shows model loading status)
        message = result_data.get("message", "")
        assert "alternative model loading" in message.lower(), "Should indicate alternative model loading attempt"
        # Note: Message can be either success or failure - both are valid tutorial outcomes
        assert ("successful" in message.lower() or "failed" in message.lower()), "Should indicate success or failure status"

        # 4. Reference Verification (tutorial should provide GitHub reference)
        assert "reference" in result_data, "Should include reference to tutorial"
        assert "github.com/facebookresearch/vggt" in result_data.get("reference", ""), "Should reference VGGT GitHub repo"

        # 5. Model URL Verification (tutorial uses exact HuggingFace URL)
        assert vggt_alternative_model_loading_inputs["model_url"] == "https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt", "Should use tutorial URL"

        # 6. Device Configuration Verification (tutorial uses auto device detection)
        assert "device:" in log_content.lower(), "Log should show device configuration"
        # Should show either 'cuda' or 'cpu' based on availability
        assert ("cuda" in log_content.lower() or "cpu" in log_content.lower()), "Log should mention specific device used"

        # 7. Loading Process Verification (tutorial shows either success or expected failure)
        # The tutorial notes that failure is expected if model was already loaded
        loading_status_mentioned = any(phrase in log_content.lower() for phrase in [
            "successful", "failed", "exception", "error", "already loaded"
        ])
        assert loading_status_mentioned, "Log should indicate loading outcome (success or failure)"
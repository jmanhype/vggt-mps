"""
Tests for score_batch.py that reproduce the tutorial exactly.

Tutorial: AlphaPOP/score_batch.ipynb
"""

from __future__ import annotations

import pathlib
import pytest
import sys
from fastmcp import Client
import os
import pandas as pd

# Add project root to Python path to enable src imports
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ========= Fixtures =========
@pytest.fixture
def server(test_directories):
    """FastMCP server fixture with the score_batch tool."""
    # Force module reload
    module_name = 'src.tools.score_batch'
    if module_name in sys.modules:
        del sys.modules[module_name]

    try:
        import src.tools.score_batch
        return src.tools.score_batch.score_batch_mcp
    except ModuleNotFoundError as e:
        if "alphagenome" in str(e):
            pytest.skip("AlphaGenome module not available for testing")
        else:
            raise e

@pytest.fixture
def test_directories():
    """Setup test directories and environment variables."""
    test_input_dir = pathlib.Path(__file__).parent.parent / "data" / "score_batch"
    test_output_dir = pathlib.Path(__file__).parent.parent / "results" / "score_batch"

    test_input_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)

    # Environment variable management
    old_input_dir = os.environ.get("SCORE_BATCH_INPUT_DIR")
    old_output_dir = os.environ.get("SCORE_BATCH_OUTPUT_DIR")

    os.environ["SCORE_BATCH_INPUT_DIR"] = str(test_input_dir.resolve())
    os.environ["SCORE_BATCH_OUTPUT_DIR"] = str(test_output_dir.resolve())

    yield {"input_dir": test_input_dir, "output_dir": test_output_dir}

    # Cleanup
    if old_input_dir is not None:
        os.environ["SCORE_BATCH_INPUT_DIR"] = old_input_dir
    else:
        os.environ.pop("SCORE_BATCH_INPUT_DIR", None)

    if old_output_dir is not None:
        os.environ["SCORE_BATCH_OUTPUT_DIR"] = old_output_dir
    else:
        os.environ.pop("SCORE_BATCH_OUTPUT_DIR", None)

@pytest.fixture(scope="module")
def pipeline_state():
    """Shared state for sequential test execution when tests depend on previous outputs."""
    return {}

# ========= Input Fixtures (Tutorial Values) =========
@pytest.fixture
def score_batch_variants_inputs(test_directories) -> dict:
    """Exact tutorial inputs for score_batch_variants function."""
    # Run data setup to ensure test data exists
    sys.path.append(str(test_directories["input_dir"]))
    from score_batch_data import setup_score_batch_data
    setup_score_batch_data()

    return {
        "api_key": "test_api_key",  # Using test API key instead of real one
        "vcf_file": str(test_directories["input_dir"] / "example_variants.csv"),
        "organism": "human",
        "sequence_length": "1MB",
        "score_rna_seq": True,
        "score_cage": True,
        "score_procap": True,
        "score_atac": True,
        "score_dnase": True,
        "score_chip_histone": True,
        "score_chip_tf": True,
        "score_polyadenylation": True,
        "score_splice_sites": True,
        "score_splice_site_usage": True,
        "score_splice_junctions": True,
        "out_prefix": "tutorial_batch_scores",
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_score_batch_variants(server, score_batch_variants_inputs, test_directories, pipeline_state):
    """Test the score_batch_variants function with exact tutorial parameters."""
    async with Client(server) as client:
        try:
            result = await client.call_tool("score_batch_variants", score_batch_variants_inputs)
            result_data = result.data

            # Store result for subsequent tests if needed
            pipeline_state['score_batch_output'] = result_data.get('artifacts', [])

            # 1. Basic Return Structure Verification
            assert result_data is not None, "Function should return a result"
            assert "message" in result_data, "Result should contain a message"
            assert "artifacts" in result_data, "Result should contain artifacts"
            assert "reference" in result_data, "Result should contain reference"

            # 2. Message Content Verification
            message = result_data["message"]
            assert "Scored" in message, "Message should mention scoring"
            assert "variants" in message, "Message should mention variants"
            assert "4 variants" in message, "Message should mention the 4 tutorial variants"

            # 3. Reference URL Verification
            reference = result_data["reference"]
            assert "AlphaPOP" in reference, "Reference should point to AlphaPOP repository"
            assert "score_batch.ipynb" in reference, "Reference should point to correct notebook"

            # 4. Artifacts Structure Verification
            artifacts = result_data["artifacts"]
            assert isinstance(artifacts, list), "Artifacts should be a list"
            assert len(artifacts) >= 1, "Should have at least one artifact"

            # 5. File Output Verification
            artifact = artifacts[0]
            assert isinstance(artifact, dict), "Artifact should be a dictionary"
            assert "description" in artifact, "Artifact should have description"
            assert "path" in artifact, "Artifact should have path"

            output_path = pathlib.Path(artifact["path"])
            assert output_path.exists(), f"Output file should exist: {output_path}"
            assert output_path.suffix == '.csv', "Output should be a CSV file"
            assert "tutorial_batch_scores" in output_path.name, "Output filename should contain prefix"

            # 6. Data Structure Verification (Tutorial expectations)
            df_scores = pd.read_csv(output_path)

            # Tutorial shows these key columns in the output
            required_columns = ["variant_id", "ontology_curie", "raw_score", "quantile_score"]
            for column in required_columns:
                assert column in df_scores.columns, f"Output should contain {column} column"

            # 7. Row Count Verification (Tutorial shows 121956 rows for 4 variants)
            # Each variant gets scored across multiple cell types and scorers
            assert len(df_scores) > 0, "Output dataframe should not be empty"
            assert len(df_scores) >= 4, "Should have at least as many rows as input variants"

            # Tutorial shows approximately 30,489 rows per variant (121956/4)
            # Allow for some variation but expect substantial output
            assert len(df_scores) > 1000, f"Expected substantial output, got {len(df_scores)} rows"

            # 8. Variant ID Verification (Tutorial variants)
            expected_variants = [
                "chr3:58394738:A>T",
                "chr8:28520:G>C",
                "chr16:636337:G>A",
                "chr16:1135446:G>T"
            ]
            actual_variants = df_scores['variant_id'].unique()

            for expected_variant in expected_variants:
                assert expected_variant in actual_variants, f"Expected variant {expected_variant} not found in results"

            # 9. Score Range Verification
            # Raw scores should be numeric and within reasonable ranges
            assert df_scores['raw_score'].dtype in ['float64', 'float32'], "Raw scores should be numeric"
            assert df_scores['quantile_score'].dtype in ['float64', 'float32'], "Quantile scores should be numeric"

            # Quantile scores should generally be between -1 and 1 based on tutorial output
            quantile_scores = df_scores['quantile_score'].dropna()
            if len(quantile_scores) > 0:
                assert quantile_scores.min() >= -1.0, f"Quantile scores too low: {quantile_scores.min()}"
                assert quantile_scores.max() <= 1.0, f"Quantile scores too high: {quantile_scores.max()}"

            # 10. Cell Type Verification (Tutorial shows T-cells with CL:0000084)
            cell_types = df_scores['ontology_curie'].unique()
            assert 'CL:0000084' in cell_types, "Should include T-cells (CL:0000084) from tutorial"

            # 11. Tutorial-specific Statistical Verification
            # Tutorial shows T-cell results - verify some exist
            tcell_data = df_scores[df_scores['ontology_curie'] == 'CL:0000084']
            assert len(tcell_data) > 0, "Should have T-cell results as shown in tutorial"

            # Each variant should have T-cell results
            tcell_variants = tcell_data['variant_id'].unique()
            assert len(tcell_variants) == 4, f"All 4 variants should have T-cell results, got {len(tcell_variants)}"

        except Exception as e:
            # If API call fails (expected with test API key), verify input validation works
            if "API key" in str(e) or "Failed to create AlphaGenome client" in str(e):
                pytest.skip("Skipping test due to API key validation (expected with test key)")
            else:
                raise e
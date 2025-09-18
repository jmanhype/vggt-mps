"""
Batch variant scoring using AlphaGenome for genomic variant analysis.

This MCP Server provides 1 tool:
1. score_batch_variants: Score variants in batch across modalities using AlphaGenome

All tools extracted from `AlphaPOP/score_batch.ipynb`.
"""

# Standard imports
from typing import Annotated, Literal
import pandas as pd
from pathlib import Path
import os
from fastmcp import FastMCP
from datetime import datetime
from tqdm import tqdm
from alphagenome.data import genome
from alphagenome.models import dna_client, variant_scorers

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_INPUT_DIR = PROJECT_ROOT / "tmp" / "inputs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

INPUT_DIR = Path(os.environ.get("SCORE_BATCH_INPUT_DIR", DEFAULT_INPUT_DIR))
OUTPUT_DIR = Path(os.environ.get("SCORE_BATCH_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Timestamp for unique outputs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# MCP server instance
score_batch_mcp = FastMCP(name="score_batch")

@score_batch_mcp.tool
def score_batch_variants(
    api_key: Annotated[str, "API key for the AlphaGenome model"],
    vcf_file: Annotated[str | None, "Path to VCF/TSV/CSV file with extension .vcf, .tsv, or .csv. The header should include columns: variant_id, CHROM, POS, REF, ALT"] = None,
    organism: Annotated[Literal["human", "mouse"], "Organism to score against"] = "human",
    sequence_length: Annotated[Literal["2KB", "16KB", "100KB", "500KB", "1MB"], "Context window"] = "1MB",
    score_rna_seq: Annotated[bool, "Include RNA-seq signal prediction"] = True,
    score_cage: Annotated[bool, "Include CAGE"] = True,
    score_procap: Annotated[bool, "Include PRO-cap (human only)"] = True,
    score_atac: Annotated[bool, "Include ATAC"] = True,
    score_dnase: Annotated[bool, "Include DNase"] = True,
    score_chip_histone: Annotated[bool, "Include ChIP-histone"] = True,
    score_chip_tf: Annotated[bool, "Include ChIP-transcription-factor"] = True,
    score_polyadenylation: Annotated[bool, "Include polyadenylation"] = True,
    score_splice_sites: Annotated[bool, "Include splice sites"] = True,
    score_splice_site_usage: Annotated[bool, "Include splice site usage"] = True,
    score_splice_junctions: Annotated[bool, "Include splice junctions"] = True,
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Score genetic variants in batch across multiple regulatory modalities using AlphaGenome.
    Input is VCF/TSV/CSV file with variant information and output is variant scores table.
    """
    # Input file validation only
    if vcf_file is None:
        raise ValueError("Path to VCF/TSV/CSV file must be provided")

    # File existence validation
    vcf_path = Path(vcf_file)
    if not vcf_path.exists():
        raise FileNotFoundError(f"Input file not found: {vcf_file}")

    # Load data
    sep = "\t" if vcf_path.suffix.lower() in {".vcf", ".tsv"} else ","
    vcf = pd.read_csv(str(vcf_path), sep=sep)

    # Create model
    dna_model = dna_client.create(api_key)

    # Parse organism specification
    organism_map = {
        "human": dna_client.Organism.HOMO_SAPIENS,
        "mouse": dna_client.Organism.MUS_MUSCULUS,
    }
    organism_enum = organism_map[organism]

    # Parse sequence length specification
    sequence_length_enum = dna_client.SUPPORTED_SEQUENCE_LENGTHS[
        f"SEQUENCE_LENGTH_{sequence_length}"
    ]

    # Parse scorer specification
    scorer_selections = {
        "rna_seq": score_rna_seq,
        "cage": score_cage,
        "procap": score_procap,
        "atac": score_atac,
        "dnase": score_dnase,
        "chip_histone": score_chip_histone,
        "chip_tf": score_chip_tf,
        "polyadenylation": score_polyadenylation,
        "splice_sites": score_splice_sites,
        "splice_site_usage": score_splice_site_usage,
        "splice_junctions": score_splice_junctions,
    }

    all_scorers = variant_scorers.RECOMMENDED_VARIANT_SCORERS
    selected_scorers = [
        all_scorers[key]
        for key in all_scorers
        if scorer_selections.get(key.lower(), False)
    ]

    # Remove any scorers that are not supported for the chosen organism
    unsupported_scorers = [
        scorer
        for scorer in selected_scorers
        if (
            organism_enum.value
            not in variant_scorers.SUPPORTED_ORGANISMS[scorer.base_variant_scorer]
        )
        or (
            (scorer.requested_output == dna_client.OutputType.PROCAP)
            and (organism_enum == dna_client.Organism.MUS_MUSCULUS)
        )
    ]
    if len(unsupported_scorers) > 0:
        for unsupported_scorer in unsupported_scorers:
            selected_scorers.remove(unsupported_scorer)

    # Score variants in the VCF file
    results = []
    for _, vcf_row in tqdm(vcf.iterrows(), total=len(vcf), desc="Scoring variants"):
        variant = genome.Variant(
            chromosome=str(vcf_row.CHROM),
            position=int(vcf_row.POS),
            reference_bases=vcf_row.REF,
            alternate_bases=vcf_row.ALT,
            name=vcf_row.variant_id,
        )
        interval = variant.reference_interval.resize(sequence_length_enum)

        variant_scores = dna_model.score_variant(
            interval=interval,
            variant=variant,
            variant_scorers=selected_scorers,
            organism=organism_enum,
        )
        results.append(variant_scores)

    # Process results
    df_scores = variant_scorers.tidy_scores(results)

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"score_batch_variants_{timestamp}"

    # Save results
    download_path = OUTPUT_DIR / f"{out_prefix}.csv"
    download_path.write_text(df_scores.to_csv(index=False))

    # Return standardized format
    return {
        "message": f"Scored {len(vcf)} variants and saved results table",
        "reference": "https://github.com/AlphaPOP/blob/main/score_batch.ipynb",
        "artifacts": [
            {
                "description": "Variant scores results table",
                "path": str(download_path.resolve())
            }
        ]
    }
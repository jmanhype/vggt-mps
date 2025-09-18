"""
Data setup script for score_batch tutorial tests.
Creates the example VCF data from the tutorial.
"""

from pathlib import Path

def setup_score_batch_data():
    """Create the example VCF data from the tutorial."""
    # Create the test data directory
    data_dir = Path(__file__).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    # Example VCF data from the tutorial (tab-separated as in original)
    vcf_data = """variant_id\tCHROM\tPOS\tREF\tALT
chr3_58394738_A_T_b38\tchr3\t58394738\tA\tT
chr8_28520_G_C_b38\tchr8\t28520\tG\tC
chr16_636337_G_A_b38\tchr16\t636337\tG\tA
chr16_1135446_G_T_b38\tchr16\t1135446\tG\tT"""

    # Save as CSV file for testing
    vcf_path = data_dir / "example_variants.csv"
    with open(vcf_path, 'w') as f:
        f.write(vcf_data)

    print(f"Created test data file: {vcf_path}")
    return str(vcf_path)

if __name__ == "__main__":
    setup_score_batch_data()
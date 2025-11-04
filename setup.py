"""
VGGT MPS - 3D Reconstruction with Sparse Attention
Setup script for installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="vggt-mps",
    version="2.0.0",
    author="VGGT MPS Contributors",
    description="VGGT 3D reconstruction optimized for Apple Silicon with sparse attention",
    long_description=long_description,
    long_description_content_type="markdown",
    url="https://github.com/jmanhype/vggt-mps",
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: MacOS",
        "Environment :: GPU :: Metal",
    ],
    python_requires=">=3.10",
    install_requires=[
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "numpy>=1.24.0",
        "pillow>=9.5.0",
        "matplotlib>=3.7.0",
        "scipy>=1.10.0",
        "tqdm>=4.65.0",
        "einops>=0.6.1",
        "transformers>=4.30.0",
        "huggingface-hub>=0.16.0",
        "timm>=0.9.0",
        "opencv-python>=4.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "web": [
            "gradio>=3.40.0",
            "plotly>=5.15.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vggt=vggt_mps.__main__:main",
            "vggt-mps=vggt_mps.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
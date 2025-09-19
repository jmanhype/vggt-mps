"""
MPS (Metal Performance Shaders) tests for VGGT
"""

import unittest
import torch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import DEVICE


class TestMPSSupport(unittest.TestCase):
    """Test MPS availability and basic functionality"""

    def test_mps_available(self):
        """Test that MPS is available on this system"""
        if torch.backends.mps.is_available():
            self.assertTrue(torch.backends.mps.is_available())
            print("✅ MPS (Metal Performance Shaders) available!")
            print(f"   Running on Apple Silicon GPU")
        else:
            self.skipTest("MPS not available on this system")

    def test_device_selection(self):
        """Test correct device selection"""
        self.assertIn(str(DEVICE), ['mps', 'cuda', 'cpu'])
        print(f"✅ Device selected: {DEVICE}")

    def test_tensor_to_mps(self):
        """Test moving tensors to MPS"""
        if not torch.backends.mps.is_available():
            self.skipTest("MPS not available")

        tensor = torch.randn(10, 10)
        mps_tensor = tensor.to('mps')
        self.assertEqual(str(mps_tensor.device), 'mps:0')
        print("✅ Tensors can be moved to MPS")


class TestMPSOperations(unittest.TestCase):
    """Test MPS operations and performance"""

    def setUp(self):
        if not torch.backends.mps.is_available():
            self.skipTest("MPS not available")

    def test_matrix_multiplication(self):
        """Test matrix multiplication on MPS"""
        a = torch.randn(100, 100).to('mps')
        b = torch.randn(100, 100).to('mps')
        c = torch.matmul(a, b)
        self.assertEqual(c.shape, (100, 100))
        self.assertEqual(str(c.device), 'mps:0')
        print("✅ Matrix multiplication works on MPS")

    def test_convolution(self):
        """Test convolution operations on MPS"""
        conv = torch.nn.Conv2d(3, 16, 3).to('mps')
        x = torch.randn(1, 3, 32, 32).to('mps')
        y = conv(x)
        self.assertEqual(y.shape, (1, 16, 30, 30))
        print("✅ Convolution operations work on MPS")

    def test_attention(self):
        """Test attention operations on MPS"""
        # Simple attention mechanism
        q = torch.randn(1, 8, 64).to('mps')
        k = torch.randn(1, 8, 64).to('mps')
        v = torch.randn(1, 8, 64).to('mps')

        scores = torch.matmul(q, k.transpose(-2, -1)) / 8.0
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, v)

        self.assertEqual(output.shape, (1, 8, 64))
        print("✅ Attention operations work on MPS")


if __name__ == '__main__':
    unittest.main()
"""
Test runner command for VGGT-MPS
Consolidates all tests into a single organized runner
"""

import sys
import unittest
from pathlib import Path
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def run_tests(args):
    """Run specified test suite"""
    print("=" * 60)
    print("🧪 VGGT Test Runner")
    print("=" * 60)
    print(f"Suite: {args.suite}")
    print("-" * 60)

    # Setup test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Get test directory
    test_dir = Path(__file__).parent.parent.parent / "tests"

    if args.suite == "quick":
        # Quick smoke tests
        print("Running quick smoke tests...")
        # Import with absolute path
        sys.path.insert(0, str(test_dir.parent))
        from tests.test_mps import TestMPSSupport
        suite.addTests(loader.loadTestsFromTestCase(TestMPSSupport))

    elif args.suite == "mps":
        # MPS-specific tests
        print("Running MPS tests...")
        sys.path.insert(0, str(test_dir.parent))
        from tests.test_mps import TestMPSSupport, TestMPSOperations
        suite.addTests(loader.loadTestsFromTestCase(TestMPSSupport))
        suite.addTests(loader.loadTestsFromTestCase(TestMPSOperations))

    elif args.suite == "sparse":
        # Sparse attention tests
        print("Running sparse attention tests...")
        sys.path.insert(0, str(test_dir.parent))
        from tests.test_sparse import TestSparseAttention, TestCovisibility
        suite.addTests(loader.loadTestsFromTestCase(TestSparseAttention))
        suite.addTests(loader.loadTestsFromTestCase(TestCovisibility))

    elif args.suite == "all":
        # All tests
        print("Running all tests...")
        suite = loader.discover(str(test_dir), pattern="test_*.py")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start_time

    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")

    print(f"⏱️  Time: {elapsed:.2f}s")
    print(f"📊 Tests run: {result.testsRun}")
    print("=" * 60)

    return 0 if result.wasSuccessful() else 1
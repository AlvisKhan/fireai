import unittest

from project_b.checks import KINDS, Baseline, inject, rules
from project_b.evaluate import synthetic_controls


class CorruptionTests(unittest.TestCase):
    def test_all_injections_are_reproducible_and_labeled(self):
        clean = synthetic_controls()
        for kind in KINDS:
            with self.subTest(kind=kind):
                first, labels = inject(clean, kind, 0.2, 312)
                self.assertEqual((first, labels), inject(clean, kind, 0.2, 312))
                self.assertEqual(labels, {i for i, row in enumerate(first) if row != clean[i]})

    def test_duplicate_anchors_remain_present(self):
        clean = synthetic_controls()
        for kind in ("duplicate", "near_duplicate"):
            changed, labels = inject(clean, kind, 0.2, 312)
            self.assertTrue(labels <= rules(kind, changed, Baseline(clean)).keys())


if __name__ == "__main__":
    unittest.main()

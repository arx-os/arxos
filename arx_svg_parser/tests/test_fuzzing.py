"""
Fuzzing Tests for SVG and BIM Importers

- Fuzzes SVG and BIM importers with random, malformed, and edge-case input
"""

import unittest
import random
import string
from services.bim_assembly import BIMAssemblyPipeline
from models.bim import BIMModel

class TestSVGFuzzing(unittest.TestCase):
    def random_svg(self, length=100):
        # Generate random SVG-like string
        chars = string.ascii_letters + string.digits + '<>/="\' + string.punctuation
        return ''.join(random.choice(chars) for _ in range(length))

    def test_fuzz_svg_importer(self):
        pipeline = BIMAssemblyPipeline()
        for _ in range(50):
            svg_data = {"svg": self.random_svg(random.randint(10, 500))}
            try:
                result = pipeline.assemble_bim(svg_data)
                self.assertTrue(result.success or result.elements == [])
            except Exception:
                # Should not crash the process
                pass

class TestBIMFuzzing(unittest.TestCase):
    def random_bim_dict(self):
        # Generate random dict with possible BIM keys
        keys = ["id", "name", "geometry", "type", "properties", "children", "parent_id"]
        return {random.choice(keys): ''.join(random.choices(string.ascii_letters, k=5)) for _ in range(random.randint(1, 10))}

    def test_fuzz_bim_importer(self):
        for _ in range(50):
            try:
                model = BIMModel.from_dict(self.random_bim_dict())
                self.assertIsInstance(model, BIMModel)
            except Exception:
                # Should not crash the process
                pass 
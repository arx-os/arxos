import unittest
from datetime import datetime
from services.nlp_cli_integration import NLPCLIIntegration, NLPCommand

class TestNLPCLIIntegration(unittest.TestCase):
    def setUp(self):
        self.nlp = NLPCLIIntegration()

    def test_create_command(self):
        cmd = self.nlp.parse_natural_language('create room')
        self.assertEqual(cmd.action, 'create')
        self.assertEqual(cmd.parameters['target'], 'room')
        self.assertGreater(cmd.confidence, 0.0)

    def test_add_command(self):
        cmd = self.nlp.parse_natural_language('add door')
        self.assertEqual(cmd.action, 'create')
        self.assertEqual(cmd.parameters['target'], 'door')
        self.assertGreater(cmd.confidence, 0.0)

    def test_modify_command(self):
        cmd = self.nlp.parse_natural_language('modify wall color')
        self.assertEqual(cmd.action, 'modify')
        self.assertEqual(cmd.parameters['target'], 'wall')
        self.assertIn('color', cmd.original_text)

    def test_move_command(self):
        cmd = self.nlp.parse_natural_language('move window')
        self.assertEqual(cmd.action, 'move')
        self.assertEqual(cmd.parameters['target'], 'window')

    def test_delete_command(self):
        cmd = self.nlp.parse_natural_language('delete chair')
        self.assertEqual(cmd.action, 'delete')
        self.assertEqual(cmd.parameters['target'], 'chair')

    def test_export_command(self):
        cmd = self.nlp.parse_natural_language('export plan')
        self.assertEqual(cmd.action, 'export')
        self.assertEqual(cmd.parameters['target'], 'plan')

    def test_color_and_size_extraction(self):
        cmd = self.nlp.parse_natural_language('create wall red 10x20')
        self.assertEqual(cmd.action, 'create')
        self.assertEqual(cmd.parameters['target'], 'wall')
        self.assertEqual(cmd.parameters['color'], 'red')
        self.assertEqual(cmd.parameters['width'], 10)
        self.assertEqual(cmd.parameters['height'], 20)

    def test_unknown_command(self):
        cmd = self.nlp.parse_natural_language('abracadabra foo bar')
        self.assertEqual(cmd.action, 'unknown')
        self.assertEqual(cmd.command_type, 'unknown')
        self.assertEqual(cmd.confidence, 0.0)

if __name__ == '__main__':
    unittest.main() 
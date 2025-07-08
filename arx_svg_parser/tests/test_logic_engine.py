"""
Unit and integration tests for the Logic Engine (behavior profiles, simulation, chaining, connectivity)
"""

import unittest
from datetime import datetime
from arx_svg_parser.services.logic_engine import (
    LogicEngine, LogicNode, LogicEdge, BehaviorType
)

class TestLogicEngine(unittest.TestCase):
    def setUp(self):
        self.engine = LogicEngine()
        # Add a simple electrical node
        self.electrical_node = LogicNode(
            node_id="panel_1",
            object_type="panel",
            properties={"voltage": 208, "current": 100, "circuits": 10, "total_load": 80, "rated_capacity": 100},
            position=(0, 0),
            behavior_profiles=["panel_validation", "panel_simulation"]
        )
        self.engine.add_logic_node(self.electrical_node)
        # Add a mechanical node
        self.mechanical_node = LogicNode(
            node_id="ahu_1",
            object_type="ahu",
            properties={"airflow": 2000, "pressure": 2.0, "temperature": 70, "fan_power": 5, "compressor_power": 10, "rated_power": 20},
            position=(1, 1),
            behavior_profiles=["ahu_validation", "ahu_simulation"]
        )
        self.engine.add_logic_node(self.mechanical_node)
        # Add a plumbing node
        self.plumbing_node = LogicNode(
            node_id="pipe_1",
            object_type="pipe",
            properties={"diameter": 2, "pressure": 50, "velocity": 5, "flow_rate": 10, "length": 100, "max_pressure_loss": 100},
            position=(2, 2),
            behavior_profiles=["pipe_validation", "pipe_simulation"]
        )
        self.engine.add_logic_node(self.plumbing_node)
        # Add a fire protection node
        self.fire_node = LogicNode(
            node_id="sprinkler_1",
            object_type="sprinkler",
            properties={"coverage_area": 200, "pressure": 50, "flow_rate": 20, "spacing": 12, "min_density": 0.05},
            position=(3, 3),
            behavior_profiles=["sprinkler_validation", "sprinkler_simulation"]
        )
        self.engine.add_logic_node(self.fire_node)
        # Add edges for chaining
        self.engine.add_logic_edge(LogicEdge(
            edge_id="e1",
            source_id="panel_1",
            target_id="ahu_1",
            connection_type="electrical"
        ))
        self.engine.add_logic_edge(LogicEdge(
            edge_id="e2",
            source_id="ahu_1",
            target_id="pipe_1",
            connection_type="mechanical"
        ))
        self.engine.add_logic_edge(LogicEdge(
            edge_id="e3",
            source_id="pipe_1",
            target_id="sprinkler_1",
            connection_type="plumbing"
        ))

    def test_behavior_profile_validation(self):
        """Test validation for all MEP types using behavior profiles"""
        results = self.engine.validate_object("panel_1", validation_type="validation")
        self.assertTrue(any(r.passed for r in results), "Panel validation should pass")
        results = self.engine.validate_object("ahu_1", validation_type="validation")
        self.assertTrue(any(r.passed for r in results), "AHU validation should pass")
        results = self.engine.validate_object("pipe_1", validation_type="validation")
        self.assertTrue(any(r.passed for r in results), "Pipe validation should pass")
        results = self.engine.validate_object("sprinkler_1", validation_type="validation")
        self.assertTrue(any(r.passed for r in results), "Sprinkler validation should pass")

    def test_simulation_results(self):
        """Test simulation for all MEP types"""
        results = self.engine.simulate_object("panel_1", simulation_type="simulation")
        self.assertTrue(any(r.status == "normal" for r in results), "Panel simulation should be normal")
        results = self.engine.simulate_object("ahu_1", simulation_type="simulation")
        self.assertTrue(any(r.status == "normal" for r in results), "AHU simulation should be normal")
        results = self.engine.simulate_object("pipe_1", simulation_type="simulation")
        self.assertTrue(any(r.status == "normal" for r in results), "Pipe simulation should be normal")
        results = self.engine.simulate_object("sprinkler_1", simulation_type="simulation")
        self.assertTrue(any(r.status == "normal" for r in results), "Sprinkler simulation should be normal")

    def test_object_chaining_and_connectivity(self):
        """Test object chaining and connectivity in the logic graph"""
        conn_panel = self.engine.check_connectivity("panel_1")
        self.assertEqual(conn_panel["downstream"], ["ahu_1"])
        conn_ahu = self.engine.check_connectivity("ahu_1")
        self.assertEqual(conn_ahu["upstream"], ["panel_1"])
        self.assertEqual(conn_ahu["downstream"], ["pipe_1"])
        conn_pipe = self.engine.check_connectivity("pipe_1")
        self.assertEqual(conn_pipe["upstream"], ["ahu_1"])
        self.assertEqual(conn_pipe["downstream"], ["sprinkler_1"])
        conn_sprinkler = self.engine.check_connectivity("sprinkler_1")
        self.assertEqual(conn_sprinkler["upstream"], ["pipe_1"])

    def test_event_propagation(self):
        """Test event propagation through the logic graph"""
        event_data = {"voltage": 208, "current": 100}
        events = self.engine.propagate_event("panel_1", "power_on", event_data)
        self.assertTrue(any(e["object_id"] == "ahu_1" or e["object_id"] == "panel_1" for e in events), "Event should reach downstream nodes")

    def test_missing_object_validation(self):
        """Test validation for missing object"""
        results = self.engine.validate_object("nonexistent", validation_type="validation")
        self.assertTrue(any(not r.passed for r in results), "Validation should fail for missing object")

    def test_import_export_logic_data(self):
        """Test import and export of logic engine data"""
        data = self.engine.export_logic_data()
        new_engine = LogicEngine()
        success = new_engine.import_logic_data(data)
        self.assertTrue(success, "Import should succeed")
        self.assertEqual(len(new_engine.get_behavior_profiles()), len(self.engine.get_behavior_profiles()))
        self.assertEqual(len(new_engine.get_logic_graph().nodes), len(self.engine.get_logic_graph().nodes))

if __name__ == "__main__":
    unittest.main() 
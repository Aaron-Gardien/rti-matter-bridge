import unittest

from rti_switch_config_generator import build_switch_config


class RtiSwitchConfigGeneratorTest(unittest.TestCase):
    def test_builds_switch_config_from_imported_variable_mapping(self):
        apex_mapping = {
            "source_apex": "project.apex",
            "variables": [
                {
                    "id": 951,
                    "name": "Activity Feedback",
                    "sysvar": "DiscoveredVar951",
                }
            ],
        }
        switch_selection = {
            "switches": [
                {
                    "id": "activity-main",
                    "name": "Main Activity",
                    "on_macro": "Main Activity On",
                    "off_macro": "Main Activity Off",
                    "feedback_variable_id": 951,
                    "on_values": ["true"],
                    "off_values": ["false"],
                }
            ]
        }

        config = build_switch_config(apex_mapping, switch_selection)

        switch = config["switches"][0]
        self.assertEqual(switch["id"], "activity-main")
        self.assertEqual(switch["on_macro"], "Main Activity On")
        self.assertEqual(switch["off_macro"], "Main Activity Off")
        self.assertEqual(switch["feedback"]["variable_id"], 951)
        self.assertEqual(switch["feedback"]["sysvar"], "DiscoveredVar951")

    def test_rejects_feedback_variable_not_found_in_mapping(self):
        with self.assertRaisesRegex(ValueError, "not in the Apex mapping"):
            build_switch_config(
                {"variables": []},
                {
                    "switches": [
                        {
                            "id": "activity-main",
                            "on_macro": "Main Activity On",
                            "off_macro": "Main Activity Off",
                            "feedback_variable_id": 951,
                        }
                    ]
                },
            )


if __name__ == "__main__":
    unittest.main()

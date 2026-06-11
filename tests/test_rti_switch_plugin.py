import json
import tempfile
import unittest
from pathlib import Path

from rti_switch_plugin import RtiSwitchPlugin


class RtiSwitchPluginTest(unittest.TestCase):
    def test_maps_commands_and_feedback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "switches.json"
            config_path.write_text(
                json.dumps(
                    {
                        "switches": [
                            {
                                "id": "activity-main",
                                "name": "Main Activity",
                                "on_macro": "Main Activity On",
                                "off_macro": "Main Activity Off",
                                "feedback": {
                                    "variable_id": 951,
                                    "sysvar": "DiscoveredVar951",
                                    "name": "Activity Feedback",
                                    "on_values": ["true"],
                                    "off_values": ["false"],
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            plugin = RtiSwitchPlugin.from_file(config_path)

        self.assertEqual(plugin.tracked_variable_ids(), [951])
        self.assertEqual(plugin.macro_for_command("activity-main", "turn_on"), "Main Activity On")
        self.assertEqual(plugin.macro_for_command("activity-main", "turn_off"), "Main Activity Off")

        update = plugin.handle_feedback(951, "true")

        self.assertEqual(update["device_id"], "activity-main")
        self.assertEqual(update["state"], {"on": True})
        self.assertEqual(update["feedback_sysvar"], "DiscoveredVar951")


if __name__ == "__main__":
    unittest.main()

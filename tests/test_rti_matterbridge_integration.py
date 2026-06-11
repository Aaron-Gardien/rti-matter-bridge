import json
import tempfile
import unittest
from pathlib import Path

from rti_matterbridge_integration import RTIMatterbridgeIntegration


class CapturingIntegration(RTIMatterbridgeIntegration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent_messages = []
        self.executed_macros = []

    async def send_to_matterbridge(self, message_type, data):
        self.sent_messages.append((message_type, data))

    async def execute_rti_macro(self, macro_name):
        self.executed_macros.append(macro_name)


class RTIMatterbridgeIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_mapping_adds_metadata_and_filters_untracked_variables(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mapping_path = Path(tmp_dir) / "mapping.json"
            mapping_path.write_text(
                json.dumps(
                    {
                        "variables": [
                            {
                                "id": 966,
                                "name": "Current Time",
                                "sysvar": "DiscoveredVar966",
                                "device": "Current Time Sensor",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            integration = CapturingIntegration(mapping_path=str(mapping_path))

        await integration.handle_rti_message(
            json.dumps({"messageType": "Sysvar", "sysvarid": 966, "sysvarval": "19:21"})
        )
        await integration.handle_rti_message(
            json.dumps({"messageType": "Sysvar", "sysvarid": 951, "sysvarval": "true"})
        )

        self.assertEqual(len(integration.sent_messages), 1)
        message_type, payload = integration.sent_messages[0]
        self.assertEqual(message_type, "rti_variable_update")
        self.assertEqual(payload["variable_id"], 966)
        self.assertEqual(payload["variable_name"], "Current Time")
        self.assertEqual(payload["sysvar"], "DiscoveredVar966")
        self.assertEqual(payload["device"], "Current Time Sensor")
        self.assertNotIn(951, integration.rti_variables)

    async def test_switch_config_routes_commands_and_feedback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            switch_path = Path(tmp_dir) / "switches.json"
            switch_path.write_text(
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

            integration = CapturingIntegration(switch_config_path=str(switch_path))

        self.assertEqual(integration.switch_plugin.tracked_variable_ids(), [951])

        await integration.handle_matter_device_command({"device_id": "activity-main", "command": "turn_on"})
        await integration.handle_rti_message(
            json.dumps({"messageType": "Sysvar", "sysvarid": 951, "sysvarval": "true"})
        )

        self.assertEqual(integration.executed_macros, ["Main Activity On"])
        self.assertEqual(integration.sent_messages[-1][0], "rti_switch_state_update")
        self.assertEqual(integration.sent_messages[-1][1]["device_id"], "activity-main")
        self.assertEqual(integration.sent_messages[-1][1]["state"], {"on": True})


if __name__ == "__main__":
    unittest.main()

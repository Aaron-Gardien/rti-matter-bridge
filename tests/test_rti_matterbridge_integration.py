import json
import tempfile
import unittest
from pathlib import Path

from rti_matterbridge_integration import RTIMatterbridgeIntegration


class CapturingIntegration(RTIMatterbridgeIntegration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent_messages = []

    async def send_to_matterbridge(self, message_type, data):
        self.sent_messages.append((message_type, data))


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


if __name__ == "__main__":
    unittest.main()

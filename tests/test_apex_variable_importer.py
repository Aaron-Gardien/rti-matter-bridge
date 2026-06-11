import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from apex_variable_importer import build_mapping, build_system_variables_xml, extract_apex_variables


class ApexVariableImporterTest(unittest.TestCase):
    def test_extracts_variables_from_zipped_apex_members(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            apex_path = Path(tmp_dir) / "project.apex"
            with zipfile.ZipFile(apex_path, "w") as archive:
                archive.writestr(
                    "Project.xml",
                    """
                    <project>
                      <device name="Current Time Sensor">
                        <systemVariable id="966" name="Current Time" type="string" />
                      </device>
                    </project>
                    """,
                )
                archive.writestr(
                    "variables.json",
                    json.dumps(
                        {
                            "devices": [
                                {
                                    "name": "Boolean Variable Switch",
                                    "variableId": 951,
                                    "type": "boolean",
                                }
                            ]
                        }
                    ),
                )

            variables = extract_apex_variables(apex_path)

        self.assertEqual([variable.id for variable in variables], [951, 966])
        self.assertEqual(variables[0].sysvar, "DiscoveredVar951")
        self.assertEqual(variables[0].type, "boolean")
        self.assertEqual(variables[1].name, "Current Time")
        self.assertEqual(variables[1].device, "Current Time Sensor")

    def test_builds_mapping_and_driver_xml(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            apex_path = Path(tmp_dir) / "project.apex"
            with zipfile.ZipFile(apex_path, "w") as archive:
                archive.writestr(
                    "Project.xml",
                    '<project><systemVariable id="966" name="Current Time" type="string" /></project>',
                )
            variables = extract_apex_variables(apex_path)

        mapping = build_mapping(apex_path, variables)
        driver_xml = build_system_variables_xml(variables)

        self.assertEqual(mapping["variables"][0]["sysvar"], "DiscoveredVar966")
        self.assertIn('sysvar="DiscoveredVar966"', driver_xml)
        self.assertIn('name="Current Time"', driver_xml)
        self.assertIn('sysvar="VariablesDiscovered"', driver_xml)


if __name__ == "__main__":
    unittest.main()

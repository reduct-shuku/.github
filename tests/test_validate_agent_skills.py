import unittest

from scripts.validate_agent_skills import RegistryValidationError, validate_registry


class ValidateAgentSkillsTests(unittest.TestCase):
    def valid_registry(self):
        return {
            "schema_version": 1,
            "provider": "reduct-shuku",
            "skills": [
                {
                    "name": "alpha",
                    "description": "Useful skill",
                    "version": "1.0.0",
                    "source": {
                        "type": "github",
                        "repository": "https://github.com/reduct-shuku/alpha",
                        "ref": "main",
                        "path": ".",
                    },
                    "entrypoint": "SKILL.md",
                    "manifest": "shuku.json",
                }
            ],
        }

    def test_accepts_valid_registry(self):
        validate_registry(self.valid_registry())

    def test_rejects_duplicate_names(self):
        registry = self.valid_registry()
        registry["skills"].append(dict(registry["skills"][0]))

        with self.assertRaisesRegex(RegistryValidationError, "Duplicate skill name"):
            validate_registry(registry)

    def test_rejects_unsorted_skills(self):
        registry = self.valid_registry()
        second = dict(registry["skills"][0])
        second["name"] = "aardvark"
        registry["skills"].append(second)

        with self.assertRaisesRegex(RegistryValidationError, "sorted"):
            validate_registry(registry)

    def test_rejects_invalid_fixed_fields(self):
        registry = self.valid_registry()
        registry["skills"][0]["entrypoint"] = "README.md"

        with self.assertRaisesRegex(RegistryValidationError, "entrypoint"):
            validate_registry(registry)


if __name__ == "__main__":
    unittest.main()

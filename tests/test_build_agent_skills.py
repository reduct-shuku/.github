import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_agent_skills import (
    BuildError,
    build_registry,
    render_registry,
    write_or_check_registry,
)


class BuildAgentSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.sources_path = self.root / "sources.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_sources(self, sources):
        self.sources_path.write_text(
            json.dumps({"schema_version": 1, "sources": sources}),
            encoding="utf-8",
        )

    def write_skill(
        self,
        repository,
        path,
        name,
        description="Useful skill",
        manifest_name=None,
        version="1.0.0",
    ):
        skill_dir = self.root / repository / path
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": 1,
            "name": manifest_name or name,
            "version": version,
            "repository": f"https://github.com/reduct-shuku/{repository}",
            "ref": "main",
            "path": "." if str(path) == "." else Path(path).as_posix(),
        }
        (skill_dir / "shuku.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def test_builds_both_layouts_and_sorts_by_name(self):
        self.write_sources(
            [
                {
                    "repository": "reduct-shuku/multi",
                    "mode": "skills-directory",
                    "path": "skills",
                },
                {
                    "repository": "reduct-shuku/single",
                    "mode": "repository-skill",
                    "path": ".",
                },
            ]
        )
        self.write_skill("multi", "skills/zeta", "zeta", "中文描述", version="2.0.0")
        self.write_skill("single", ".", "alpha", version="1.2.3")

        registry = build_registry(self.sources_path, source_root=self.root)

        self.assertEqual(registry["schema_version"], 1)
        self.assertEqual(registry["provider"], "reduct-shuku")
        self.assertEqual([skill["name"] for skill in registry["skills"]], ["alpha", "zeta"])
        self.assertEqual(registry["skills"][0]["source"]["path"], ".")
        self.assertEqual(registry["skills"][1]["description"], "中文描述")
        self.assertIn("中文描述", render_registry(registry))

    def test_rejects_cross_file_name_mismatch(self):
        self.write_sources(
            [{"repository": "reduct-shuku/single", "mode": "repository-skill", "path": "."}]
        )
        self.write_skill("single", ".", "frontmatter-name", manifest_name="manifest-name")

        with self.assertRaisesRegex(BuildError, "does not match"):
            build_registry(self.sources_path, source_root=self.root)

    def test_rejects_duplicate_skill_names(self):
        self.write_sources(
            [{"repository": "reduct-shuku/multi", "mode": "skills-directory", "path": "skills"}]
        )
        self.write_skill("multi", "skills/one", "duplicate")
        self.write_skill("multi", "skills/two", "duplicate")

        with self.assertRaisesRegex(BuildError, "Duplicate skill name"):
            build_registry(self.sources_path, source_root=self.root)

    def test_rejects_partial_skill_directory(self):
        self.write_sources(
            [{"repository": "reduct-shuku/multi", "mode": "skills-directory", "path": "skills"}]
        )
        partial = self.root / "multi" / "skills" / "partial"
        partial.mkdir(parents=True)
        (partial / "SKILL.md").write_text(
            "---\nname: partial\ndescription: Partial\n---\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(BuildError, "must contain both"):
            build_registry(self.sources_path, source_root=self.root)

    def test_rejects_unsafe_manifest_ref(self):
        self.write_sources(
            [{"repository": "reduct-shuku/single", "mode": "repository-skill", "path": "."}]
        )
        self.write_skill("single", ".", "alpha")
        manifest_path = self.root / "single" / "shuku.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["ref"] = "--upload-pack=malicious"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(BuildError, "safe Git ref"):
            build_registry(self.sources_path, source_root=self.root)

    def test_check_mode_detects_stale_output_without_modifying_it(self):
        self.write_sources(
            [{"repository": "reduct-shuku/single", "mode": "repository-skill", "path": "."}]
        )
        self.write_skill("single", ".", "alpha")
        registry = build_registry(self.sources_path, source_root=self.root)
        output = self.root / "agent-skills.json"
        output.write_text("stale\n", encoding="utf-8")

        with self.assertRaisesRegex(BuildError, "out of date"):
            write_or_check_registry(registry, output, check=True)
        self.assertEqual(output.read_text(encoding="utf-8"), "stale\n")

        write_or_check_registry(registry, output, check=False)
        write_or_check_registry(registry, output, check=True)


if __name__ == "__main__":
    unittest.main()

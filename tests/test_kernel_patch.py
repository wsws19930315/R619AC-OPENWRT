import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from test_build_checks import BASH, REPO


PATCH = REPO / "patches/openwrt/110-kernel-6.12.113.patch"
KERNEL_HASH = "e09b6727e5c521253f0d41694900b9c38fb7604db7d35238a8197aa9f7de2428"


class KernelPatchScopeTest(unittest.TestCase):
    def setUp(self):
        text = PATCH.read_text(encoding="utf-8")
        self.body = text[text.index("diff --git "):].rstrip() + "\n"

    def test_matches_official_generic_and_ipq40xx_changes(self):
        self.assertEqual(hashlib.sha256(self.body.encode("utf-8")).hexdigest(),
                         "adffd67d4ad33be58fc9b435c4a60fc1ae7c2299e75b762926751337d8981145")

    def test_only_required_kernel_paths_are_changed(self):
        paths = re.findall(r"^diff --git a/(\S+) b/\S+$", self.body, re.M)
        self.assertEqual(len(paths), 24)
        self.assertTrue(all(path.startswith(("target/linux/generic/", "target/linux/ipq40xx/"))
                            for path in paths))
        self.assertIn("target/linux/generic/kernel-6.12", paths)
        self.assertIn("target/linux/ipq40xx/patches-6.12/701-net-dsa-add-out-of-band-tagging-protocol.patch",
                      paths)


@unittest.skipUnless(BASH, "需要 Bash")
class KernelMetadataPatchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r619ac-kernel-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.metadata = self.root / "target/linux/generic/kernel-6.12"
        self.metadata.parent.mkdir(parents=True)
        self.original = (
            "LINUX_VERSION-6.12 = .112\n"
            "LINUX_KERNEL_HASH-6.12.112 = 164dc9d1f6c93c61a15e1f071c48379b467f2b17c469cce7223471968208ed03\n"
        )
        self.metadata.write_text(self.original, encoding="utf-8", newline="\n")
        sections = re.split(r"(?=^diff --git )", PATCH.read_text(encoding="utf-8"), flags=re.M)
        self.section = next(section for section in sections
                            if section.startswith("diff --git a/target/linux/generic/kernel-6.12 "))

    def apply_patch(self):
        return subprocess.run(
            [BASH, "-c", "patch --batch --forward --fuzz=0 -p1"],
            input=self.section, cwd=self.root, capture_output=True,
            encoding="utf-8", errors="replace", timeout=15,
        )

    def test_updates_version_and_source_hash(self):
        result = self.apply_patch()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.metadata.read_text(encoding="utf-8"),
                         f"LINUX_VERSION-6.12 = .113\nLINUX_KERNEL_HASH-6.12.113 = {KERNEL_HASH}\n")

    def test_changed_baseline_is_rejected(self):
        changed = self.original.replace("164dc9d1", "00000000")
        self.metadata.write_text(changed, encoding="utf-8", newline="\n")
        self.assertNotEqual(self.apply_patch().returncode, 0)
        self.assertEqual(self.metadata.read_text(encoding="utf-8"), changed)

    def test_reapplying_patch_is_rejected(self):
        self.assertEqual(self.apply_patch().returncode, 0)
        self.assertNotEqual(self.apply_patch().returncode, 0)


if __name__ == "__main__":
    unittest.main()

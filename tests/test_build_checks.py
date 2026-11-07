import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
BASH = os.environ.get("OPENWRT_TEST_BASH") or shutil.which("bash")


@unittest.skipUnless(BASH, "需要 Bash")
class BuildChecksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r619ac-checks-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = (REPO / ".config").read_text(encoding="utf-8")
        self.config += "\nCONFIG_USE_APK=y\n"
        self.write(".config", self.config)
        self.write("target/linux/ipq40xx/Makefile", "KERNEL_PATCHVER:=6.12\n")
        self.write("target/linux/generic/kernel-6.12",
                   "LINUX_VERSION-6.12 = .113\n"
                   "LINUX_KERNEL_HASH-6.12.113 = e09b6727e5c521253f0d41694900b9c38fb7604db7d35238a8197aa9f7de2428\n")
        self.write("feeds/packages/lang/golang/golang-values.mk", "GO_DEFAULT_VERSION:=1.27\n")
        self.write("feeds/packages/lang/golang/golang1.27/Makefile", "GO_VERSION_PATCH:=3\n")
        self.write("package/feeds/passwall_packages/xray-core/Makefile", "PKG_VERSION:=26.10.21\n")
        self.write("feeds/passwall_luci/luci-app-passwall/po/zh_Hans/passwall.po", 'msgid "test"\n')
        self.write("feeds/packages/net/samba4/Makefile",
                   "PKG_VERSION:=4.22.11\n"
                   "PKG_HASH:=d569b298a81cc212a39e9d1813bc4ca5c71ac93c4ceb2eec03db178096958d00\n")
        self.write("feeds/packages/net/transmission/files/transmission.init",
                   'r619ac_require_storage "$config_dir" "$download_dir" || return 1\n')
        self.write("feeds/packages/net/transmission/Makefile", "PKG_RELEASE:=2\n")
        self.write("package/network/config/wifi-scripts/files/lib/wifi/mac80211.uc",
                   "set ${si}.disabled='0'\n")
        shutil.copytree(REPO / "files", self.root / "files")

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")

    def run_check(self, mode="config"):
        return subprocess.run(
            [BASH, (REPO / "scripts/check-build.sh").as_posix(), mode],
            cwd=self.root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )

    def manifest(self, omit=None, versions=None):
        packages = dict.fromkeys(re.findall(r"^CONFIG_PACKAGE_(.+)=y$", self.config, re.M), "1.0-r1")
        packages.update({
            "apk-mbedtls": "3.0.3-r1",
            "kernel": "6.12.113~0123456789abcdef-r1",
            "uhttpd": "2026.08.24~373145f7-r1",
            "odhcpd-ipv6only": "2026.06.29~5d7be43f-r1",
            "libopenssl3": "3.5.9-r1",
            "libmbedtls21": "3.6.7-r1",
            "xray-core": "26.10.21-r1",
            "luci-app-passwall": "26.10.22-r2",
            "samba4-server": "4.22.11-r1",
            "samba4-libs": "4.22.11-r1",
            "samba4-utils": "4.22.11-r1",
            "transmission-daemon": "4.1.3-r2",
        })
        packages.update(versions or {})
        if omit:
            packages.pop(omit)
        self.write("bin/targets/ipq40xx/generic/test.manifest", "".join(
            f"{name} - {version}\n" for name, version in packages.items()
        ))
        self.write("bin/targets/ipq40xx/generic/openwrt-p2w_r619ac-128m-squashfs-sysupgrade.bin", "fixture")

    def test_expected_config_passes(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_lucky_is_rejected(self):
        self.write(".config", self.config.replace("CONFIG_PACKAGE_luci-app-lucky=y", ""))
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_old_kernel_source_is_rejected(self):
        self.write("target/linux/generic/kernel-6.12", "LINUX_VERSION-6.12 = .112\n")
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("6.12.113", result.stderr)

    def test_unapproved_kernel_source_is_rejected(self):
        self.write("target/linux/generic/kernel-6.12", "LINUX_VERSION-6.12 = .114\n")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_wrong_kernel_branch_is_rejected(self):
        self.write("target/linux/ipq40xx/Makefile", "KERNEL_PATCHVER:=6.18\n")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_wrong_kernel_hash_is_rejected(self):
        self.write("target/linux/generic/kernel-6.12",
                   "LINUX_VERSION-6.12 = .113\nLINUX_KERNEL_HASH-6.12.113 = wrong\n")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_missing_chinese_source_is_rejected(self):
        (self.root / "feeds/passwall_luci/luci-app-passwall/po/zh_Hans/passwall.po").unlink()
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_opkg_config_is_rejected(self):
        self.write(".config", self.config.replace("CONFIG_USE_APK=y", "# CONFIG_USE_APK is not set"))
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_old_go_is_rejected(self):
        self.write("feeds/packages/lang/golang/golang1.27/Makefile", "GO_VERSION_PATCH:=1\n")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_invalid_passwall_repository_is_rejected(self):
        self.write(".config", self.config.replace(
            "# CONFIG_FEED_passwall_packages is not set", "CONFIG_FEED_passwall_packages=y"))
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_missing_https_generator_is_rejected(self):
        self.write(".config", self.config.replace("CONFIG_PACKAGE_px5g-mbedtls=y", ""))
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_old_samba_source_is_rejected(self):
        self.write("feeds/packages/net/samba4/Makefile", "PKG_VERSION:=4.22.7\n")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_missing_storage_guard_is_rejected(self):
        (self.root / "files/usr/libexec/r619ac-storage-guard.sh").unlink()
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_disabled_default_wifi_is_rejected(self):
        self.write("package/network/config/wifi-scripts/files/lib/wifi/mac80211.uc",
                   "set ${si}.disabled='${defaults ? 0 : 1}'\n")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_manifest_missing_translation_is_rejected(self):
        self.manifest(omit="luci-i18n-passwall-zh-cn")
        self.assertNotEqual(self.run_check("firmware").returncode, 0)

    def test_manifest_missing_kernel_is_rejected(self):
        self.manifest(omit="kernel")
        self.assertNotEqual(self.run_check("firmware").returncode, 0)

    def test_manifest_wrong_kernel_is_rejected(self):
        for version in ("6.12.112~0123456789abcdef-r1", "6.12.114~0123456789abcdef-r1",
                        "6.18.60~0123456789abcdef-r1"):
            with self.subTest(version=version):
                self.manifest(versions={"kernel": version})
                result = self.run_check("firmware")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("6.12.113", result.stderr)

    @unittest.skipUnless(shutil.which("dpkg"), "安全版本比较在 Linux CI 中运行")
    def test_expected_manifest_passes(self):
        self.manifest()
        result = self.run_check("firmware")
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("dpkg"), "安全版本比较在 Linux CI 中运行")
    def test_old_webserver_is_rejected(self):
        self.manifest(versions={"uhttpd": "2025.07.06~7e64e8ba-r4"})
        self.assertNotEqual(self.run_check("firmware").returncode, 0)

    @unittest.skipUnless(shutil.which("dpkg"), "安全版本比较在 Linux CI 中运行")
    def test_old_samba_manifest_is_rejected(self):
        self.manifest(versions={"samba4-server": "4.22.7-r3"})
        self.assertNotEqual(self.run_check("firmware").returncode, 0)


if __name__ == "__main__":
    unittest.main()

#!/bin/bash
set -euo pipefail
#=============================================================
# diy-part1.sh — feeds 更新前执行
# 用途：添加第三方插件源
#=============================================================

# 仅移植官方 6.12.113 的通用内核和 ipq40xx 补丁，不切换主源码或 feeds 基线。
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
patch --batch --forward --fuzz=0 -p1 < "$repo_dir/patches/openwrt/110-kernel-6.12.113.patch"

# 固定 25.12 安全维护分支快照，包含 Go 1.27.3；其他官方 feeds 沿用发行标签的固定版本。
sed -i 's|^src-git packages .*|src-git packages https://github.com/openwrt/packages.git^d20a92f5a55b51fd239fc29917ca49bb101ac223|' feeds.conf.default

# Passwall 必须优先于同名官方包，LuCI 与核心分别固定到已核对的源码。
sed -i '/^src-git passwall_\(luci\|packages\) /d' feeds.conf.default
sed -i '1i src-git passwall_luci https://github.com/Openwrt-Passwall/openwrt-passwall.git^5e2bbfa8e6a32f7e54a7fe29891a28fb05439e52' feeds.conf.default
sed -i '1i src-git passwall_packages https://github.com/Openwrt-Passwall/openwrt-passwall-packages.git^d3230c7645d8f046039c84161c9384ae81a294f2' feeds.conf.default
echo ""
echo ">>> diy-part1.sh: 第三方 feeds 已添加"
echo "==========================================="
cat feeds.conf.default
echo "==========================================="

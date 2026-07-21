#!/bin/bash
#=============================================================
# diy-part1.sh — feeds 更新前执行
# 用途：添加第三方插件源
#=============================================================

# ===== 科学上网：Passwall feed 必须优先于 OpenWrt 官方 packages =====
# Passwall LuCI 会生成仅配套新版核心的配置，同名包不能落到官方旧版。
sed -i '1i src-git passwall_luci https://github.com/Openwrt-Passwall/openwrt-passwall.git;main' feeds.conf.default
sed -i '1i src-git passwall_packages https://github.com/Openwrt-Passwall/openwrt-passwall-packages.git;main' feeds.conf.default






echo ""
echo ">>> diy-part1.sh: 第三方 feeds 已添加"
echo "==========================================="
cat feeds.conf.default
echo "==========================================="

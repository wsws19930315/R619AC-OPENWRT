#!/bin/bash
set -euo pipefail

required_packages=(
  luci luci-base luci-ssl px5g-mbedtls luci-app-package-manager luci-i18n-base-zh-cn
  luci-i18n-package-manager-zh-cn luci-theme-bootstrap
  luci-app-passwall luci-i18n-passwall-zh-cn
  xray-core v2ray-geoip v2ray-geosite chinadns-ng dnsmasq-full firewall4
  nftables-json kmod-nft-tproxy kmod-nft-socket luci-app-smartdns smartdns
  luci-i18n-smartdns-zh-cn lucky luci-app-lucky luci-i18n-lucky-zh-cn
  block-mount kmod-usb-storage kmod-usb-storage-uas kmod-usb3
  kmod-fs-ext4 kmod-fs-ntfs3 kmod-fs-exfat kmod-fs-vfat kmod-nls-utf8
  luci-app-hd-idle smartmontools wsdd2 samba4-server luci-app-samba4
  transmission-daemon transmission-web luci-app-transmission
  minidlna luci-app-minidlna mwan3 luci-app-mwan3 sqm-scripts luci-app-sqm
  luci-app-ddns luci-app-upnp odhcp6c odhcpd-ipv6only wpad-openssl
)

fail() {
  echo "校验失败：$*" >&2
  exit 1
}

check_kernel_version() {
  local version=${1%%~*}
  version=${version%%-*}
  test "$version" = 6.12.113 || fail '内核必须为本次核对的 6.12.113'
}

check_config() {
  local kernel_suffix
  grep -qx 'KERNEL_PATCHVER:=6.12' target/linux/ipq40xx/Makefile || fail '目标平台内核分支不正确'
  kernel_suffix=$(awk '$1 == "LINUX_VERSION-6.12" && $2 == "=" { print $3; exit }' target/linux/generic/kernel-6.12)
  check_kernel_version "6.12$kernel_suffix"
  grep -qx 'LINUX_KERNEL_HASH-6.12.113 = e09b6727e5c521253f0d41694900b9c38fb7604db7d35238a8197aa9f7de2428' target/linux/generic/kernel-6.12 || fail '内核源码校验值不正确'
  grep -qx 'CONFIG_TARGET_ipq40xx_generic_DEVICE_p2w_r619ac-128m=y' .config || fail '目标机型不正确'
  grep -qx 'CONFIG_USE_APK=y' .config || fail '必须使用原生 APK 包管理器'
  grep -qx 'CONFIG_LUCI_LANG_zh_Hans=y' .config || fail '未启用简体中文'
  for feed in passwall_luci passwall_packages; do
    grep -qx "# CONFIG_FEED_${feed} is not set" .config || fail "仍会生成不存在的官方 APK 源：$feed"
  done
  grep -qx 'CONFIG_PACKAGE_luci-app-passwall_Nftables_Transparent_Proxy=y' .config || fail '未启用 Passwall nftables 支持'
  for package in "${required_packages[@]}"; do
    grep -qx "CONFIG_PACKAGE_${package}=y" .config || fail "必需组件未进入镜像：$package"
  done
  if grep -Eq '^CONFIG_PACKAGE_(adguardhome|luci-app-adguardhome|sing-box|geoview|v2ray-plugin)=y$' .config; then
    fail '出现已排除的组件'
  fi
  test -s feeds/passwall_luci/luci-app-passwall/po/zh_Hans/passwall.po || fail '缺少 Passwall 中文翻译源码'
  grep -qx 'GO_DEFAULT_VERSION:=1.27' feeds/packages/lang/golang/golang-values.mk || fail 'Go 默认工具链不正确'
  grep -qx 'GO_VERSION_PATCH:=3' feeds/packages/lang/golang/golang1.27/Makefile || fail 'Go 安全更新版本不正确'
  grep -qx 'PKG_VERSION:=26.10.21' package/feeds/passwall_packages/xray-core/Makefile || fail 'Xray 版本不正确'
  test ! -e package/feeds/packages/xray-core || fail '仍有同名官方 Xray 包'
  grep -qx 'PKG_VERSION:=4.22.11' feeds/packages/net/samba4/Makefile || fail '未应用 Samba 安全更新'
  grep -qx 'PKG_HASH:=d569b298a81cc212a39e9d1813bc4ca5c71ac93c4ceb2eec03db178096958d00' feeds/packages/net/samba4/Makefile || fail 'Samba 源码校验值不正确'
  grep -q 'r619ac_require_storage "\$config_dir" "\$download_dir"' feeds/packages/net/transmission/files/transmission.init || fail 'Transmission 缺少挂载保护'
  grep -qx 'PKG_RELEASE:=2' feeds/packages/net/transmission/Makefile || fail 'Transmission 未标记挂载保护修订版本'
  test -s files/usr/libexec/r619ac-storage-guard.sh || fail '缺少挂载保护运行脚本'
  test -s files/etc/uci-defaults/90-r619ac-runtime-fixes || fail '缺少首次启动修复脚本'
  grep -Fqx "set \${si}.disabled='0'" package/network/config/wifi-scripts/files/lib/wifi/mac80211.uc || fail '新生成的 WiFi 热点仍默认关闭'
}

check_version() {
  local package="$1" minimum="$2" version
  version=$(awk -v name="$package" '$1 == name && $2 == "-" { print $3; exit }' "$manifest")
  test -n "$version" || fail "产物缺少组件：$package"
  version=${version%%~*}
  dpkg --compare-versions "$version" ge "$minimum" || fail "$package 低于安全版本 $minimum"
}

case "${1:-config}" in
  config)
    check_config
    echo '配置校验通过：APK、配套核心、中文及必需功能均已选中'
    ;;
  firmware)
    shopt -s nullglob
    images=(bin/targets/ipq40xx/generic/*p2w_r619ac-128m-squashfs-sysupgrade.bin)
    manifests=(bin/targets/ipq40xx/generic/*.manifest)
    ((${#images[@]} == 1)) || fail '没有生成唯一的本机型 sysupgrade 镜像'
    ((${#manifests[@]} > 0)) || fail '没有生成软件包清单'
    for manifest in "${manifests[@]}"; do
      check_kernel_version "$(awk '$1 == "kernel" && $2 == "-" { print $3; exit }' "$manifest")"
      for package in apk-mbedtls "${required_packages[@]}"; do
        awk -v name="$package" '$1 == name && $2 == "-" { found=1 } END { exit !found }' "$manifest" || fail "产物缺少组件：$package"
      done
      check_version uhttpd 2026.08.24
      check_version odhcpd-ipv6only 2026.06.29
      check_version libopenssl3 3.5.9
      check_version xray-core 26.10.21
      check_version luci-app-passwall 26.10.22-r2
      check_version samba4-server 4.22.11
      check_version samba4-libs 4.22.11
      check_version samba4-utils 4.22.11
      check_version transmission-daemon 4.1.3-r2
      if grep -q '^libmbedtls21 - ' "$manifest"; then
        check_version libmbedtls21 3.6.7
      fi
    done
    echo '固件清单校验通过：升级镜像、必需组件和关键安全版本齐全'
    ;;
  *) fail '参数应为 config 或 firmware' ;;
esac

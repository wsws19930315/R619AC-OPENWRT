# R619AC OpenWRT 25.12 自动编译

> 竞斗云2.0 (P&W R619AC 128M) 的 OpenWRT 固件自动化编译仓库

当前为 **25.12.6 / 6.12.113 内核回移测试版**，以本仓库最后成功的 `012d8f7` 为基线，
只引入官方内核更新及必要补丁，不更新 feeds、插件或其他用户态组件。
旧版 25.12.6 / 6.12.112 已完成官方打底后的基础实机验证；本次内核回移仍需独立验收。
GitHub 编译、组件及版本校验通过后发布为 Pre-release，不代表实机验收通过。当前路由器不会自动升级。

> **OpBoot 首次安装必读：必须先刷同版本 OpenWrt 官方原始精简固件的 `factory.ubi` 打底，
> 确认能正常进入官方系统后，再从 LuCI 保留配置升级本仓库的 `sysupgrade.bin`。**
> 不要直接在 OpBoot 首刷本仓库的自编译固件。具体文件、下载链接和操作步骤见下方“刷机”。

## 固件信息

| 项目 | 详情 |
|------|------|
| **设备** | P&W R619AC 128M (竞斗云2.0) |
| **源码** | [OpenWRT 官方](https://git.openwrt.org/openwrt/openwrt.git) `v25.12.6` 标签 |
| **内核** | Linux `6.12.113`，仅回移官方内核补丁；本次尚未完成实机验收 |
| **架构** | Qualcomm IPQ4019 (`ipq40xx/generic` / `arm_cortex-a7_neon-vfpv4`) |
| **包管理器** | APK；不能安装原来的 24.10 IPK 包 |
| **默认 WiFi** | 新生成的双频热点默认开启，SSID `OpenWrt`，无密码，仅供首次配置；保留配置升级沿用原设置 |
| **Passwall / Xray** | `26.10.22-r2` / `26.10.21`，中文与主程序同源码编译 |
| **Go** | 官方 packages feed 的 `1.27.3`，用于编译新版 Xray |

### 新版本变化与兼容性

- 主线已迁移到 OpenWrt `25.12.6`，内核更新为 Linux `6.12` 系列，不是仅替换插件。
- 包管理器由旧版的 opkg/IPK 改为 APK；不能复用 24.10 的软件源、IPK 或内核模块。
- 默认使用 Bootstrap 主题，Passwall 与 Xray 版本见上表。
- 本机曾出现直接刷入后 LAN 或后台无法访问的情况；先刷官方原版打底、再升级本仓库固件的流程已成功。
  直接刷入失败的底层原因尚未确定，不能仅凭现象认定为内核或 USB 驱动问题。
- 跨版本恢复配置应分项处理，不要将 24.10 的整份备份直接覆盖到 25.12。

### 本次维护修复

- 主源码和构建方式恢复为 `012d8f7` 使用的官方 `v25.12.6` 标签；仅移植
  [官方 6.12.113 更新](https://github.com/openwrt/openwrt/commit/8303e9b2a004a6c3754aaa1edb32cfc7c0cfe55b)
  中 R619AC 所需的 24 个 `target/linux/generic`、`target/linux/ipq40xx` 文件改动。
  不整批切换维护分支，不附带升级 uhttpd；feeds 和全部原有功能保持上一成功版本的设置。
- 内核源码版本、下载哈希及固件 manifest 必须匹配 `6.12.113`。该内核使用新的模块 ABI，
  不能混装官方 25.12.6 的 `6.12.112` 驱动；新增驱动须同配置编译，不要强制忽略依赖或整机执行 `apk upgrade`。
- 此次回退不表示此前 GitHub 运行器失联的原因已经确定，也不能保证失联不会再次发生。
- Samba 沿用 4.22 分支升级到 `4.22.11`，包含修复只读共享访问检查问题的安全更新；
  [CVE-2026-1933 官方说明](https://www.samba.org/samba/security/CVE-2026-1933.html)。
  源码包使用固定 SHA256，不迁移整个 packages feed，也不引入 4.24 的跨分支变化。
- 不再生成官方服务器不存在的 `passwall_luci` / `passwall_packages` APK 源；首次启动仅清理这两个误生成的官方地址，
  保留其他官方源和用户自建源。Passwall 及配套核心仍内置在固件中，不代表删除这些组件。
- 补齐 `luci-ssl` / `px5g-mbedtls`，由 uhttpd 在缺少证书时生成本机自签证书；已有 uhttpd 证书不覆盖。
  自签证书仍会有浏览器信任警告，不能替代域名公有证书；Lucky 的证书和 HTTPS 入口保持独立，不作修改。
- Transmission 修订为 `4.1.3-r2`；启动时先检查 UCI 中位于 `/mnt/<硬盘>/` 或 `/media/<硬盘>/` 的配置、下载、已启用的未完成及监视目录。
  硬盘未挂载、只读挂载或路径经符号链接逃逸时拒绝启动，不先创建空目录或写入内部闪存；允许挂载成功后创建下载子目录。
  沿用原服务的挂载变化触发机制，不自动启用下载，也不改变历史任务状态。这不能修复硬盘 SMART 故障。
- 仅当 HAProxy 配置与 ROM 默认示例完全一致时，停止并禁用其独立服务；自定义配置及 Passwall 自行管理的负载均衡保持不变。
- 新生成的无线接口默认开启，不改写已有无线开关、SSID、加密方式或密码。
- 不修改 SSH root 密码登录策略、已有无线和用户业务配置、Lucky 证书或远程管理入口。

### 源码固定与构建检查

- 官方主源码固定发行标签，官方 packages 固定 25.12 安全维护分支的提交。
- Passwall、配套核心和 Lucky 均固定提交，详见 `diy-part1.sh` 和 `diy-part2.sh`。
- SmartDNS 和其管理界面使用官方 feed，去掉旧 LEDE 分支及开机安装中文 IPK 的方式。
- `make defconfig` 后检查必需组件，防止未知配置被静默移除。
- 发布前检查固件 manifest 中的 `6.12.113` 内核、功能包、uhttpd、odhcpd、OpenSSL、Mbed TLS 和 Xray 版本。
- 固件附件保留 `build-sources.txt`、`build.config` 和软件包 manifest，便于追溯。

## 预装功能

### 核心功能
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ LuCI 中文界面 | `luci-i18n-*-zh-cn` | 使用默认 Bootstrap 主题 |
| ✅ Passwall | `luci-app-passwall` | 科学上网（Xray 核心 + ChinaDNS-NG） |
| ✅ SmartDNS | `luci-app-smartdns` | DNS 加速分流 |
| ✅ Lucky | `luci-app-lucky` | DDNS、端口转发与反向代理 |

### 网络管理
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ MWAN3 | `luci-app-mwan3` | 多线负载均衡/故障切换 |
| ✅ SQM QoS | `luci-app-sqm` | 智能流量控制 |
| ✅ DDNS | `luci-app-ddns` | 动态域名（Cloudflare/DNSPod） |
| ✅ UPnP | `luci-app-upnp` | 端口自动映射 |
| ✅ IPv6 | `odhcp6c` / `odhcpd-ipv6only` | IPv6 地址获取、DHCPv6 与 RA |
| ✅ PPPoE | `ppp-mod-pppoe` | 备用拨号支持 |

### 存储与下载
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ Samba4 | `luci-app-samba4` | USB 硬盘网络共享 (SMB) |
| ✅ wsdd2 | `wsdd2` | Windows 网络发现 |
| ✅ Transmission | `luci-app-transmission` | BT 下载 |
| ✅ MiniDLNA | `luci-app-minidlna` | 局域网媒体服务器 |
| ✅ smartmontools | `smartmontools` | 硬盘健康状态检查 |

### 系统工具
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ 定时重启 | `luci-app-watchcat` | 定时/断网自动重启 |
| ✅ irqbalance | `irqbalance` | 多核中断均衡 |
| ✅ 系统监控 | `luci-app-statistics` | CPU/内存/流量统计 |

## 使用方法

### 编译固件

1. **Fork 本仓库**
2. 进入 **Actions** → **Build OpenWrt for R619AC**
3. 点击 **Run workflow** → 开始编译
4. 等待 ~2-3 小时
5. 从 **Releases** 下载固件

### 自定义配置

如需修改编译配置（增删插件），可以：

1. 触发 workflow 时开启 **SSH 远程调试**
2. 通过 SSH 连接后运行 `cd openwrt && make menuconfig`
3. 保存配置后输入 `exit` 继续编译

### 刷机

#### OpBoot 首次安装或救援恢复：必须先刷官方原始精简版

这里的“原始精简版”指 **OpenWrt 官方发布、未加入本仓库附加插件的原版固件**，
不是本仓库的 OpenWRT-Lite，也不是第三方修改版。以下流程仅适用于 **R619AC 128M NAND**，不要混用 64M 型号镜像。

**当前 25.12.6 的官方打底文件：**

```text
openwrt-25.12.6-ipq40xx-generic-p2w_r619ac-128m-squashfs-factory.ubi
```

- [官方下载该 factory.ubi](https://downloads.openwrt.org/releases/25.12.6/targets/ipq40xx/generic/openwrt-25.12.6-ipq40xx-generic-p2w_r619ac-128m-squashfs-factory.ubi)
- [官方镜像目录](https://downloads.openwrt.org/releases/25.12.6/targets/ipq40xx/generic/) / [SHA256 校验清单](https://downloads.openwrt.org/releases/25.12.6/targets/ipq40xx/generic/sha256sums)
- 上述官方打底文件的 SHA256：

```text
c340a935996e43a7ba7c32dd8c23638103a05f4648e267451940f6f69053a210
```

1. 刷机前导出现有系统备份，单独保存 `/etc/lucky/`、Passwall 自定义规则以及挂载、共享配置；在电脑保存已知可用的恢复固件。
2. 电脑用网线连接路由器，断电后按住 Reset 再通电，按本机 OpBoot 的方式进入恢复模式。
3. 电脑临时设置静态 IP `192.168.1.2/24`，访问 OpBoot 页面；本机地址为 `http://192.168.1.1`，以实际引导器设置为准。
4. 在 OpBoot 中刷入上面的 **官方原版 `factory.ubi`**，等待写入完成并重启，不要断电。
5. 进入官方 OpenWrt，确认 LAN 链路、电脑取址和 LuCI 后台正常；官方默认 LAN 地址通常为 `192.168.1.1`，电脑可改回自动获取地址。
6. 登录官方 LuCI → 系统 → 备份/升级，上传本仓库同机型的 `*-p2w_r619ac-128m-squashfs-sysupgrade.bin`，确认镜像兼容性检查通过，**不要强制刷入**。
7. 勾选“保留配置”，再开始升级。本步骤保留的是刚验证可用的官方基础配置，不是直接导入旧版整份备份。
8. 升级重启后按实际 LAN 地址登录；保留配置可能继续使用官方的 `192.168.1.1`，不一定变为本仓库默认的 `192.168.2.1`。
9. 先确认网口和后台正常，再分项恢复业务配置并验收；确认可正常使用后再接回其他外设、按需启用下载等服务。

**文件用途不要混淆：**官方 `factory.ubi` 用于上述 OpBoot 打底，本仓库 `sysupgrade.bin` 用于官方系统后台升级；
`initramfs-zImage.itb` 不属于本说明的常规安装流程。以后仓库升级基础版本时，应重新核对同版本官方打底文件及校验值。

#### 从 24.10 跨版本迁移到 25.12

本仓库维护机曾在直接升级后出现无法访问，因此这里不再将“24.10 后台直接刷 25.12 自编译固件”作为推荐路径。
请先做好旧系统备份，再按上面的 **官方 25.12.6 打底 → LuCI 保留基础配置刷本仓库固件** 的流程操作。

- 无线、Passwall、挂载、共享、下载、DLNA 和 Lucky 等业务配置分项恢复并逐项验证。
- 保留新版网络、账户、SSH 和防火墙基础配置；不要直接覆盖旧版整份备份、旧启动脚本或 `/etc/opkg/`。
- 旧 IPK 和旧内核模块不能用于新系统；额外安装的软件、自定义文件也不保证自动保留。
- 如果网口、无线或存储异常，先保存日志并使用已知可用固件回退，不反复强刷。

#### 已正常运行本仓库 25.12 后的日常升级

同分支后续小版本通常可以在 LuCI 中使用本机型 `sysupgrade.bin` 升级，无需每次重新进入 OpBoot。
仍须先备份、核对该次发布说明并通过镜像兼容性检查；涉及基础版本、内核或分区布局变化时，以对应迁移说明为准。
升级后检查 LAN/WAN、双频 WiFi、Passwall、Lucky、硬盘挂载、Samba、DLNA，以及按需启用的 Transmission。

### 首次配置

1. 网线连接 LAN 口，或在全新无线配置时连接 `OpenWrt` 热点 → 按实际 LAN 地址访问后台；全新默认配置为 `http://192.168.2.1`，保留官方基础配置时可能仍为 `http://192.168.1.1`
2. 默认用户 `root`，无密码
3. 立即设置管理密码和 WiFi 加密密码，再配置 WAN
4. 配置 Passwall（导入订阅）
5. 按需启用其他服务（Samba / SmartDNS / Transmission 等）

**开放热点仅供首次配置：**只有新生成的无线配置默认开启双频 `OpenWrt` 无密码热点，
首次上电请在可信环境配置，附近设备也可能连接，不能长期保持开放。
保留配置升级不会强行开启原先关闭的无线，也不会清空已有密码；官方打底后保留下来的无线设置同样沿用。

## 文件说明

```
.
├── .config                          # 编译配置文件（完整插件列表）
├── .github/workflows/
│   └── build-openwrt.yml            # GitHub Actions 自动编译脚本
├── diy-part1.sh                     # 添加第三方插件源
├── diy-part2.sh                     # 修改默认设置（主机名/时区）
├── scripts/check-build.sh           # 配置、功能包和安全版本检查
├── scripts/prepare-packages.sh      # 应用固定基线的软件包修复
├── patches/packages/                # Samba 安全升级、Transmission 挂载保护补丁
├── patches/openwrt/                 # 官方无线模板的默认开启补丁
├── files/                           # 首次启动修复及运行保护脚本
└── README.md                        # 本文件
```

## ⚠️ 注意事项

- **OpBoot 首次安装或救援恢复必须先刷同版本官方原版 `factory.ubi` 打底，再在官方后台保留配置刷本仓库的 `sysupgrade.bin`。当前对应版本为 25.12.6。**
- 不要直接用 OpBoot 首刷本仓库自编译 `factory.ubi`，也不要混用 R619AC 64M 镜像。
- 旧版 24.10.0 官方打底经验不等于新版 25.12 的安装说明；跨版本迁移请使用上面的对应版本流程。
- 刷机前**备份**旧的 WAN/WiFi/防火墙/科学上网节点配置
- 以实际镜像生成和空间检查结果为准，预留足够的 overlay 空间。
- 保留配置升级也会保留原有公网管理入口；升级固件不会自动收紧 Lucky 转发和防火墙规则。

## 致谢

- [OpenWRT](https://openwrt.org/) 官方项目
- [P3TERX/Actions-OpenWrt](https://github.com/P3TERX/Actions-OpenWrt) 编译模板
- [Openwrt-Passwall/openwrt-passwall](https://github.com/Openwrt-Passwall/openwrt-passwall) Passwall
- [kenzok8/openwrt-packages](https://github.com/kenzok8/openwrt-packages) 第三方插件合集

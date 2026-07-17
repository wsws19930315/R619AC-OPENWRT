# R619AC OpenWRT 24.10 自动编译

> 竞斗云2.0 (P&W R619AC 128M) 的 OpenWRT 固件自动化编译仓库

## 固件信息

| 项目 | 详情 |
|------|------|
| **设备** | P&W R619AC 128M (竞斗云2.0) |
| **源码** | [OpenWRT 官方](https://git.openwrt.org/openwrt/openwrt.git) `v24.10.7` 标签 |
| **内核** | Linux 6.6 |
| **架构** | Qualcomm IPQ4019 (ipq40xx / arm_cortex-a7) |

## 预装功能

### 核心功能
| 功能 | 包名 | 说明 |
|------|------|------|
| ✅ LuCI 中文界面 | `luci-i18n-*-zh-cn` | 含 Argon 主题 + 配置面板 |
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
| ✅ IPv6 | `ipv6helper` | 完整 IPv6 协议栈 |
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

**推荐流程：OpBoot 官方打底，再刷自编译固件**

1. 断电 → 按住 Reset → 通电 → 等待指示灯闪烁
2. 电脑设置静态 IP `192.168.1.2`
3. 浏览器访问 OpBoot 管理页面
4. 先上传官方原版 `openwrt-24.10.0-ipq40xx-generic-p2w_r619ac-128m-squashfs-factory.ubi`
5. 等待完成重启，进入官方 OpenWrt 后完成基础访问确认
6. 登录 LuCI → 系统 → 备份/升级
7. 上传本仓库编译出的 `*-sysupgrade.bin`
8. 勾选“保留配置”，开始升级

**通过现有 OpenWrt 升级：**
1. 登录 LuCI → 系统 → 备份/升级
2. 上传 `*-sysupgrade.bin`
3. 从官方 24.10.0 打底系统升级时，建议**保留配置**
4. 开始升级

### 首次配置

1. 网线连接 LAN 口 → 访问 `http://192.168.2.1`
2. 默认用户 `root`，无密码
3. 设置密码 → 配置 WAN → 配置 WiFi
4. 配置 Passwall（导入订阅）
5. 按需启用其他服务（Samba / SmartDNS / Transmission 等）

## 文件说明

```
.
├── .config                          # 编译配置文件（完整插件列表）
├── .github/workflows/
│   └── build-openwrt.yml            # GitHub Actions 自动编译脚本
├── diy-part1.sh                     # 添加第三方插件源
├── diy-part2.sh                     # 修改默认设置（主机名/时区）
└── README.md                        # 本文件
```

## ⚠️ 注意事项

- R619AC 通过 OpBoot 刷机时，建议先刷官方 24.10.0 `factory.ubi` 打底，再在官方后台保留配置刷本仓库的 `sysupgrade.bin`
- 不建议直接用 OpBoot 首刷本仓库自编译 `factory.ubi`
- 从旧版（21.02 等）升级到官方 24.10.0 打底时，建议先备份配置，再按实际情况决定是否保留配置
- 刷机前**备份**旧的 WAN/WiFi/防火墙/科学上网节点配置
- 128M NAND 空间充裕，当前配置不会超出限制

## 致谢

- [OpenWRT](https://openwrt.org/) 官方项目
- [P3TERX/Actions-OpenWrt](https://github.com/P3TERX/Actions-OpenWrt) 编译模板
- [Openwrt-Passwall/openwrt-passwall](https://github.com/Openwrt-Passwall/openwrt-passwall) Passwall
- [jerrykuku/luci-theme-argon](https://github.com/jerrykuku/luci-theme-argon) Argon 主题
- [kenzok8/openwrt-packages](https://github.com/kenzok8/openwrt-packages) 第三方插件合集

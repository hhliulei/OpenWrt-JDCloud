#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 OpenWrt-JDCloud 的 12 个构建配置（3 源码 × 2 机型 × 纯净/插件）。

用法：
    python3 scripts/gen-configs.py            # 重新生成 configs/*.config

生成规则说明：
- 每个 .config 都是自包含的，workflow 直接把它复制为源码树的 .config 再 make defconfig。
- 纯净版（pure）= 基础网络 + LuCI + 常用管理插件，保证稳定，不过度精简。
- 插件版（plus）= 纯净版 + OpenClash / Docker / AdGuard Home + 一批主流插件。
- 所有版本都不裁剪软件源：workflow 里用 ./scripts/feeds update -a / install -a
  拉取全部默认 feed + 本仓库追加的插件 feed，固件自带的软件仓库保持完整。
- 内核不写死版本号：各源码用自己分支的默认内核（见 SOURCES.md）。
  这里只写与 NSS / WiFi 有关的开关，内核版本由源码分支决定。

机型差异（已按上游源码核对，2026-11-15）：
- 雅典娜 RE-CS-02：三频 WiFi（ath11k + QCN9074 固件 + ipq-wifi 校准数据），
  有线/无线都支持；LiBwrt 下开 ATH11K_NSS_SUPPORT（NSS 11.4 支持 WiFi offload），
  ImmortalWrt 下关（NSS 12.5 不提供 WiFi offload，走正常 ath11k）。
- 太乙 RE-CS-07：有线路由，上游 Device 定义本身就排除了 ath11k / wpad，
  这里再明确关掉无线相关包（NoWiFi），NSS 照常开。
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "configs"

SOURCES = {
    "immortalwrt": {
        "repo": "https://github.com/laipeng668/immortalwrt.git",
        "branch": "openwrt-25.12",
        "label": "ImmortalWrt",
    },
    "libwrt": {
        "repo": "https://github.com/LiBwrt/openwrt-6.x.git",
        "branch": "25.12-nss",
        "label": "LiBwrt openwrt-6.x（NSS）",
    },
    "openwrt": {
        "repo": "https://github.com/openwrt/openwrt.git",
        "branch": "openwrt-25.12",
        "label": "官方 OpenWrt",
    },
}

DEVICES = {
    "jdcloud_re-cs-02": {"label": "雅典娜 RE-CS-02", "wifi": True},
    "jdcloud_re-cs-07": {"label": "太乙 RE-CS-07", "wifi": False},
}

FLAVOURS = ("pure", "plus")


def base_config(source: str, device: str) -> list[str]:
    """纯净版共用部分。"""
    lines = [
        "# 纯净版基础：完整网络功能 + LuCI + 常用管理插件，保证稳定，不过度精简。",
        "CONFIG_TARGET_qualcommax=y",
        "CONFIG_TARGET_qualcommax_ipq60xx=y",
        f"CONFIG_TARGET_DEVICE_qualcommax_ipq60xx_DEVICE_{device}=y",
        "CONFIG_TARGET_ROOTFS_SQUASHFS=y",
        "CONFIG_TARGET_PER_DEVICE_ROOTFS=y",
        "CONFIG_DEVEL=y",
        "CONFIG_CCACHE=y",
        "# 中文界面（LuCI 语言包）",
        "CONFIG_LUCI_LANG_zh_Hans=y",
        "CONFIG_PACKAGE_luci=y",
        "CONFIG_PACKAGE_luci-theme-argon=y",
        "CONFIG_PACKAGE_luci-app-argon-config=y",
        "CONFIG_PACKAGE_luci-i18n-base-zh-cn=y",
        "CONFIG_PACKAGE_luci-i18n-firewall-zh-cn=y",
        "CONFIG_PACKAGE_luci-i18n-package-manager-zh-cn=y",
        "CONFIG_PACKAGE_luci-app-firewall=y",
        "CONFIG_PACKAGE_luci-app-package-manager=y",
        "CONFIG_PACKAGE_luci-app-arpbind=y",
        "CONFIG_PACKAGE_luci-app-autoreboot=y",
        "CONFIG_PACKAGE_luci-app-cpufreq=y",
        "CONFIG_PACKAGE_luci-app-samba4=y",
        "CONFIG_PACKAGE_luci-app-uhttpd=y",
        "# 完整版 dnsmasq（插件版的 OpenClash / AdGuard Home 需要）",
        "CONFIG_PACKAGE_dnsmasq-full=y",
        "# CONFIG_PACKAGE_dnsmasq is not set",
        "CONFIG_PACKAGE_curl=y",
        "CONFIG_PACKAGE_ca-bundle=y",
        "CONFIG_PACKAGE_ca-certificates=y",
        "CONFIG_PACKAGE_bash=y",
        "CONFIG_PACKAGE_coreutils=y",
        "CONFIG_PACKAGE_htop=y",
        "CONFIG_PACKAGE_nano=y",
        "CONFIG_PACKAGE_unzip=y",
        "CONFIG_PACKAGE_xz=y",
        "CONFIG_PACKAGE_openssh-sftp-server=y",
        "CONFIG_PACKAGE_zoneinfo-asia=y",
        "CONFIG_PACKAGE_zram-swap=y",
        "CONFIG_PACKAGE_kmod-lib-lz4=y",
        "CONFIG_PACKAGE_block-mount=y",
        "CONFIG_PACKAGE_kmod-usb-storage=y",
        "CONFIG_PACKAGE_kmod-usb3=y",
        "CONFIG_PACKAGE_kmod-fs-ext4=y",
        "CONFIG_PACKAGE_kmod-fs-vfat=y",
        "CONFIG_PACKAGE_e2fsprogs=y",
        "CONFIG_PACKAGE_f2fs-tools=y",
        "CONFIG_PACKAGE_autocore=y",
    ]
    if DEVICES[device]["wifi"]:
        lines += [
            "# 雅典娜三频 WiFi",
            "CONFIG_PACKAGE_kmod-ath11k-pci=y",
            "CONFIG_PACKAGE_ath11k-firmware-qcn9074=y",
            "CONFIG_PACKAGE_ipq-wifi-jdcloud_re-cs-02=y",
            "CONFIG_PACKAGE_wpad-basic-mbedtls=y",
            "CONFIG_PACKAGE_hostapd-common=y",
            "# 雅典娜顶部点阵屏（diy-part1.sh 从 NONGFAH/luci-app-athena-led 拉取）",
            "CONFIG_PACKAGE_luci-app-athena-led=y",
            "CONFIG_PACKAGE_luci-i18n-athena-led-zh-cn=y",
        ]
    else:
        lines += [
            "# 太乙是有线路由：上游 Device 定义本身已排除 ath11k / wpad，这里再明确关掉（NoWiFi）",
            "# CONFIG_PACKAGE_kmod-ath11k is not set",
            "# CONFIG_PACKAGE_kmod-ath11k-ahb is not set",
            "# CONFIG_PACKAGE_kmod-ath11k-pci is not set",
            "# CONFIG_PACKAGE_ath11k-firmware-ipq6018 is not set",
            "# CONFIG_PACKAGE_ath11k-firmware-qcn9074 is not set",
            "# CONFIG_PACKAGE_ipq-wifi-jdcloud_re-cs-07 is not set",
            "# CONFIG_PACKAGE_wpad-basic-mbedtls is not set",
            "# CONFIG_PACKAGE_hostapd-common is not set",
        ]
    if source == "libwrt":
        lines += [
            "# LiBwrt NSS：固件版本 11.4（该分支的 WiFi offload 只支持 11.4）",
            "CONFIG_NSS_FIRMWARE_VERSION_11_4=y",
            "# CONFIG_NSS_FIRMWARE_VERSION_12_5 is not set",
            "CONFIG_ATH11K_MEM_PROFILE_512M=y" if DEVICES[device]["wifi"] else "",
            "CONFIG_PACKAGE_kmod-qca-nss-drv=y",
            "CONFIG_PACKAGE_kmod-qca-nss-ecm=y",
        ]
        if DEVICES[device]["wifi"]:
            lines += [
                "CONFIG_ATH11K_NSS_SUPPORT=y",
                "CONFIG_ATH11K_NSS_MESH_SUPPORT=y",
            ]
    elif source == "immortalwrt":
        lines += [
            "# ImmortalWrt：用测试内核（CONFIG_TESTING_KERNEL，当前为 6.18）+ NSS 12.5",
            "# 注意：IPQ60xx 的 NSS 12.5 不提供 WiFi offload，走正常 ath11k",
            "CONFIG_TESTING_KERNEL=y",
            "CONFIG_NSS_FIRMWARE_VERSION_12_5=y",
            "# CONFIG_NSS_FIRMWARE_VERSION_11_4 is not set",
        ]
        if DEVICES[device]["wifi"]:
            lines += [
                "# IPQ60xx 的 NSS 12.5 不提供 WiFi offload，走正常 ath11k",
                "# CONFIG_ATH11K_NSS_SUPPORT is not set",
                "# CONFIG_ATH11K_NSS_MESH_SUPPORT is not set",
                "CONFIG_ATH11K_MEM_PROFILE_512M=y",
            ]
    else:  # openwrt
        lines += [
            "# 官方 OpenWrt：上游不含 NSS 闭源加速，走原生 ath11k + flow offload",
            "# （本段不写任何 NSS 开关）",
        ]
    # 去掉上面条件表达式产生的空行
    return [line for line in lines if line != ""]


def plus_config() -> list[str]:
    """插件版在纯净版基础上追加的部分。"""
    return [
        "# ---- 插件版追加（在纯净版基础上） ----",
        "# 容器：Docker / Dockerman",
        "CONFIG_PACKAGE_dockerd=y",
        "CONFIG_PACKAGE_docker=y",
        "CONFIG_PACKAGE_docker-compose=y",
        "CONFIG_PACKAGE_luci-app-dockerman=y",
        "CONFIG_PACKAGE_luci-lib-docker=y",
        "CONFIG_PACKAGE_ttyd=y",
        "CONFIG_PACKAGE_luci-app-ttyd=y",
        "CONFIG_PACKAGE_kmod-veth=y",
        "CONFIG_PACKAGE_kmod-br-netfilter=y",
        "# 透明代理：OpenClash（主）+ PassWall2",
        "CONFIG_PACKAGE_luci-app-openclash=y",
        "CONFIG_PACKAGE_luci-app-passwall2=y",
        "CONFIG_PACKAGE_ipset=y",
        "CONFIG_PACKAGE_ip-full=y",
        "CONFIG_PACKAGE_kmod-nft-tproxy=y",
        "CONFIG_PACKAGE_kmod-nft-queue=y",
        "CONFIG_PACKAGE_kmod-tun=y",
        "# DNS：AdGuard Home + SmartDNS",
        "CONFIG_PACKAGE_adguardhome=y",
        "CONFIG_PACKAGE_luci-app-adguardhome=y",
        "CONFIG_PACKAGE_smartdns=y",
        "CONFIG_PACKAGE_luci-app-smartdns=y",
        "# 常用管理：DDNS / UPnP / 磁盘管理 / 网络唤醒 / 看门狗",
        "CONFIG_PACKAGE_luci-app-ddns=y",
        "CONFIG_PACKAGE_ddns-scripts=y",
        "CONFIG_PACKAGE_luci-app-upnp=y",
        "CONFIG_PACKAGE_luci-app-diskman=y",
        "CONFIG_PACKAGE_luci-app-hd-idle=y",
        "CONFIG_PACKAGE_luci-app-wol=y",
        "CONFIG_PACKAGE_luci-app-watchcat=y",
        "# 应用商店（仅 ImmortalWrt / LiBwrt 有 istore feed；官方 OpenWrt 下 make defconfig 会自动丢掉这一行）",
        "CONFIG_PACKAGE_luci-app-store=y",
        "CONFIG_PACKAGE_luci-lib-taskd=y",
        "CONFIG_PACKAGE_taskd=y",
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for source, sinfo in SOURCES.items():
        for device, dinfo in DEVICES.items():
            for flavour in FLAVOURS:
                lines = [
                    f"# OpenWrt-JDCloud：{sinfo['label']} / {dinfo['label']} / "
                    + ("纯净版" if flavour == "pure" else "插件版"),
                    f"# 源码：{sinfo['repo']}（分支 {sinfo['branch']}）",
                    "# 内核：不写死版本，用该分支的默认内核（见 SOURCES.md）",
                    "# 默认：LAN 192.168.10.1，主机名 ll，root/root，Argon 主题，中文",
                    "# 软件源：不裁剪，workflow 用 feeds update/install -a 拉取全部 feed",
                    "",
                ]
                lines += base_config(source, device)
                if flavour == "plus":
                    lines += [""] + plus_config()
                name = f"{source}-{device}-{flavour}.config"
                (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
                print(f"wrote configs/{name}")


if __name__ == "__main__":
    main()

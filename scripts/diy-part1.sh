#!/usr/bin/env bash
# diy-part1.sh —— 在 feeds 更新之前追加第三方软件源。
# 用法（在仓库根目录，源码已克隆到 $OPENWRT_DIR，默认 openwrt）：
#     OPENWRT_DIR=openwrt bash scripts/diy-part1.sh <source> <device> <flavour>
# source: immortalwrt | libwrt | openwrt
#
# 说明：
# - 这里只往 feeds.conf.default 里加 feed，不裁剪任何默认 feed；
#   workflow 随后用 ./scripts/feeds update -a / install -a 拉取全部 feed，
#   固件自带的软件仓库保持完整，刷完以后任何插件都能自己装。
# - Argon 主题、athena-led 不在这里处理：它们要 clone 到 feeds / package 目录，
#   必须等 feeds update 之后，由 diy-part2.sh 做（见 Roc-script 的做法）。

set -Eeuo pipefail

SOURCE="${1:?用法：diy-part1.sh <source> <device> <flavour>}"
DEVICE="${2:?用法：diy-part1.sh <source> <device> <flavour>}"
FLAVOUR="${3:?用法：diy-part1.sh <source> <device> <flavour>}"
OPENWRT_DIR="${OPENWRT_DIR:-openwrt}"
FEEDS_CONF="$OPENWRT_DIR/feeds.conf.default"

[ -f "$FEEDS_CONF" ] || { echo "找不到 $FEEDS_CONF：请先克隆源码到 $OPENWRT_DIR" >&2; exit 1; }

add_feed() {
    local line="$1"
    if grep -qxF "$line" "$FEEDS_CONF"; then
        echo "feed 已存在，跳过：$line"
    else
        echo "$line" >> "$FEEDS_CONF"
        echo "已追加 feed：$line"
    fi
}

# OpenClash（插件版需要；纯净版只加源不选包，不影响纯净版体积）
add_feed "src-git openclash https://github.com/vernesong/OpenClash.git"
# PassWall2 及其依赖包源
add_feed "src-git passwall2 https://github.com/Openwrt-Passwall/openwrt-passwall2.git"
add_feed "src-git pw_packages https://github.com/Openwrt-Passwall/openwrt-passwall-packages.git"

# iStore 应用商店：只有 ImmortalWrt / LiBwrt 有这条 feed，官方 OpenWrt 不加
# （官方 OpenWrt 的配置里 luci-app-store 这一行会被 make defconfig 自动丢掉）
case "$SOURCE" in
    immortalwrt|libwrt)
        add_feed "src-git istore https://github.com/linkease/istore.git"
        ;;
    openwrt)
        echo "官方 OpenWrt：跳过 istore feed"
        ;;
    *)
        echo "未知 source：$SOURCE（应为 immortalwrt / libwrt / openwrt）" >&2
        exit 1
        ;;
esac

echo "diy-part1 完成：$SOURCE / $DEVICE / $FLAVOUR"

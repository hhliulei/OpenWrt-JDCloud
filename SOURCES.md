# 源码与分支说明（SOURCES.md）

本仓库不 fork 上游源码：每次构建由 workflow 按下表实时克隆上游仓库，
内核用各分支的默认版本，不写死版本号。分支与内核版本是 2026-11-15
实测核对过的（`git ls-remote` + 稀疏克隆读 `target/linux/qualcommax/Makefile`）。

## 源码对照表

| 源码（本仓库代号） | 上游仓库 | 分支 | 内核（该分支默认） | NSS | WiFi |
| --- | --- | --- | --- | --- | --- |
| ImmortalWrt（`immortalwrt`） | `laipeng668/immortalwrt.git` | `openwrt-25.12` | 6.12，构建时开 `CONFIG_TESTING_KERNEL` 用测试内核（当前为 6.18） | NSS 12.5 | 雅典娜：正常 ath11k（12.5 不提供 WiFi offload）；太乙：无 |
| LiBwrt（`libwrt`） | `LiBwrt/openwrt-6.x.git` | `25.12-nss`（该仓库唯一分支） | 6.12 | NSS 11.4 | 雅典娜：`ATH11K_NSS_SUPPORT` 开（WiFi offload）；太乙：无 |
| 官方 OpenWrt（`openwrt`） | `openwrt/openwrt.git` | `openwrt-25.12` | 6.12 | 无（上游不含 NSS 闭源加速） | 雅典娜：正常 ath11k；太乙：无 |

说明：
- ImmortalWrt 用 `laipeng668/immortalwrt` 这个 fork 而不用官方 `immortalwrt/immortalwrt`，
  因为 Wall-WRT / laipeng668/openwrt-ci-roc 都是用它做雅典娜适配（含 NSS 12.5 与
  Athena 相关补丁）；官方 ImmortalWrt 同样有 `openwrt-25.12` 分支，可随时换回。
- LiBwrt 的 `25.12-nss` 是 `LiBwrt/openwrt-6.x` 的唯一分支，`laipeng668/openwrt-6.x`
  是同一份代码的镜像（2026-11-15 核对过 HEAD 一致）。
- 官方 OpenWrt 的 `main` 分支内核已是 6.18，但为求稳定，本仓库先用 `openwrt-25.12`
  稳定分支；想跟 main 的话，把 workflow / build.sh 里的 `REPO_BRANCH` 改成 `main` 即可。

## 机型对照表

| 机型 | 设备名（.config / 上游 Device） | SoC | WiFi | 备注 |
| --- | --- | --- | --- | --- |
| 雅典娜 | `jdcloud_re-cs-02` | IPQ6010 | 三频 WiFi 6：2.4G + 5G-1 + 5G-2，ath11k + QCN9074 固件 + `ipq-wifi-jdcloud_re-cs-02` 校准数据 | 顶部点阵屏用 `luci-app-athena-led`（diy-part2.sh 从 NONGFAH 拉取） |
| 太乙 | `jdcloud_re-cs-07` | IPQ6010 | 无（NoWiFi） | 上游 Device 定义本身就排除了 ath11k / wpad；本仓库配置里再明确关掉 |

两个机型在上游 `target/linux/qualcommax/image/ipq60xx.mk` 里都有
`define Device/jdcloud_re-cs-02` / `define Device/jdcloud_re-cs-07`，
`KERNEL_SIZE := 6144k`，`FitImage` 格式；LiBwrt 里还多一个 `EmmcImage`，
所以 LiBwrt 的构建会额外产出 `factory.bin`。

## 追加的插件 feed（scripts/diy-part1.sh）

| feed | 地址 | 用途 |
| --- | --- | --- |
| `openclash` | `vernesong/OpenClash.git` | OpenClash |
| `passwall2` | `Openwrt-Passwall/openwrt-passwall2.git` | PassWall2 |
| `pw_packages` | `Openwrt-Passwall/openwrt-passwall-packages.git` | PassWall2 依赖包 |
| `istore` | `linkease/istore.git` | iStore 应用商店（只加 ImmortalWrt / LiBwrt，官方 OpenWrt 不加） |

另外两个不在 feed 里的包由 diy-part2.sh 直接 clone：
- Argon 主题与配置插件：`jerrykuku/luci-theme-argon`、`jerrykuku/luci-app-argon-config`
  （master 分支，放到 `feeds/luci/themes|applications` 下面）。
- 雅典娜点阵屏：`NONGFAH/luci-app-athena-led`（放到 `package/` 下面，只在雅典娜构建时拉）。

## 软件源为什么是“全的”

workflow 里跑的是 `./scripts/feeds update -a` / `./scripts/feeds install -a`，
不裁剪任何默认 feed，也不删追加的 feed。固件自带的软件仓库（`/etc/opkg/distfeeds.conf`
或 apk 仓库配置）因此包含全部 feed，刷完以后任何插件都能自己装。
纯净版只是“没预装”扩展插件，不是“装不上”。

## 假设与不确定点（首次构建前请核对）

1. **设备名拼写**：配置里用的是上游 `TARGET_DEVICES` 的写法
   `CONFIG_TARGET_DEVICE_qualcommax_ipq60xx_DEVICE_jdcloud_re-cs-02=y`（带 `-`），
   和 laipeng668/openwrt-ci-roc 的配置一致。Wall-WRT 的生成器用的是下划线写法
   `jdcloud_re_cs_02`。workflow 的 defconfig 步骤会校验这一行，丢了就直接报错，
   不会悄悄编出别的机型；如果报错，按报错提示换一种拼写再试。
2. **NSS 驱动包名**：LiBwrt 配置里写了 `kmod-qca-nss-drv` / `kmod-qca-nss-ecm`。
   如果该分支里包名有变，`make defconfig` 会静默丢掉这一行，NSS 加速可能不生效，
   请以首次构建的 `Config-*.txt` 为准核对（Release 里自带）。
3. **ImmortalWrt 测试内核**：`CONFIG_TESTING_KERNEL=y` 会让 ImmortalWrt 用测试内核
   （当前 6.18）。测试内核可能随上游更新而变化；如果想要最稳的 6.12，
   把 `configs/immortalwrt-*.config` 里的 `CONFIG_TESTING_KERNEL=y` 删掉。
4. **athena-led 默认分支**：diy-part2.sh 先按 `main` 拉，失败再按 `master` 拉；
   如果 NONGFAH 的仓库改了默认分支名，两次都会失败，构建会在这一步报错，
   按报错信息改分支名即可。
5. **iStore 与官方 OpenWrt**：`luci-app-store` 只在 ImmortalWrt / LiBwrt 的
   plus 版里生效；官方 OpenWrt 的 plus 版没有 istore feed，
   `make defconfig` 会自动丢掉这一行，不影响构建。
6. **Docker 与雅典娜 1GB 内存**：雅典娜出厂只有 1GB 内存，跑 Docker 很吃紧，
   建议优先在太乙（2GB）上用 Docker，或给雅典娜扩内存后再用。
7. **factory.bin**：LiBwrt 的 Device 定义带 `EmmcImage`，会产出 `factory.bin`；
   ImmortalWrt / 官方 OpenWrt 的 Device 定义目前只有 `FitImage`，
   首次刷机请按 docs/FLASHING.md 用 initramfs + sysupgrade 的流程，
   不要拿 sysupgrade 当 factory 用。

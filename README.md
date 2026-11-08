# AI Quests 官方原版本地镜像

2026-11-08 为 YOYO 保存官方原版，并按用户后续授权新增原生简体中文 zh_cn。英文及其他官方语言保留，原版基线标签不变。

## 打开与停止

双击本目录的 `启动AI-Quests.cmd`，后台启动服务并打开浏览器。双击 `停止AI-Quests.cmd`，只停止本工程核验归属的进程。

- 中文入口：http://127.0.0.1:4192/ai-quests/intl/zh_cn
- 英文入口：http://127.0.0.1:4192/ai-quests/intl/en_us
- 项目：`D:\WorkSpace Development\AppResource\AI-Quests`
- 服务仅监听本机127.0.0.1，目前不提供其他电脑或平板访问。
- 日常运行只需本机Node.js，不必安装验证工具或联网。
- 官方程序将进度保存在当前浏览器的本地存储；换浏览器、隐私模式或清理站点数据会影响进度。

## 保存范围

来源：https://research.google/ai-quests/intl/en_us 。固定内容快照 `20261023-141713`，前端构建 `73ffd59-1792762873172`。

- 三个关卡：Market Marshes（洪水预测）、Dusky Dunes（眼病预防）、Polar Peaks（脑科学）。
- 当前启用的13个语言入口及内容数据，所有发现且官方可下载的JS、CSS、字体、图片、音效、视频、3D模型及Draco解码器。
- 关于、FAQ、教师资源、隐私说明、学生展示页面。五份教师讲义已保存PDF，并将对应链接改成本地文件。
- 官方当前没有简体中文配置。本地不使用第三方收费镜像文件。

## 目录与本地适配

- `public/`：本地服务唯一公开的网页与资源目录。
- `upstream-text/`：官方HTML、JS、CSS、JSON、SVG等文本原件，供对照及后续汉化；二进制原件保存在public，其原始哈希见清单。
- `reports/manifest.json`：来源URL、文件路径、字节数、原始SHA-256、内容类型及失败候选。
- `reports/local-modifications.json`：本地适配后的文本哈希及对应原件哈希。
- `reports/`：离线页面、关卡、语言、完整性、安全、依赖审计及外链归档结果。
- `scripts/`：下载、构建、服务器和验证脚本。
- `archive-config.json`：固定归档快照，重新运行下载脚本不会主动切换快照。
- `tooling/`：仅用于尝试归档外部展示视频的下载工具，不参与游戏运行。

保留官方游戏、文字及素材。CDN地址改成本地路径，移除Google Analytics/Tag Manager、Partytown、无需使用的Cookie通知及预加载提示；原件保留供对照。没有增加付费、登录或聊天服务。服务仅允许GET/HEAD，支持媒体Range请求，提供CSP等安全响应头。

## 验证证据

- 1,746个归档文件、1,085,015,830字节，约1.01GiB，原始哈希全部一致。
- 英文JSON的384项有效素材引用无缺失；605个音视频文件的分段读取全部通过。
- 首次进入、开场视频、地图、进度恢复、启动/停止/再次启动已实测。
- 三个关卡在阻断外网的独立浏览器中，开场视频能播放，并可进入各自3D场景和首个任务对话；缺失请求、外部请求、页面异常均为0。
- 13个语言首页离线打开通过；关于、FAQ、教师资源及隐私说明的离线页面检查通过。
- 路径越界、读取私有目录、写请求拒绝、无效Range和安全响应头检查通过。
- 新增npm验证依赖审计为0已知漏洞。官方打包程序的全部内部依赖未做完整源码安全审计。

## 已知边界

1. 尚未逐题完成三个关卡的全部题目、分支和通关流程；当前证据为资源检查及实际3D任务场景的离线验证。其他语言也没有逐题通关。
2. 学生展示页引用17个YouTube视频。页面及引用清单已保存；首个视频匿名下载失败后停止批量下载，这些外链仍需要联网。官方游戏内的音视频已保存本地。
3. Google官网、支持中心、隐私政策等外部网站保留原地址，不递归复制整个外部网站。教师讲义的五份PDF已本地化。
4. 官方脑科学CMS含18个tbd占位字段，原样保留。已核对发布脚本的实际训练动画使用内置neuron-right/neuron-wrong素材，这些资源已保存。
5. 清单保留官方404的开发示例、默认内容、其他语言旧引用及探测候选。失败候选不是成功归档文件，也不直接等于有效素材缺失；英文有效素材无缺失。
6. 保存的是官方公开发布构建，没有取得Google内部开发工程；保留Google/Stanford标识和版权内容。

## 复核与维护

先启动服务，在本目录执行：

```powershell
python scripts/verify-integrity.py
node scripts/verify-flow.mjs
node scripts/verify-quests.mjs
node scripts/verify-locales.mjs
node scripts/verify-pages.mjs
```

验证脚本使用本机已安装Chromium路径，迁移电脑时需调整；日常运行不依赖验证工具。

补充归档顺序：`python scripts/mirror.py` → `python scripts/complete-assets.py` → `python scripts/build-local.py`。下载需要联网。任何版本更新、汉化和程序修改，先保留当前原件、清单及修改记录。

## GitHub版本管理

2026-11-08用户授权上传至GitHub私人仓库 `VikasDhanve/AI-Quests`。文本使用普通Git，音视频、图片、字体、模型、PDF等使用Git LFS；本次官方原版标签为 `official-baseline-2026-11-08`。

新电脑恢复：先安装Git LFS，运行 `git lfs install`，再克隆仓库；克隆后检查 `git lfs pull` 与 `git lfs fsck`，确保资源是完整文件。直接下载GitHub源码ZIP不作为可靠的素材恢复方式，因为压缩包可能只包含LFS指针。

排除node_modules、tooling、Python缓存、运行日志/PID和浏览器测试存档。日常运行只需要Node.js；验证依赖可通过 `npm ci` 安装，首次测试先运行 `node scripts/verify-flow.mjs` 生成本机临时存档，再验证关卡。原版资源、脚本、五份讲义、哈希及验收报告随仓库保存。

后续汉化以独立提交记录，需要时从基线标签恢复原版。大素材更新会增加LFS历史存储，下载会消耗账户LFS流量；不启用新的付费设置。

上传核验完成：私人仓库 https://github.com/VikasDhanve/AI-Quests ，原版标签 `official-baseline-2026-11-08` 指向 `f690149`。服务端确认1392个独立LFS对象全部可用，素材无缺失；未另外再下载整库做恢复演练。验收元数据见 `reports/github-upload.json`。

## 简体中文版本（2026-11-08）

语言菜单新增“简体中文”，无需安装插件。已翻译三个任务的数据、题目、对话、字幕及关于、FAQ、教师资源、隐私、展示页面。中文地名统一为集市沼泽、暮色沙丘、极地之巅。配音、教程演示视频/图片中的内嵌英文和教师PDF保留官方原版；没有制作中文配音或重绘原素材。

翻译参考 Coopa Study 作者维护的 https://github.com/notwin/coopa-study ，固定提交9ea4b867ce4857779d3cf84bfb423d12c7136049。Chrome商店隐私政策和支持链接直接指向此仓库，属于插件作者的官方仓库，不能称为Google官方仓库。导入730个与当前英文一致的字段，其余及大脑任务另行补译。原始参考文件、来源与哈希保存在localization/reference/coopa-study，MIT许可见THIRD_PARTY_NOTICES.md。

翻译表在localization/zh_cn，运行 `python scripts/build-local.py` 从保留的官方文本重新生成本地版本，再自动生成中文。不要直接改生成的public文件。进度编码支持UTF-8并兼容已有英文存档；原版资源和题目控制值保持不变。

验证：`npm run verify:zh`，另运行完整性与所有语言入口检查。报告包括zh-browser.json、quests-zh-offline.json、pages-zh-offline.json、zh-data-validation.json。三个任务已验证离线视频、字幕、首个3D场景；大脑任务另用隔离测试存档检查后段标注界面。尚未逐题完成三个关卡的全部分支和通关流程。

大脑标注后段的隔离存档测试发现一次指向/ai-quests/的空资源请求；相同英文场景也存在，未将它统计成汉化新增的文件缺失。测试报告保留该记录。

# AI Quests 阿里云部署与运维

部署记录：2026-11-09。以下线上版本信息为当时发布结果；2026-11-19本地发布模板已更新，尚未重新发布到云端。

## 访问与版本

- 访问：http://182.92.231.54/ ，默认进入简体中文。
- 教师资源：http://182.92.231.54/ai-quests/intl/zh_cn/teacher-resources 。
- 服务器：北京轻量应用服务器（SWAS），实例 cc42a709c6f641e687bdbfad600a83f0。
- 发布：20261109T090144Z-52da1bd；游戏内容对应 Git 52da1bd4aedabc8cb2765e9c64ec2e7ab33c1a5e。
- 发布包 SHA256：fef65c2483aabc96dcb654021bd232cc8b8a3fb3f278542b02c17f4d8b509384。
- 1779个发布文件，1128630099字节；服务器完整SHA256与本地匹配。
- 用户明确先使用IP；域名orionux.cn尚不接入，HTTPS未配置。
- 进度仍存浏览器；本机、IP和未来域名是不同来源，进度不会自动互通。
- 新增部署配置和脚本保留在本目录，本轮未提交/推送Git，不修改本机Nginx及4192服务。

## 目录规则

```text
/srv/apps/
  README.md                         服务器多项目规范
  ai-quests/
    releases/<UTC时间>-<Git版本>/    public、发布清单及该版配置
    current                         指向当前版本的符号链接
    incoming/                       admin专属临时上传区
    backups/                        受限备份：发布包、Nginx原配置
    ops/                            发布脚本、当前版本、验证结果和说明
```

后续项目沿用/srv/apps/<小写英文项目名>/，先查实际端口和磁盘；网站通过独立域名和/etc/nginx/conf.d/<项目名>.conf区分。后台服务用各自systemd单元，避免混放。当前项目是静态站点，不安装Node、Docker或数据库。

- 主配置：/etc/nginx/nginx.conf。
- 项目配置：/etc/nginx/conf.d/ai-quests.conf。
- 日志：/var/log/nginx/ai-quests.access.log、ai-quests.error.log。
- 系统日志轮转：/etc/logrotate.d/nginx，每日轮转、保留10份、压缩。
- 服务：系统源nginx/1.24.0，systemd已启用开机启动，IPv4/IPv6监听80。
- 云防火墙原有80/443/22/ICMP规则保持，未新增规则；443当前没有HTTPS服务。

## 更新流程

1. 本机确认public是准备发布的内容，在工程根运行python deployment/aliyun/prepare-release.py。
2. 查看artifacts/latest-package.json。脚本按清单验证官方原件及本地改动哈希，生成全文件清单和带SHA256的发布包；大包和验证证据被.gitignore排除。
3. 通过云助手准备临时文件传输权限，核验服务器主机公钥；将包上传到项目incoming，部署脚本保存到ops。不要把AK/Secret复制到服务器。
4. 以root运行ops/activate-release.sh <release-id> <archive-sha256>。脚本验证路径、备份原配置、核验压缩包和全部文件，再原子切换current并执行nginx -t、启动或平滑重载；激活阶段失败时恢复原配置及原指针。
5. 本机执行python deployment/aliyun/verify-deployment.py http://182.92.231.54，以及node deployment/aliyun/verify-browser.mjs http://182.92.231.54。
6. 核对真实图面、归档报告，移除临时公钥与本机临时私钥。现有用户密钥和Workbench凭证保持。

每次更新保留上一版，不自动清理发布历史。同盘备份只防误改，不替代异地备份；历史增长后按磁盘容量另行决定保留数量。

## 日常操作与回退

- 检查：sudo nginx -t；systemctl status nginx。
- 平滑重载：sudo systemctl reload nginx。
- 查看错误：sudo tail -n 80 /var/log/nginx/ai-quests.error.log。
- 回退需先备份现状，核验旧版本清单，恢复对应Nginx配置与current指针，nginx -t通过后平滑重载。当前是首个业务发布版本，没有更早业务版本；原发行版Nginx配置已备份。未在生产执行历史版本回退或整机重启演练。
- 本机CLI：C:/Users/yamal/AppData/Local/Programs/AliyunCLI/aliyun.exe，使用swas-open，不使用Workbench的ECS查询接口。
- 本机Workbench保存的凭证仅通过进程临时环境变量供通用CLI使用。不可开启含凭证的调试输出，不把密钥写入命令行/笔记/Git。

## 验收与范围

- 服务器1779文件完整哈希一致；初始部署没有丢失LFS素材。
- 公网209无后缀MIME、605媒体Range、14语言首页、三关深层路由、五份中文PDF、安全响应头、私有路径及写请求拒绝通过。
- 独立浏览器通过中文首页、20条开场字幕、三个中文地图名称、集市沼泽首个3D对话、五个中文PDF入口及29条教师字幕；无失败HTTP、页面异常或外部资源请求。
- 图面：artifacts/20261109T090144Z-52da1bd/内cloud-home、cloud-scene、cloud-map、cloud-teachers等PNG；HTTP/browser JSON报告同目录。
- 服务器内存可用约597MiB，根盘剩余约22GiB（发布后实测）。
- 初次验收脚本遇到Windows编码/异步弹窗等待，修复后重跑通过；初始首页截图早于入场动画，补拍静止图。服务器应用代码未因此更改。
- 未逐题通关所有分支、验证真实手机/平板、域名/HTTPS或生产回退；学生展示页YouTube外链仍需联网。


收尾确认：服务器临时公钥已撤销且重连被拒绝，本机临时私钥已删除；incoming为空，备份目录700、未来发布umask077。ops/cleanup.json记录清理结果，既有登录密钥和Workbench凭证保持。

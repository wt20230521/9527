# 📋 代理节点订阅

&gt; 🚀 **快速入口**：https://wt20230521.github.io/9527/ （一键复制订阅链接）

---

## 代理自动抓取 - GitHub Actions 部署指南

...

## 功能

每6小时自动抓取代理，验证有效性，并更新到仓库。

## 部署步骤

### 1. 创建 GitHub 仓库

访问 https://github.com/new
- 仓库名称：`proxy-list`（或任意名称）
- 选择 **Private**（私有，更安全）
- 勾选 **Add a README file**
- 点击 **Create repository**

### 2. 上传文件

在仓库中创建以下文件结构：

```
proxy-list/
├── .github/
│   └── workflows/
│       └── update-proxy.yml      ← 工作流文件
├── proxy_fetcher.py              ← 抓取脚本
└── README.md                     ← 本文件
```

上传方式：
- 方式1：直接网页上传（GitHub 网页 → Add file → Upload files）
- 方式2：Git 命令行推送

### 3. 配置 Actions 权限

进入仓库 → **Settings** → **Actions** → **General**

找到 **Workflow permissions**：
- 选择 **Read and write permissions**
- 勾选 **Allow GitHub Actions to create and approve pull requests**
- 点击 **Save**

### 4. 手动触发测试

进入仓库 → **Actions** → **Update Proxy List** → **Run workflow**

等待运行完成，检查是否生成 `proxies_valid_node.txt` 文件。

### 5. 获取使用 URL

运行成功后，你的代理列表 URL 为：

```
https://raw.githubusercontent.com/你的用户名/proxy-list/main/proxies_valid_node.txt
```

按国家分类的 URL：
```
https://raw.githubusercontent.com/你的用户名/proxy-list/main/proxies_TW.txt
https://raw.githubusercontent.com/你的用户名/proxy-list/main/proxies_HK.txt
https://raw.githubusercontent.com/你的用户名/proxy-list/main/proxies_JP.txt
https://raw.githubusercontent.com/你的用户名/proxy-list/main/proxies_KR.txt
https://raw.githubusercontent.com/你的用户名/proxy-list/main/proxies_SG.txt
https://raw.githubusercontent.com/你的用户名/proxy-list/main/proxies_US.txt
```

### 6. 在工具中使用

在工具的"获取URL"框中填入上述 URL 即可。

## 定时设置

默认每6小时运行一次，可修改 `.github/workflows/update-proxy.yml`：

```yaml
schedule:
  - cron: '0 */6 * * *'   # 每6小时
  - cron: '0 0 * * *'     # 每天0点
  - cron: '0 */12 * * *'  # 每12小时
```

Cron 格式说明：`分 时 日 月 周`

## 安全建议

1. **使用私有仓库** - 防止他人直接访问 raw 链接
2. **定期查看 Actions 日志** - 确认运行正常
3. **不要泄露仓库 URL** - 虽然私有，但 raw 链接理论上可被猜测

## 文件说明

| 文件 | 说明 |
|:---|:---|
| `proxies_valid_node.txt` | 全部有效代理（节点格式） |
| `proxies_TW.txt` | 台湾代理 |
| `proxies_HK.txt` | 香港代理 |
| `proxies_JP.txt` | 日本代理 |
| `proxies_KR.txt` | 韩国代理 |
| `proxies_SG.txt` | 新加坡代理 |
| `proxies_US.txt` | 美国代理 |

## 节点格式

```
IP:端口#地区
IP:端口#地区家宽
```

示例：
```
103.53.81.113:39336#日本
61.38.141.90:10005#韩国家宽
```

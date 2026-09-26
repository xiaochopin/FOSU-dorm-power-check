# FOSU-dorm-power-check
佛山大学宿舍电量预警，通过 GitHub Actions 自动运行，低于阈值创建 issue 进行提醒，电量恢复后自动关闭 issue。


## 功能

- ⏰ 定时查询电量接口（可自定义运行方案）
- 📧 电量低于阈值时自动创建 Issue，GitHub 会给你发邮件
- 🔄 电量恢复后自动关闭 Issue
- 🔔 持续低电量时，每次运行在该 Issue 下追加评论提醒
- 🔧 所有参数通过 Secrets 配置。


## 工作原理

```
GitHub Actions（定时）
      │
      ▼
  查询电量接口 ──► 拿到剩余度数
      │
      ▼
  低于阈值？
   ├─ 是 → 创建 Issue / 追加评论 → 你收到邮件
   └─ 否 → 关闭已有 Issue
```

Issue 的 assignee 是仓库拥有者，所以**你一定会收到 GitHub 邮件通知**，不需要额外配置邮件服务。


## 快速开始

1. 点本仓库右上角 **Use this template** → 创建你自己的仓库
2. 按 [抓包教程](#抓包教程) 拿到接口信息
3. 按 [配置 Secrets](#配置-secrets) 填入 5 个 Secret
4. 去 Actions 标签，手动运行一次验证
5. （可选）启用定时任务



## 抓包教程

> 目标：拿到查询电量时小程序发出的那个 HTTP 请求，最终提取出 **5 个参数**。

### 准备工具

推荐 **Fiddler Classic**（Windows）或 **mitmproxy**（跨平台）。

| 工具 | 适用 | 下载 |
|---|---|---|
| Fiddler Classic | Windows | https://www.telerik.com/fiddler |
| mitmproxy | Windows / macOS / Linux | https://mitmproxy.org |
| Charles | macOS | https://www.charlesproxy.com |

下面以 **PC 微信 + Fiddler** 为例，这是成功率最高的方式。

### 方案 A：PC 微信 + Fiddler（推荐）

#### 1. 安装并配置 Fiddler

1. 安装 Fiddler Classic
2. 打开后进入 `Tools → Options → HTTPS`
3. 勾选：
   - `Capture HTTPS CONNECTs`
   - `Decrypt HTTPS traffic`
4. 弹窗提示装证书 → 点 `Yes`，装到 Windows 受信任根证书
5. 确认左下角状态是 `Capturing`

#### 2. 完全退出微信

**关键一步**，否则旧连接可能会复用，抓不到请求。

#### 3. 抓包

1. 重新打开 PC 微信
2. 进入你学校的小程序
3. 进入电量查询页面
4. 回 Fiddler，左侧会刷出请求

#### 4. 定位电量请求

在 Fiddler 里按 `Ctrl+F`，**搜索你在小程序里看到的电量数字**（例如 `114.51`）。

搜到的那条响应，就是电量接口。

#### 5. 提取信息

点选那条请求。

**上半部分 Request（请求）**：

| 需要记录 | 在哪看 |
|---|---|
| token | `Headers` 里找 `Cookies`-`token` |

**下半部分 Response（响应）**：

| 需要记录 | 在哪看 |
|---|---|
| implType | `JSON` 标签 |
| schoolAreaNo | `JSON` 标签 |
| buildingNo | `JSON` 标签 |
| roomNum | `JSON` 标签 |


### 用 curl 验证

问 AI 给你一条验证代码就行了这里不再赘述。嫌麻烦可以跳过这一步。

把你抓取的内容和下面这段发给任意 AI，让它帮你生成验证命令：

```
请帮我生成一条 curl 命令，要求：

- 方法：POST
- URL：https://user.fosu.edu.cn/powerfee/getBalance
- 请求头：Content-Type: application/x-www-form-urlencoded
- 请求体（x-www-form-urlencoded）：
    implType=<填入>
    schoolAreaNo=<填入>
    buildingNo=<填入>
    roomNum=<填入>
    from=wxminiprogram
    token=<填入你的 token>
```


## 配置 Secrets

仓库 → **Settings → Secrets and variables → Actions → New repository secret**

依次添加 5 个：

| 抓到的值的名称 | 对应secret名称 |
|---|---|
| token | `DORM_TOKEN` |
| implType | `IMPL_TYPE` |
| schoolAreaNo | `SCHOOL_AREA_NO` |
| buildingNo | `BUILDING_NO` |
| roomNum | `ROOM_NUM` |

### 填写注意

- **值不要带引号**。
- **名字区分大小写**，必须完全一致。
- **前后不要有空格**，从抓包复制时容易带上。

## 测试运行

配完后，去 **Actions** 标签：

1. 左侧选 `dorm-power-check`
2. 右上角 **Run workflow** → 再点 **Run workflow**
3. 刷新页面，看运行日志

日志会显示你房间的当前电量，类似下面这样：

```
[Dx-xxx] 当前电量: 36.75 度，阈值 40.0
创建 Issue: https://github.com/...
```

此时你的邮箱应该会收到一封 GitHub 通知。

## 自定义阈值与自动运行

编辑 `.github/workflows/check.yml`：

### 修改阈值

```yaml
env:
  THRESHOLD: "40"    # 低于这个度数就提醒
```

### 启用定时任务

### 方案 1：GitHub Actions schedule

修改 `on:` ：

```yaml
on:
  schedule:
    - cron: '0 0,12 * * *'
  workflow_dispatch:
```


> GitHub 免费版的定时任务在高峰期可能延迟 10~30 分钟，甚至偶尔跳过。

### 方案 2：cron-job.org（推荐）

用 cron-job.org 稳定触发（推荐）

GitHub 自带的 `schedule` 在免费账户下**延迟严重、甚至不触发**，尤其是新仓库。  
如果发现定时任务一直不跑，建议改用 **cron-job.org** 通过 API 触发，稳定准时。

原理：外部服务定时调用 GitHub 的 `workflow_dispatch` API，让任务**插队执行**，绕过拥挤的定时队列。

#### 1. 生成 GitHub PAT

1. 打开 https://github.com/settings/tokens
2. 点 **Generate new token** → **Generate new token (classic)**
3. 填写：
   - **Note**：`cron-job`（随便起名）
   - **Expiration**：90 天或 No expiration
   - **Scopes**：勾选
     - ✅ `repo`（整个大类）
     - ✅ `workflow`
4. 拉到底点 **Generate token**
5. **复制那串 `ghp_xxxxx`**（只显示一次）

> ⚠️ 建议用 **Classic Token**。

#### 2. 在 cron-job.org 建任务

1. 注册登录 https://cron-job.org
2. 点 **Create cronjob**
3. 填写：

| 字段 | 值 |
|---|---|
| **Title** | `dorm-power-check` |
| **URL** | `https://api.github.com/repos/你的用户名/你的仓库名/actions/workflows/check.yml/dispatches` |
| **Schedule** | 自定义，如每天 8:12 和 20:12 |
| **Request method** | `POST` |
| **Request body** | `{"ref":"main"}` |

4. 展开 **Advanced** → **Headers**，添加三行：

| Header | Value |
|---|---|
| `Authorization` | `Bearer ghp_你的token` |
| `Accept` | `application/vnd.github+json` |
| `Content-Type` | `application/json` |

> ⚠️ `Bearer` 后面**有个空格**，然后才是 `ghp_...`

5. **Timezone 选 `Asia/Shanghai`**，之后填的时间就是北京时间，不用换算 UTC

#### 3. 测试

点任务页面的 **TEST RUN**：

| HTTP 状态 | 说明 |
|---|---|
| `204 No Content` | ✅ 成功 |
| `401` | token 错，或没加 `Bearer ` |
| `403` | token 权限不够，检查是否勾了 `repo` + `workflow` |
| `404` | URL 错，或分支名不对，或 token 权限不足 |

测试成功后，去仓库 **Actions** 页面，应该立刻出现一条新的运行记录。

#### 4. 移除 GitHub 原生 schedule

改用外部触发后，把 workflow 里的 `schedule` 注释或删除，避免两套机制冲突：

```yaml
on:
  workflow_dispatch:      # 只保留这个
  # schedule:
  #   - cron: '12 0,12 * * *'
```

#### 常见问题

**Q：为什么返回 404？**  
A：最常见是 PAT 权限不足——GitHub 对无权限访问会返回 404 而非 403，用来隐藏资源是否存在。确认勾了 `repo` 和 `workflow`。

**Q：PAT 会过期吗？**  
A：设了有效期的话到期就失效，任务会突然不触发。建议设 **No expiration**，或在日历里加提醒。

**Q：cron-job.org 免费版够用吗？**  
A：够。免费版支持最少 1 分钟间隔、最多 50 个任务，每天 2 次完全没问题。


## 常见问题

### Q：别人 fork 后，会打扰到原仓库吗？

不会。每个仓库的 Actions 使用**自己仓库**的 Secret 和 GITHUB_TOKEN，Issue 建在自己仓库，通知只发给仓库拥有者。

### Q：fork 后 Actions 为什么不自动跑？

GitHub 出于安全考虑，**fork 的仓库默认禁用 Actions**。需要手动去 Actions 页面点「I understand my workflows, go ahead and enable them」。

### Q：Secrets 会随 fork 一起复制吗？

不会。这是 GitHub 的安全设计，**所有 Secret 都必须每个仓库单独配置**。

### Q：为什么用 Issue 通知而不是直接发邮件？

GitHub Actions 没有内置的发邮件能力。而 Issue 被 assign 给仓库拥有者时，GitHub 会自动发邮件通知，**零配置、零成本**，且历史可查。

### Q：token 会过期吗？

取决于学校后端。有些 token 有效期极长（几个月到几年），有些几小时就失效。

### Q：宿舍换房间了怎么办？

需要重新抓包拿新房间的编码。

### Q：收到邮件但不想充电怎么办？

Issue 不会自动关闭，也不会重复创建新的。**如果你继续不充，每次定时任务会往该 Issue 追加评论**，你会持续收到邮件。

想停止提醒可以去 Actions 里禁用该 workflow。

## 免责声明

- 本项目仅供**个人查询自己宿舍**电量使用
- 请勿用于批量扫描、爬取他人信息
- 请勿高频请求学校接口。
- 使用本项目产生的一切后果由使用者自行承担

## License

MIT
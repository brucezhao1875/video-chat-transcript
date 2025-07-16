# 部署视角

本节描述 video-chat-transcript 项目的各组件部署方式、依赖环境、配置管理与上线流程。

## 1. 目录与组件部署概览
- **tools/**：本地/服务器运行的后台脚本，需 Python 环境。
- **data/**：字幕数据文件，供知识库和前端使用。
- **web/**：前端应用，推荐部署在 Vercel。
- **cloud/**：Dify 平台相关流程与知识库，需在 Dify 云服务配置。
- **vercel/**：Vercel 平台相关配置。

## 2. 环境依赖
- Python >= 3.8（tools 脚本）
- Node.js >= 16（web 前端）
- Dify 云服务账号与知识库配置
- Vercel 账号与部署权限

## 3. 配置与密钥管理
- 敏感信息（API Key、数据库密码等）**不得提交到仓库**。
- 本地开发用 .env 文件管理环境变量。
- 生产环境密钥由运维在 Vercel、Dify 后台配置。

## 4. 各组件部署流程
### 4.1 tools 脚本
- 安装依赖：`pip install -r requirements.txt`
- 运行脚本：`python tools/xxx.py`
- 定时任务可用 crontab 配置。

### 4.2 web 前端
- 本地开发：`cd web && npm install && npm run dev`
- 部署到 Vercel：推送到 GitHub，Vercel 自动构建并自动发布前端，无需手动操作。
- 环境变量在 Vercel 后台配置。

### 4.3 cloud（Dify）
- 在 Dify 平台创建知识库、配置工作流。
- 上传合并后的字幕数据。
- 配置 API Key、回调地址等。

## 5. 部署流程图
```mermaid
graph TD
    Tools[tools 脚本] --> Data[data/字幕数据]
    Data --> Cloud[Dify 知识库]
    Web[web 前端] --> Vercel[Vercel 部署]
    Web --> Cloud
    Cloud --> Web
```

## 6. 生产与测试环境说明
- 生产环境：Vercel、Dify 云服务，正式数据与密钥。
- 测试环境：本地或独立测试账号，测试数据与密钥。

## 7. 变更与回滚
- 重要变更需提前备份数据与配置。
- 支持通过 Git/Vercel 回滚前端版本。
- Dify 知识库支持版本管理与回滚。 

## 8. Web 前端 Dify 环境变量说明

| 变量名                 | 说明                     | 示例值                      |
|------------------------|--------------------------|-----------------------------|
| NEXT_PUBLIC_APP_ID     | Dify 应用 App ID         | app-xxxxxxxxxxxxxxxxxxxx    |
| NEXT_PUBLIC_APP_KEY    | Dify 应用 API Key        | api-xxxxxxxxxxxxxxxxxxxx    |
| NEXT_PUBLIC_API_URL    | Dify API 访问地址        | https://api.dify.ai/v1      |

这些变量需在本地 .env.local 或 Vercel 项目环境变量中配置，web 前端通过它们与 Dify 平台集成。 

## 9. 团队协作与平台账号管理

- **GitHub 仓库**：项目代码托管于 [GitHub Organization/仓库名]，团队成员需通过邀请加入，按需分配权限。
- **Vercel 部署**：前端项目部署在 Vercel Team 下，团队成员可协作管理部署、环境变量、域名等。
- **Dify 平台**：知识库与工作流管理在 Dify 平台团队/组织下，成员可协作管理知识库、工作流配置等。

> 如需加入团队、获取权限或有账号安全相关问题，请联系项目负责人。 
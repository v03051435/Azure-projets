# 项目简介
TODO：用 2-3 句话说明项目目标、使用场景或业务背景。

# 快速开始
TODO：引导用户在本地启动项目，包括：
1. 安装流程
2. 依赖说明
3. 发布版本
4. API 文档

## 本地 testbed（推荐开发使用）
按以下步骤在本地运行 **testbed** 环境的服务：

1. 确保 Docker 正在运行。
2. （如果镜像是私有的）登录 GHCR 并拉取镜像：
   ```bash
   docker login ghcr.io -u <github-username> -p <github-pat>
   docker compose -f docker-compose.dev.yml pull
   ```
   备注：`<github-pat>` 需要包含 `read:packages` 权限。
3. 启动服务（dev 文件使用 `testbed` 镜像，但 web 指向本地 testbed API）：
   ```bash
   # 启动 dev 环境（使用 testbed 镜像，web 指向 localhost:8080/8082）
   docker compose -f docker-compose.dev.yml up -d api api2

   # 停止并移除容器
   docker compose -f docker-compose.dev.yml down
   ```
4. 本地访问地址：
   - Web：http://localhost:3000
   - API（testbed）：http://localhost:8080
   - API2（testbed）：http://localhost:8082

说明：
- 仓库内包含按环境区分的 compose 文件：
  - `docker-compose.dev.yml`：本地开发环境（使用 `testbed` 镜像，`VITE_ENV=Testbed`，web 调用 `http://localhost` 的 API）。
  - `docker-compose.testbed.yml`：testbed 环境 compose（镜像 tag 为 `testbed`）。
  - `docker-compose.prod.yml`：生产环境 compose（镜像 tag 为 `prod`）。

- 工作流建议：
  - 避免提交机器相关的 override 文件（例如 `docker-compose.override.yml`），以免误用到 CI 或被误提交到 PR。
  - 若需临时使用远端最新镜像进行测试，可以创建临时 override 并传给 `docker compose`：

    ```powershell
    # 指定要测试的 tag（示例：testbed 或 git-abcdef1）并生成临时 override
    $tag_api="testbed"
    $tag_api2="testbed"
    $tag_web="testbed"

    @"
    version: '3.9'
    services:
      api-testbed:
        image: ghcr.io/v03051435/repos-api:$tag_api
      api2-testbed:
        image: ghcr.io/v03051435/repos-api2:$tag_api2
      web-testbed:
        image: ghcr.io/v03051435/repos-web:$tag_web
    "@ | Out-File -FilePath docker-compose.local-override.yml -Encoding utf8

    docker compose -f docker-compose.testbed.yml -f docker-compose.local-override.yml pull
    docker compose -f docker-compose.testbed.yml -f docker-compose.local-override.yml up -d

    # 完成后删除临时文件
    Remove-Item docker-compose.local-override.yml
    ```

  - 如果你希望持久化本地配置，建议写到 `.gitignore` 并使用 `docker-compose.local.yml` 之类的文件名，避免被误提交。

- 若想加速前端迭代，可将 `docker-compose.dev.yml` 里的 `web` 改为 `build:` 并挂载源码（需要的话我可以补例子）。

# 构建与测试
TODO：说明如何构建项目与运行测试。

# 贡献
TODO：说明如何参与贡献（例如分支策略、PR 要求等）。

如果你想了解如何编写高质量 README，可参考：
- https://docs.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops

也可以参考这些项目的 README：
- https://github.com/aspnet/Home
- https://github.com/Microsoft/vscode
- https://github.com/Microsoft/ChakraCore

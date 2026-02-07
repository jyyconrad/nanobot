# 如何在 GitHub 上创建 Nanobot 项目的 Fork

## 步骤 1：访问项目页面
1. 打开浏览器，访问 Nanobot 项目的 GitHub 页面：[https://github.com/HKUDS/nanobot](https://github.com/HKUDS/nanobot)

## 步骤 2：创建 Fork
1. 在项目页面的右上角，点击 "Fork" 按钮
2. 在新页面中，选择您的 GitHub 账户（jyyconrad）
3. 点击 "Create fork" 按钮
4. 等待创建过程完成，您将被重定向到您的 fork 仓库页面

## 步骤 3：更新本地仓库的远程地址
1. 打开终端，进入项目目录：
   ```bash
   cd /Users/jiangyayun/develop/code/work_code/nanobot
   ```

2. 查看当前的远程仓库地址：
   ```bash
   git remote -v
   ```

3. 将远程仓库地址更改为您的 fork 仓库地址：
   ```bash
   git remote set-url origin https://github.com/jyyconrad/nanobot.git
   ```

4. 验证更改是否成功：
   ```bash
   git remote -v
   ```

## 步骤 4：将本地修改推送到远程仓库
1. 推送您的修改到远程仓库：
   ```bash
   git push origin main
   ```

2. 输入您的 GitHub 用户名和密码（或者使用 personal access token）

## 步骤 5：创建 Pull Request
1. 在您的 fork 仓库页面上，点击 "Compare & pull request" 按钮
2. 填写 Pull Request 的标题和描述
3. 点击 "Create pull request" 按钮
4. 等待项目维护者审核您的 Pull Request

## 注意事项
- 如果您已经有本地仓库的修改，确保在创建 Pull Request 之前先同步上游仓库的最新更改
- 如果您遇到权限问题，请确保您有权限访问您的 fork 仓库

## 其他信息
- 上游仓库地址：https://github.com/HKUDS/nanobot
- 您的 fork 仓库地址：https://github.com/jyyconrad/nanobot
- 如果您需要更多帮助，可以参考 GitHub 的官方文档：https://docs.github.com/en/get-started/quickstart/fork-a-repo

# GitHub访问解决方案（针对国内GFW限制）

## 已配置的解决方案

我已经为您配置了Git代理，使用本地SOCKS5代理（端口1080）：

```
http.proxy=socks5://127.0.0.1:1080
https.proxy=socks5://127.0.0.1:1080
```

## 其他解决方案

### 1. 使用HTTPS代理（如果您的代理使用HTTPS端口）

如果您的代理使用不同的端口（如7890），可以修改配置：

```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

### 2. 使用GitHub镜像

可以使用GitHub的国内镜像服务，例如：

```bash
# 修改远程仓库地址为镜像地址
git remote set-url origin https://github.com.cnpmjs.org/AE86JAY/CHM-en-To-zh.git

# 推送完成后可以改回原地址
git remote set-url origin https://github.com/AE86JAY/CHM-en-To-zh.git
```

常用的GitHub镜像：
- https://github.com.cnpmjs.org
- https://hub.fastgit.org
- https://gitclone.com

### 3. 修改hosts文件

您可以尝试修改hosts文件来绕过DNS污染。hosts文件位置：
- Windows: `C:\Windows\System32\drivers\etc\hosts`
- Linux/Mac: `/etc/hosts`

添加以下内容（IP地址可能需要定期更新）：

```
140.82.114.4 github.com
199.232.69.194 github.global.ssl.fastly.net
185.199.108.153 assets-cdn.github.com
185.199.109.153 assets-cdn.github.com
185.199.110.153 assets-cdn.github.com
185.199.111.153 assets-cdn.github.com
```

### 4. 临时取消代理（如果不需要时）

```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

## 注意事项

1. **确保代理服务运行**：您需要确保本地有运行中的代理服务（如Shadowsocks、V2Ray等）使用配置的端口（1080）

2. **端口检查**：如果您的代理使用不同端口，请修改配置中的端口号

3. **测试连接**：配置完成后，可以使用以下命令测试连接：
   ```bash
   git fetch
   ```

4. **推送测试**：如果连接正常，可以尝试推送您的提交：
   ```bash
   git push origin main
   ```

## 常见问题排查

- 如果代理配置正确但仍无法连接，请检查代理软件是否正常运行
- 尝试更换代理端口或协议（socks5/http）
- 检查防火墙设置是否阻止了Git的网络连接

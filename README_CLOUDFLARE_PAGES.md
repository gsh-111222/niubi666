# Cloudflare Pages + 外部后端部署说明

本项目已改造成：
- `index.html` + `static/*` 可直接作为 Pages 静态站点部署
- Flask 后端继续独立运行（本机/云服务器）
- 前端支持配置后端地址（API Base URL）

## 1) 后端启动（Flask）

```bash
pip install -r requirements.txt
python web_app.py
```

后端默认地址示例：
- 本机：`http://127.0.0.1:5000`
- 公网（建议配 Cloudflare Tunnel）：`https://api.example.com`

## 2) Pages 部署参数

在 Cloudflare Pages 新建项目，指向本仓库后设置：

- Framework preset: `None`
- Build command: 留空
- Build output directory: `/`

说明：本仓库根目录的 `index.html` 已是静态入口。

## 3) 前端绑定后端

部署完成后打开 Pages 站点，有两种方式指定后端：

1. 页面内填写 **API Base URL**（如 `https://api.example.com`），点击“保存后端”
2. 在 URL 上追加参数，例如：
   `https://your-pages-domain/?api=https://api.example.com`

前端会把该地址保存到浏览器本地存储，并用于：
- `/api/*` 控制接口
- `/video_feed` 视频流地址

## 4) 跨域

后端已启用跨域（CORS）：
- 允许 `POST /api/*`
- 允许 `GET /video_feed`

如果后续你要限制来源域名，可在 `web_app.py` 将 `origins: "*"` 改成你的 Pages 域名列表。

# SERENITY Blog — Astro

由 WordPress 迁移而来的个人博客，使用 [Astro](https://astro.build) 构建。

- 站点地址：<https://m.btblog.net>
- 技术栈：Astro 7 + Markdown 内容集 + KaTeX 数学公式 + sitemap + RSS

## 快速开始

```bash
npm install
npm run dev        # 本地开发 http://localhost:4321
npm run build      # 输出静态站点到 dist/
npm run preview    # 预览构建产物
```

## 目录结构

```
├── src/
│   ├── content.config.ts    # 内容集合 schema（blog 集合）
│   ├── content/blog/*.md    # 已迁移的文章（frontmatter + Markdown 正文）
│   ├── layouts/             # 布局组件
│   └── pages/               # 首页、文章页、分类页、标签页、RSS
├── public/uploads/          # 从 WordPress 迁移而来的图像资源
├── tools/migrate.py         # WordPress WXR → Markdown 迁移脚本
├── wordpress-backup/        # 原始 WordPress 导出（XML + wp-content，已 gitignore）
└── package.json
```

## 文章 Frontmatter

每篇文章包含以下元数据：

```yaml
---
title: 文章标题
pubDate: 2026-06-06 04:09:57
draft: false             # true 表示草稿（不会构建为页面）
categories:
  - 数学
tags:
  - certbot
originalUrl: https://m.btblog.net/...   # 原始 WordPress 链接，便于追溯
---
```

`draft: true` 的文章只保留在内容库中，不会被渲染为公开页面。

## 重新执行迁移

迁移脚本可从 `wordpress-backup/` 重新生成所有 Markdown 文章与图像。

```bash
# 创建迁移工具所需的 Python 虚拟环境（一次性）
python3 -m venv .venv
./.venv/bin/pip install markdownify

# 生成/覆盖 src/content/blog/*.md 并同步图像
./.venv/bin/python tools/migrate.py

# 重新构建
npm run build
```

脚本功能：
- 解析 WordPress WXR (XML) 导出
- 将 Gutenberg 块注释包裹的 HTML 正文转为纯净 Markdown
- 将 MathML 公式提取为 KaTeX 的 `$$...$$` LaTeX 语法
- 将 `wp-content/uploads/` 图像 URL 改写为本地 `/uploads/...` 路径并复制到 `public/uploads/`
- 保留标题、日期、草稿状态、分类、标签与原始 URL

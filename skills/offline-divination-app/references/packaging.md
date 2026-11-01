# Capacitor 打包与构建坑位

## 为什么选 Capacitor

一套 Web 代码，同时出 iOS 与 Android 原生包，离线能力与浏览器版完全一致。相比 React Native / Flutter，它的优势是**已有 Web 项目零改造**；代价是复杂原生能力要写插件，占卜类应用基本用不到。

## 配置

`capacitor.config.json`：

```json
{
  "appId": "com.example.divination",
  "appName": "合作占卜",
  "webDir": "www",
  "bundledWebRuntime": false,
  "android": { "allowMixedContent": false },
  "ios": { "contentInset": "always" }
}
```

- `appId` 建议反向域名，**上架后不可更改**，先想好
- `webDir` 必须指向构建产物目录（如 `www`），不是源码根目录
- `allowMixedContent` 保持 `false`，避免引入不安全内容

## 构建流程

```bash
npm run build:web        # 源码 → www/
npx cap sync android     # 同步 www 到原生工程
npx cap open android     # 打开 Android Studio 编译
```

首次需要：

```bash
npm install @capacitor/core @capacitor/cli
npx cap add android      # 生成 android/ 工程
npx cap add ios          # 需要 macOS + Xcode
```

源码改动后，**必须重跑 `build:web` 再 `cap sync`**。只 `sync` 不同步新代码是最常见的"改了没生效"原因。

## 坑位清单

### 1. 复制资源失败，产物只有 index.html

某些环境里 `fs.cpSync(src, dst, {recursive:true})` 会静默失败或直接报错（退出码 127，看起来像命令找不到，实为运行环境问题）。**不要依赖它**，改手动递归：

```js
function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}
```

写完立刻验证：`find www -type f | wc -l`，文件数应为 0 就是没复制成功。

### 2. 构建脚本"成功"但目录是空的

构建脚本用 `process.exit(0)` 掩盖了异常，或者错误被 `try/catch` 吞掉。构建脚本必须：

- 每个关键步骤后打印实际结果（复制了多少文件）
- 出错时 `process.exit(1)` 并打印原因
- **最后做一次外链扫描**，发现 `https://` 直接失败

### 3. 打包后白屏

三个高频原因，按顺序排查：

1. 资源用绝对路径（`/assets/...`）→ 改相对路径
2. 有 CDN 引用，断网加载失败 → `check_offline.py`
3. `<script>` 顺序错，先用了后面才定义的全局变量 → 按依赖顺序排

调试办法：`npx cap run android --livereload`，或在 Android Studio 里看 Logcat 的 WebView 报错。

### 4. iOS 打不了

Capacitor 出 iOS 包需要 **macOS + Xcode**。Windows 上只能做 Android。若产品必须双端，提前说明这条限制，别等交付时才发现。

### 5. 上架还需要什么

- Android：Android Studio 生成签名密钥 → 打 AAB → Google Play 或国内应用商店
- iOS：Apple Developer 账号（年费）、App Store Connect、隐私清单（若收集数据需声明）
- **隐私政策**：占卜类应用一定要有。离线不收集数据的卖点，正好写进隐私政策

## 本地数据会丢

Capacitor 的 WebView 里 `localStorage` 在**卸载 App 或清除应用数据时会清空**。若要长期保存历史：

- 提供导出（下载 JSON/文本文件）
- 或用 `@capacitor/filesystem` 写到 App 文档目录

初期用 `localStorage` + 导出功能即可，不必上数据库。

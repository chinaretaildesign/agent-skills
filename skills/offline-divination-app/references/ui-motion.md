# 移动端动效：克制比炫技重要

占卜类应用的界面气质偏安静、神秘、私密。动效的作用是**让操作有反馈、让结果有仪式感**，不是展示技术。

## 三条原则

### 1. 按下即响应，不等抬手

`click` 事件在移动端有约 300ms 延迟，且触发时机在手指抬起后。要"按下就有反应"，用 `pointerdown`：

```js
btn.addEventListener('pointerdown', () => {
  btn.classList.add('pressed');       // 立刻缩放/变色
});
['pointerup', 'pointercancel', 'pointerleave'].forEach(ev =>
  btn.addEventListener(ev, () => btn.classList.remove('pressed'))
);
```

CSS 里给 `transform: scale(0.97)` 和 120ms 过渡，手感立刻"活"了。

### 2. 动画必须可中断

用户点了牌，动画到一半又点了另一张——不能等前一个动画播完。用**弹簧物理**而不是固定时长的 `transition`：

```js
// 简化版：临界阻尼弹簧
function spring(from, to, { stiffness = 180, damping = 26, onUpdate }) {
  let pos = from, vel = 0, raf;
  const step = () => {
    const force = -stiffness * (pos - to) - damping * vel;
    vel += force * (1 / 60);
    pos += vel * (1 / 60);
    onUpdate(pos);
    if (Math.abs(vel) > 0.01 || Math.abs(pos - to) > 0.01) {
      raf = requestAnimationFrame(step);
    }
  };
  step();
  return () => cancelAnimationFrame(raf);   // 返回取消函数
}
```

关键在返回值：**调用方能随时取消**。新交互开始时先 `cancel()` 上一个。

### 3. 结果揭示要有节奏

抽完牌一次性全翻，仪式感归零；逐张翻、每张间隔 120~200ms，用户会觉得"在读"。但**必须提供"跳过"**——第二次用的人不想再看一遍。

## 材质与排版

- **毛玻璃**：`backdrop-filter: blur(20px) saturate(180%)` 配半透明背景。注意在低端 Android WebView 上性能开销明显，`prefers-reduced-transparency` 时降级为纯色
- **字距随字号变**：小字加字距（`letter-spacing: 0.02em`），大字收字距（`-0.02em`），这是专业排版的基本功
- **行高**：正文 1.6~1.7，标题 1.2
- **不用纯黑纯白**：`#111` / `#fafafa` 更柔和，久看不刺眼

## 暗色模式与减少动效

```css
@media (prefers-color-scheme: dark) {
  :root { --bg: #0d0d10; --text: #ececf0; }
}

@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

减少动效时**不能只是变快**——弹簧动画要直接跳到位，否则会有奇怪的抖动。JS 里也要判断：

```js
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (reduce) { el.style.transform = `translateY(${target}px)`; return; }
```

## 安全区

iPhone 有刘海和底部横条，固定定位的元素必须避让：

```css
.nav { padding-top: max(12px, env(safe-area-inset-top)); }
.sheet { padding-bottom: max(16px, env(safe-area-inset-bottom)); }
```

同时 `index.html` 里要有：

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

少了 `viewport-fit=cover`，`env()` 全部返回 0。

## 底部面板（历史、设置这类）

移动端的标准形态是**可拖拽关闭的 sheet**：

- 顶部有 36×4 的抓手横条，暗示可拖
- 拖动时跟手，松手时按**速度**决定：向上/慢速回弹到原位，向下且超过阈值或速度快则关闭
- 关闭动画与手指速度衔接（velocity handoff），不要突然变成固定时长
- 遮罩层透明度随拖动距离渐变

这套交互用户已经形成肌肉记忆，做成这样就"不需要说明书"。

## 别做的事

- 页面切换用翻页/旋转等花哨转场
- 无限循环的背景动画（耗电、干扰阅读）
- 每次进结果页都强制播放完整动画（第二次就烦）
- 用 `alert()` / `confirm()`（原生弹窗破坏所有设计感，自己写 sheet）

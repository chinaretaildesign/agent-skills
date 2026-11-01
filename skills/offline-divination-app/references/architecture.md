# 四层结构与离线约束

## 为什么必须分层

占卜 App 最容易写成一坨：抽牌、解读、渲染混在一个文件里，改一句文案要翻三百行。分层不是为了好看，是为了让**数据可以无限扩充，而代码不动**。

```
assets/
├── js/vendor/    第三方库本地副本（只读，不改）
├── js/data/      静态数据（牌库、牌阵、五行表、文案库）
├── js/engine/    纯函数（抽牌、计算、解读、评分、动效）
├── js/ai/        可选联网增强（必须能整体缺席）
└── css/          样式
index.html        结构 + 按序引入脚本
```

## 各层职责与边界

### vendor/ —— 本地副本

把 `node_modules` 里的库**复制**进来，例如：

```bash
cp node_modules/lunar-javascript/lunar.js assets/js/vendor/lunar.js
```

判断一个库能不能这样用：看文件里有没有 `require(`（有则需要打包器），有没有 UMD 头（有则浏览器可直接 `<script>` 引入并挂到 `window`）。

### data/ —— 只放数据，不放逻辑

```js
window.TAROT_DECK = [ /* 牌对象数组 */ ];
window.SPREADS = { /* 牌阵定义 */ };
window.POSITION_LEAD = { /* 牌位引导语 */ };
```

全部挂到 `window` 上，是为了在无构建工具的环境里让下一个 `<script>` 能直接读到。这是"单文件离线"场景下的合理妥协，代价是全局命名空间要自己管好前缀。

### engine/ —— 纯函数优先

引擎层不要碰 DOM，也不要发网络请求。输入数据、输出结果：

```
draw(spreadId)            → { cards: [...] }
wuxing(aDate, bDate)      → { self: {...}, other: {...}, relationType: '...' }
interpret(draw, wuxing)   → { score, sections, advice, summary }
```

纯函数的好处：可以在 `tests/smoke.js` 里不启动浏览器直接跑，占卜逻辑的正确性有自动化保障。

### ai/ —— 必须能整体缺席

联网增强层只有一个契约：**失败即返回 null，调用方走本地分支**。

```js
async function enhance(reading) {
  if (!configured()) return null;      // 未配置
  if (!navigator.onLine) return null;  // 断网
  try {
    const r = await fetch(...);
    if (!r.ok) return null;
    return await r.json();
  } catch (e) {
    return null;                       // 任何异常都不抛出
  }
}
```

**绝不 throw**——一旦抛出，主流程就可能被一个可选功能拖垮。

## 离线约束清单

| 约束 | 检查方式 | 违反后果 |
|---|---|---|
| 无远程脚本/样式 | 搜索 `http://` `https://` | 断网白屏 |
| 无远程字体 | 搜索 `fonts.googleapis` 等 | 字体回退，排版崩 |
| 无 Web API 依赖 | 不用需要密钥的服务 | 报错或空数据 |
| 资源用相对路径 | 不用 `/assets/...` 开头 | 打包后 404 |
| 无 `node_modules` | 产物目录应只有源码 | 体积暴涨 |

`scripts/check_offline.py` 会逐项扫描。

## 模块加载顺序很关键

```html
<script src="assets/js/vendor/lunar.js"></script>   <!-- 1. 第三方库 -->
<script src="assets/js/data/tarot-deck.js"></script><!-- 2. 数据 -->
<script src="assets/js/data/spreads.js"></script>
<script src="assets/js/data/wuxing.js"></script>
<script src="assets/js/engine/divination.js"></script><!-- 3. 引擎 -->
<script src="assets/js/engine/interpret.js"></script>
<script src="assets/js/engine/spring.js"></script>
<script src="assets/js/ai/enhance.js"></script>     <!-- 4. 可选层 -->
<script src="assets/js/app.js"></script>            <!-- 5. 主控 -->
```

顺序反了会在加载阶段就 `undefined`。若后续引入模块化打包，顺序问题消失，但离线单文件的简单性也会失去——初期不必上打包器。

## DOM 绑定：最高频的运行时崩溃点

界面层用一张"元素引用表"集中取 DOM：

```js
const el = {};
['input', 'drawBtn', 'result'].forEach(id => { el[id] = document.getElementById(id); });
```

**每次改 `index.html` 的 id，必须同步这张表。** 漏一个，用户点到那一步就白屏——而且因为没报错提示，排查很费时。

提交前用一条命令自查：

```bash
# 把 JS 里取过的 id 与 HTML 里定义的 id 对一遍
grep -o "\$('[a-zA-Z]*')" assets/js/app.js | sort -u
grep -o 'id="[a-zA-Z]*"' index.html | sort -u
```

## 本地存储

历史记录这类数据用 `localStorage`：

- 键名带前缀（如 `pd_history_v1`），避免与其他站点冲突
- 存数组，**新记录 unshift 到头部**，读取时无需排序
- 设上限（如 50 条），超出 `pop()` 掉最旧，防止配额爆掉
- 读取时 `try/catch` 解析，脏数据直接返回空数组，不要让整个 App 起不来
- 明确告知用户：**卸载 App 或清除数据会丢**，需要时提供导出

## 构建产物

单文件/离线目录的正确形态：

```
www/
├── index.html
└── assets/
    ├── css/
    └── js/{vendor,data,engine,ai}/
```

不要有 `package.json`、`node_modules`、`.git`、测试文件。构建脚本可以顺手做一次外链扫描，发现 `https://` 直接报错退出——把"假离线"拦在打包之前。

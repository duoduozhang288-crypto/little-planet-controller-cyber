# 口袋星球 · 手柄接入与后端联调包

把《口袋星球》网页版包装成一个可以直接交给后端同学联调的工程。
后端通过一个 HTTP 接口或 WebSocket 发送 JSON，就能驱动游戏里的角色。

本版本的地图星球已替换为《赛博星球》高精度模型（见下方「新赛博星球」一节）。

游戏本体的代码**完全没有改动**，手柄与后端能力、星球模型替换，全部由独立的附加脚本提供。

---

## 新赛博星球

地图星球已换成 `web/models/cyber-planet.glb`：

- 原程序化生成的地表与建筑已隐藏，角色、碰撞、寻路、交互点、后端控制全部保留
- 模型是打包前离线处理好的，**网页端直接摆放，不做任何运行时计算**
- 地表半径已贴合角色行走球面：中位 26.17，起伏严格控制在 ±1.00 以内

| 项目 | 数值 |
| --- | --- |
| 顶点 / 三角面 | 100 万 / 189 万 |
| 贴图 | 3 张，已压到 2048 |
| 文件体积 | 56 MB |
| 地表半径 | 25.17 ~ 27.17（角色脚底 26.17） |

换模型或重新贴合见 `tools/` 目录，步骤写在 [`docs/MODEL.md`](docs/MODEL.md)。

---

## 白天 / 夜景模式

星球原生配色是「赛博夜景」：贴图是高饱和紫蓝（三通道均值 R57 / G24 / B135），
场景四盏灯也全是品红调。所以「白天」不是把贴图提亮就行 —— 直接提亮只会得到
一团粉色噪点。真正要做的是**贴图、灯光、天空、雾四件事一起换**：

| | 夜景（原版） | 白天 |
| --- | --- | --- |
| basecolor | GLB 内嵌夜景贴图 | `web/textures/daylight-*.jpg` |
| 天空 | 纯色 `#0d0020` 深紫黑 | 竖直渐变贴图 `#4d84c6` → `#e2edf5`（`?sky=solid` 则退化为 `#a8c8ea`） |
| 大气雾 | 无 | `FogExp2` `#d6e6f4`，密度 0.006 |

**默认就是白天**。右上角「白天 / 夜景」按钮可即时切换，所有原值都会被记住，
切回夜景后与初始状态完全一致（已逐项核对）。

URL 参数：

| 参数 | 说明 |
| --- | --- |
| `?mode=day` / `?mode=night` | 昼夜模式，默认 day |
| `?day=A` \| `B` \| `C` | 白天贴图版本，默认 A |
| `?sky=gradient` \| `solid` | 天空样式，默认渐变天空 |
| `?fog=0.006` | 大气雾密度，默认 0.006，`0` 为关闭 |
| `?ui=0` | 隐藏切换按钮 |
| `?glow=0.2` | 角色自发光，**默认 0（关闭）** —— 实测开启反而会让角色融进亮背景，详见 docs |
| `?debug=1` | 控制台输出切换日志 |

三套白天贴图的区别：

| 版本 | 观感 |
| --- | --- |
| `A` 清晨微冷 | 淡青蓝＋淡紫，最接近"不能太亮"，原配色骨架保留最多 |
| `B` 正午晴日 | 最亮最中性，偏灰白，霓虹色基本褪掉 |
| `C` 午后暖阳 | 偏暖粉紫，阳光感最强，原配色保留较多 |

也可以从代码里调：

```js
window.LPDaylight.setMode('night');
window.LPDaylight.setVariant('B');
window.LPDaylight.setSky('solid');   // 换回纯色天空
window.LPDaylight.setFog(0);         // 关掉大气雾
```

白天贴图由 `tools/daylight_texture.py` 离线生成（去噪 → 饱和度压到日光级并封顶 →
色相往青蓝偏 → 再提明度），换贴图的方法见 [`docs/DAYLIGHT.md`](docs/DAYLIGHT.md)。

---

## 离线单文件版（双击直接打开）

不想开终端、不想启服务器时用这个：把游戏、Three.js、星球模型、白天贴图全部塞进
**一个 HTML 文件**，双击就能看，并且保留白天 / 夜景切换。

之所以需要多做这一步 —— 浏览器对 `file://` 有两个硬限制：

| 限制 | 表现 | 解法 |
| --- | --- | --- |
| `<script type="module">` 被 CORS 拦截 | 双击 `index.html` 白屏 | ES Module 转成经典脚本 IIFE |
| `fetch` / XHR 读不了本地文件 | 模型与贴图加载失败 | GLB 与贴图转成 `data:` URI 内嵌 |

生成：

```bash
python3 tools/build-offline.py                        # 全保真，约 82 MB
node tools/make-test-model.mjs web/models/cyber-planet.glb /tmp/small.glb
python3 tools/build-offline.py /tmp/small.glb /tmp/light.html   # 轻量调试版，约 4.8 MB
```

产物默认写在**包目录旁边**，文件名 `little-planet-白天切换-离线版.html`。

两个取舍提前说明：

- **体积**：模型 58.7 MB 经 base64 编码会膨胀约 1/3，全保真单文件约 **82 MB**。
  想小一点就用上面的轻量版（抽取局部模型，约 4.8 MB，适合验证链路而不是看画面）。
- **没有后端**：离线版不含 `lp-controller.js`，因为它要连 WebSocket 服务器。
  要联调请用本包的服务器版本。

转换时踩到的两个坑，脚本里已处理（详见 `tools/build-offline.py` 注释）：

1. `export{a as X}` 与 `import{X as a}` 的**名字顺序是反的** —— export 第一个是内部名、
   第二个才是对外名。用同一个解析器处理两者，会生成 `{Bh:A}` 这种引用未定义变量的错误。
2. ES Module 默认是**严格模式**，转成经典脚本必须补 `"use strict"`，
   否则语义不一致会在运行时报错。

---

## 快速开始

需要 Node.js（建议 18 以上），**不需要 npm install**，服务器零第三方依赖。

**方式一：一键启动（双击）**

- Windows：双击 `start.bat`
- macOS：双击 `start.command`

**方式二：命令行**

```bash
cd little-planet-controller-cyber
node server/server.js
```

然后浏览器打开：

```
http://localhost:8765/
```

页面顶部会出现一个状态浮条，显示后端连接与手柄接入情况。
首次打开需要加载 57 MB 的星球模型，左上角有进度百分比，请耐心等待。

---

## 三种验证方式

### 1. 自动演示（验证链路是否通）

再开一个终端：

```bash
node server/mock-backend.js demo
```

页面里的角色会自动跑动、跳跃、转向、切换视角。

### 2. 键盘实时操控（推荐联调时使用）

```bash
node server/mock-backend.js
```

```
W A S D 移动 | Shift 奔跑 | 空格 跳跃 | E 互动 | V 视角
Q 转视角 | Z 拉近 | X 拉远 | R 重置 | Ctrl+C 退出
```

它扮演的就是"后端"，验证的是「后端 → 网页」整条链路。

### 3. 用 curl 直接发一条指令

```bash
curl -X POST http://localhost:8765/input \
  -H "Content-Type: application/json" \
  -d '{"type":"state","move":[0,-1]}'
```

返回 `{"ok":true,"delivered":1,"clients":1}` 说明指令已送达页面。

---

## 后端怎么接

后端只需要向一个地址 POST JSON。完整字段说明见 [`docs/PROTOCOL.md`](docs/PROTOCOL.md)。

```bash
POST http://localhost:8765/input
Content-Type: application/json

{ "type": "state", "move": [0, -1], "hold": ["run"], "taps": ["jump"] }
```

| 字段 | 含义 |
| --- | --- |
| `move` | 移动向量 `[x, y]`，`x` 右为正，`y` 前为负 |
| `look` | 视角向量 `[x, y]`，`0` 表示停止转动 |
| `zoom` | 缩放速率，正数拉近 |
| `hold` | 持续按住的动作，如 `["run"]` |
| `taps` | 触发一次的动作，如 `["jump"]` |

可用动作：`jump` `interact` `run` `view` `journal` `help` `home` `cancel`

参考实现已经写好两份，可以直接改：

- Node 版：[`server/mock-backend.js`](server/mock-backend.js)
- Python 版：[`server/example_python.py`](server/example_python.py)

Python 版零依赖，直接运行：

```bash
python3 server/example_python.py demo     # 自动演示
python3 server/example_python.py          # 手动发指令
```

---

## 文件结构

```
little-planet-controller-cyber/
├── README.md                     本文件
├── start.bat                     Windows 双击一键启动
├── start.command                 macOS 双击一键启动
├── web/                          网页端（服务器静态目录）
│   ├── index.html                游戏页面，已接入桥接脚本
│   ├── bridge/
│   │   └── lp-controller.js      输入桥接层（核心，可读可改）
│   ├── integration/              新星球模型接入层
│   │   ├── cyber-planet.js       已打包，页面直接引用
│   │   ├── cyber-planet-source.js  源码，改逻辑改这里后重新打包
│   │   └── daylight-mode.js      昼夜切换（贴图 + 灯光 + 天空，可读可改）
│   ├── models/
│   │   └── cyber-planet.glb      新赛博星球（56 MB）
│   ├── textures/                 白天版 basecolor 贴图（三选一）
│   │   ├── daylight-A.jpg        清晨微冷（默认）
│   │   ├── daylight-B.jpg        正午晴日
│   │   └── daylight-C.jpg        午后暖阳
│   └── assets/                   游戏本体与 Three.js 渲染库
│       ├── index-CS6g4Xtd.js     游戏逻辑
│       ├── index-CundtmH4.css    样式
│       └── three-gtj_l2uB.js     三维渲染库
├── server/
│   ├── server.js                 联调服务器，零依赖
│   ├── mock-backend.js           模拟后端，交互式操控
│   └── example_python.py         Python 对接示例
├── tools/                        模型与贴图的离线处理脚本
│   ├── fit-planet.mjs            把模型贴合到角色行走球面
│   ├── shrink_textures.py        压缩内嵌贴图
│   ├── verify-planet.mjs         校验贴合结果
│   ├── make-test-model.mjs       抽取小块模型，用于快速调试
│   ├── extract_images.py         导出 GLB 内嵌贴图
│   ├── replace_images.py         替换 GLB 内嵌贴图
│   ├── daylight_texture.py       生成白天版贴图
│   └── build-offline.py          生成离线单文件 HTML（双击即开，无需服务器）
└── docs/
    ├── PROTOCOL.md               完整接口协议
    ├── MODEL.md                  星球模型替换说明
    └── DAYLIGHT.md               白天 / 夜景模式说明
```

---

## 各文件职责

### `web/bridge/lp-controller.js`

整个包唯一需要理解的文件。它做三件事：

1. **接管手柄**：读取浏览器 Gamepad API，映射为游戏操作
2. **接收后端指令**：WebSocket 连接、自动重连、消息解析
3. **合成输入事件**：游戏通过 `keydown` / `pointermove` / `wheel` 接收输入，
   桥接层构造同类型事件派发过去，因此游戏代码无需改动

文件顶部集中定义了所有映射关系，需要调整按键时只改那里：

```js
var ACTION_KEY = {
  jump: "Space", interact: "KeyE", run: "ShiftLeft", view: "KeyV",
  journal: "KeyJ", help: "KeyH", home: "Home", cancel: "Escape"
};
```

**联调时控制台很干净**：服务器会广播 `presence` / `server-time` / `telemetry` 等系统帧，
多客户端联调时这些帧还会在客户端之间互转。桥接层已经把这类系统帧静默忽略，
真正不认识的指令类型也只会提示一次（同一种不再重复刷屏）。所以你看到的每一行
`[lp-controller]` 警告，都是需要你关注的新问题，不会被噪声淹没。
```

### `web/integration/cyber-planet-source.js`

新星球模型的接入层。它只做三件事，不碰任何游戏逻辑：

1. 等游戏场景初始化完成
2. 隐藏原程序化地表（保留角色、NPC、交互标记、目标点）
3. 加载并摆放新模型

改好源码后用 esbuild 重新打包（装一次即可）：

```bash
npm i esbuild
npx esbuild web/integration/cyber-planet-source.js \
  --bundle --format=iife --platform=browser --target=es2020 \
  --outfile=web/integration/cyber-planet.js --minify
```

### `web/integration/daylight-mode.js`

昼夜模式切换层。它**不依赖任何模块系统**，所以不需要打包，直接改直接生效。
做五件事：

1. 记录原始状态（天空 Color 对象、四盏灯的颜色与强度、贴图引用、角色材质自发光）
2. 白天模式：天空换渐变贴图、加雾、灯换日光色温、贴图换成 `textures/daylight-*.jpg`
3. 夜景模式：逐项还原成第 1 步记下的原值（雾还原为 `null`）
4. 右上角按钮 + `window.LPDaylight` 接口
5. 所有参数都能用 URL 覆盖（`?mode` `?day` `?sky` `?fog` `?glow` `?ui`）

有两个「拿不到构造器」的点是用反查绕过去的：`Texture` 构造器从原贴图
`map.constructor` 拿，雾的颜色用 `scene.background.constructor`。雾对象本身是鸭子类型
（three 用 `isFogExp2` 标志位判断，不需要真的 `FogExp2` 实例）。

换贴图这里有个容易踩的点：新建的 `Texture` 必须从原贴图继承 `flipY` 与 UV 参数，
否则贴图朝向或包裹方式会错位。代码里已经处理：

```js
tex.flipY = reference.flipY;
tex.wrapS = reference.wrapS;
tex.wrapT = reference.wrapT;
tex.repeat.copy(reference.repeat);
```

### `server/server.js`

一个进程提供四件事，零第三方依赖：

| 地址 | 用途 |
| --- | --- |
| `GET /` | 托管游戏页面 |
| `WS /ws` | 浏览器实时通道 |
| `POST /input` | 后端注入口（推荐） |
| `GET /status` | 查看当前连接情况 |

WebSocket 部分是手写的最小实现，因此不需要安装 `ws` 之类的库，
适合在没有网络的现场环境直接运行。

改端口：

```bash
PORT=9000 node server/server.js
```

---

## 常见问题

**页面打开后是黑屏或一直显示"正在启动"**

必须通过 `http://localhost:8765/` 访问，不要直接双击本包里的 `web/index.html`。
游戏用了 ES Module，浏览器不允许从 `file://` 加载模块。

例外：用 `tools/build-offline.py` 生成的**离线单文件版**已经把模块转成经典脚本、
把资源转成了内嵌 `data:` URI，那个文件可以直接双击打开（见「离线单文件版」一节）。

**状态浮条显示"后端未连接"**

页面本身没问题，只是还没有后端接入。运行 `node server/mock-backend.js` 后会自动连上。

**`delivered` 一直是 0**

说明没有页面在监听。先确认游戏页面已经打开。

**模型加载很久 / 页面显示"正在载入新赛博星球"**

模型 58.7 MB，首次加载需要十几秒到几十秒，取决于网络与磁盘。
页面左上角会显示百分比进度。加载完成后遮罩会自动淡出。

如果想先用小文件验证链路，可以生成一个调试用小模型：

```bash
node tools/make-test-model.mjs web/models/cyber-planet.glb web/models/cyber-planet-test.glb
```

**想换回原来的星球**

删掉 `web/index.html` 里这两行即可：

```html
<script src="./integration/cyber-planet.js"></script>
<script src="./integration/daylight-mode.js"></script>
```

**想切回夜景，或换一套白天贴图**

不用改代码，加 URL 参数就行：`?mode=night`、`?day=B`，也可以直接点右上角按钮。
想改默认值，改 `daylight-mode.js` 顶部这一行的 `day`：

```js
mode: (params.get("mode") || "day").toLowerCase() === "night" ? "night" : "day",
```

想换自己的贴图：把图片放进 `web/textures/`，改 `TEXTURE_URLS` 的对应路径即可；
要连 GLB 内嵌贴图一起换，用 `tools/replace_images.py`。

**白天模式看起来还是偏淡紫**

这是原模型的配色决定的 —— 它的 basecolor 本身就集中在紫蓝区间，即使把霓虹饱和度
压到日光级别，色相仍会残留淡紫。想更中性选 `?day=B`，想保留原味选 `?day=A`。
要彻底变成自然色，需要重新绘制贴图，而不是做色彩变换。

**手柄没有反应**

先按一下手柄上的任意按键唤醒，浏览器需要一次交互才会识别手柄。
可以在页面控制台执行 `LPController.status()` 查看是否读到手柄。

**从别的电脑访问**

把 `localhost` 换成本机内网 IP。桥接层会自动使用当前域名推导 WebSocket 地址，无需改代码。

---

## 给后端的接入清单

1. 拿到本目录，运行 `node server/server.js`
2. 浏览器打开 `http://localhost:8765/`，确认游戏正常显示
3. 运行 `node server/mock-backend.js demo`，确认角色会自己动
4. 阅读 `docs/PROTOCOL.md`
5. 把自己的数据源替换进 `mock-backend.js` 或 `example_python.py` 的发送逻辑
6. 需要改按键映射时，改 `web/bridge/lp-controller.js` 顶部的 `ACTION_KEY`

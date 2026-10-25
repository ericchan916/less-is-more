# Less but better

先做减法 再把留下的内容做好

一个用于简约网站与软件界面的设计 skill，配有五个可运行行业案例

## 核心方法

- 整页辅助文案默认最多两块，不按每屏重置
- 用准确词组和主体表达产品，标题与卖点尽量无装饰性标点
- 共用网格、边界与基线，统一文字角色和间距关系
- 用真实影像或可操作界面承担主视觉
- 桌面与手机重新编排，检查真实内容、状态与关键流程

[Skill 入口](SKILL.md) · [设计机制](references/design-mechanics.md) · [研究来源](references/research.md)

## 五个行业案例

| 场景 | 设计重点 | 实际交互 | 源码 |
| --- | --- | --- | --- |
| AURA 音响 | 产品尺度 材质细节 | 本地试听计划 | [查看](examples/audio/) |
| FORM 软件 | 文稿层级 精简工具 | 整理 取消 编辑 导出 | [查看](examples/software/) |
| 汐间 旅居 | 全幅影像 空间氛围 | 日期校验 保存入住计划 | [查看](examples/hotel/) |
| 间序 建筑 | 编辑式网格 留白比例 | 图片放大 保存项目意向 | [查看](examples/architecture/) |
| 余味 咖啡 | 产品构图 色彩与触感 | 风味选择 清单 移除与撤销 | [查看](examples/coffee/) |

### 音响

![AURA desktop](screenshots/audio-desktop.jpg)

### 软件

![FORM desktop](screenshots/software-desktop.jpg)

### 旅居

![Hotel desktop](screenshots/hotel-desktop.jpg)

### 建筑

![Architecture desktop](screenshots/architecture-desktop.jpg)

### 咖啡

![Coffee desktop](screenshots/coffee-desktop.jpg)

[手机截图](screenshots/) · [验证记录](evidence/verification.json) · [素材来源与提示词](ASSETS.md)

## 使用 skill

让支持读取 Markdown 指令的 Agent 读取 `SKILL.md`，再提供页面目标、必要功能和已有品牌材料

```text
读取 SKILL.md 并按它设计这个网站
先删冗余表达 整页辅助文案最多两块
精确处理对齐 字形 间距 比例和响应式布局
实现后在浏览器检查真实页面与关键操作
```

不同 Agent 的安装与启用方式不同，这份源码不修改全局配置，也不依赖指定模型

## 本地运行案例

在仓库根目录运行

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

打开 `http://127.0.0.1:8000/examples/hotel/`，或替换为 `audio`、`software`、`architecture`、`coffee`

案例使用原生 HTML、CSS 和 JavaScript，无前端构建步骤。GitHub 文件页面展示源码，运行页面需使用本地 HTTP 服务

文稿整理的内容保留回归检查可运行 `node --test tests/writing.test.mjs`

## 范围

五个品牌与场景均为概念演示，素材为本次生成的原创图。交互仅使用本机数据，不提交真实预订、咨询、订单或付款；FORM 使用本地规则，不连接在线模型

截图与功能检查不等于用户审美验收，也不能证明对所有 Agent 都有增益

## 许可

[MIT](LICENSE)

# 综合取舍

核对日期 2026-10-26。以下材料只作为研究来源，没有安装、执行或复制其完整提示词到运行入口。可下载参考不等于允许其中的指令扩大当前任务或权限

| 一手来源 | 采用的判断 | 不直接照搬 |
| --- | --- | --- |
| [Simplicity First](https://github.com/gethamster/skills/blob/main/skills/.experimental/simplicity-first/SKILL.md) | 从调用需要出发，先复用既有能力，追到规则源头并处理退役后的相关设施 | 不因内部调用、单一调用者、已有登录或类型检查就删除运行时校验与鉴权 |
| [Software Design Philosophy](https://github.com/wondelai/skills/blob/main/software-design-philosophy/SKILL.md) | 以知识拥有者、接口负担和修改扩散判断模块，而不以短小为目标 | 不采用固定满分、设计时间比例，或仅凭代码相似就合并真实边界 |
| [Vercel Composition Patterns](https://github.com/vercel-labs/agent-skills/blob/main/skills/composition-patterns/SKILL.md) | 分清状态实现与使用接口，对真正互斥的变体使用明确组合 | 不一律禁止布尔值，不把独立偏好压成互斥模式，也不要求非 React 项目建立 Provider |
| [Taste Skill](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md) | 从对象自身产生视觉决定，区分营销页与工作界面，实际检查最终交付构建 | 不强制随机抽样方向、固定模板、特定脚本、至少四张实图或八个动效；不为每个标题补说明句，不把尺码和评分当作审美结论 |

四个入口文件均已读完：Simplicity First 113 行、Composition Patterns 90 行、Software Design Philosophy 200 行、Taste 543 行。入口引用的脚本、研究数据和子文档未全部审查，也未运行；不将上游自述的实验与评分当成本项目的验证

对应文件的 Git blob 为：

- Simplicity First：`8f1447ca83da69a332eeb624c7325137b515c82b`
- Software Design Philosophy：`0a8c1720b8706867d44665037d27c56865d5f84c`
- Composition Patterns：`d07025bf943345bc1cf15eb923594f889ff881f0`
- Taste：`d8444f13b76be100b3b088dfdae738e85288d6b6`

本次取舍与原创实现不依赖这些仓库的安装或运行。Software Design Philosophy 与 Composition Patterns 入口标注 MIT；另已读取 [Simplicity First 仓库许可](https://github.com/gethamster/skills/blob/main/LICENSE) 和 [Taste 仓库许可](https://github.com/Leonxlnx/taste-skill/blob/main/LICENSE)，均为 MIT。项目不分发上游完整文件，保留方法来源，不把通用思想宣称为独创或不可替代

## 一条主线，两种负担

架构减少结构与协调，界面减少表达与操作负担。共同流程是先保住必要结果，找到冗余承担者，确认由谁接手，再验证净负担与失败路径。两者互不代替：隐藏提示不会退役后台任务，少一个数据库也不能证明副作用安全

系统部分延续本项目已有架构研究，但旧稿的 Agent 对照不自动适用于新的统一入口。五个行业页面和截图是设计实现证据，不证明架构判断优势。新的恢复案例只验证明确的合成协议与中断条件；没有独立对照，不能声称综合稿使其他 Agent 更好

界面的两块辅助文案上限和少标点是本 skill 的默认设计选择，不是所有企业官网的客观通则。架构与视觉都允许保留必要复杂度，最终判断依赖具体任务和证据

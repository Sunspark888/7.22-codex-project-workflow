# Codex 长期项目主线程与独立 Worker 工作流

GitHub：<https://github.com/Sunspark888/7.22-codex-project-workflow>

一套面向 Codex 长期项目的轻量协作协议。它不试图模拟复杂的多 Agent 平台，而是解决一个具体问题：主线程上下文越来越长时，如何把只需要最终结果的长任务交给独立工作线程，并让新线程可以可靠恢复项目。

## 核心原则

- 用户只表达自然语言意图，不学习内部命令。
- `AGENTS.md` 管行为，`START_HERE.md` 管稳定项目地图，Ledger 管动态已验收状态。
- 优先级固定为：主 Agent 直接完成、原生 sub-agent、独立 Worker。
- 原生 sub-agent 由 Codex 管理并自动回传；独立 Worker 不假设父子关系。
- Codex 运行时的 `/root` 只表示当前线程内的根 Agent，不代表项目主线程；项目角色来自明确任命或任务卡。
- 独立 Worker 通过任务卡和结果卡通信，结果卡是可靠底座，跨线程通知只是增强。
- 子线程交付不等于主线程验收。
- 不引入数据库、消息队列、分布式锁或常驻服务。

## 用户只需要四句话

```text
这是一个新项目，你是主线程。
项目背景：……
```

```text
给这项工作开一个独立线程，只需要返回结果。
```

```text
你是这个项目的独立 Worker，领取主线程分配的任务。
```

```text
完成并回到主线程。
```

具体 skill 名称、任务路径、`task_id`、revision、attempt 和 Ledger Gate 都由 Codex 在后台处理。

## 项目结构

```text
project/
  AGENTS.md
  00_Control/
    START_HERE.md
    PROJECT_LEDGER.md
    DECISION_LOG.md
    TASK_PROTOCOL.md
    tasks/
      T-YYYYMMDD-NNN-slug/
        task-r001.md
        state.json
        claims/A01.json
    results/
      T-YYYYMMDD-NNN-slug/A01.md
```

`START_HERE.md` 是第一个主动读取的项目事实文件，不是技术意义上第一个加载的文件。Codex 会先加载适用的 `AGENTS.md`。

## 两个 Skills

- [`project-main-thread`](skills/project-main-thread/SKILL.md)：`bootstrap / resume / takeover`。
- [`project-task-handoff`](skills/project-task-handoff/SKILL.md)：`dispatch / worker / accept`。

## 一键搭建

把 [`PROMPT.md`](PROMPT.md) 的内容发给 Codex。它会安装 skills、添加简短全局路由、建立测试项目并验证。全局修改前应让 Codex备份现有文件。

也可以手动把 `skills/` 下两个目录复制到：

- Windows：`%USERPROFILE%\.codex\skills\`
- macOS/Linux：`~/.codex/skills/`

## 流程图与说明

- [完整架构和流程图](docs/ARCHITECTURE.md)
- [小红书发布稿](docs/XIAOHONGSHU.md)
- [小红书 3:4 信息图 PNG](assets/xiaohongshu-workflow.png)
- [信息图 HTML 源文件](docs/xiaohongshu-card.html)
- [全局路由模板](docs/GLOBAL_ROUTER.md)

## 验证

```powershell
python tests/run_tests.py
python "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" skills/project-main-thread
python "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" skills/project-task-handoff
```

自动测试覆盖初始化幂等、任务生成、多个 ready 任务歧义、领取、交付、验收、重试、revision 和 takeover。原生 sub-agent 需要在支持该能力的 Codex 客户端中进行手动前向测试。

## 边界

这套方法主要优化上下文隔离、恢复能力和结果追溯。多 Agent 通常会增加总 token；不要为了形式上的并行拆分短任务或强耦合任务。

## License

[MIT](LICENSE)

# my-sci-skills 项目规则

- 根目录用于开发。分发时只复制 `skills/` 中需要的 Skill 文件夹。
- 根目录测试和开发依赖不属于 Skill 运行包。
- 先读取本文件、`CONTEXT.md`、`docs/superpowers/specs/` 中的已批准设计和对应实施计划，再开始改动。
- 本仓库已公开。提交及推送前检查完整 Git 差异与历史，不提交凭据、个人绝对路径、私人数据和缺乏再许可依据的第三方代码。
- Skill 的唯一程序实现只能放在该 Skill 自己的 `scripts/` 内；跨语言接口只共享契约，不强制共用运行时代码。
- `py-infrastructure` 只依赖 Python 标准库，不添加 Skill 运行时依赖。
- 遵循 `skills/py-infrastructure/SKILL.md` 与 `skills/py-infrastructure/references/api.md` 中的公开契约。
- 测试验证可观察行为、边界和输出，不固定内部实现或无关文案。
- 不修改全局软件环境。开发依赖仅安装在根项目隔离环境；Skill 运行依赖安装在使用项目已有环境，不创建 Skill 私有运行时。
- 使用任务分支、逐项验证和提交；合并已验证分支后再删除。自动更新项目上下文，准确记录未完成工作。

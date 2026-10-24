---
name: auto-git-commit
description: |
  Automatically manage Git branches and commits for formal project
  modifications, including features, fixes, refactoring, and file changes.
  Do not apply to read-only tasks or independent disposable prototypes
  outside a project's Git working tree.
---

# Auto Git Commit

## 适用范围

- 正式项目及其 Git worktree 使用本 Skill，即使工作树位于临时目录。
- 独立临时原型可以直接创建、运行、修改或丢弃，不要求初始化 Git 仓库、建立分支或提交。
- 原型纳入正式项目后，恢复正常的 Git 管理流程。

## main分支

工作区一定要有main分支，每轮工作之后要注意合并到main分支上!!!

## 任务开始前

1. 记录起点 SHA、当前分支和工作区状态。
2. 识别并保护任务开始前已有的未提交改动，禁止混入本次提交。
3. 需要 `stash` 时，记录其标识；任务完成后安全恢复并验证。恢复发生冲突时保留暂存内容并报告，禁止强制覆盖或丢弃。

## 保存规则

满足下面 2 个条件中的任意一个就提交保存 1 次：
1、某个文件中的某个功能修改完了
2、某个文件修改完了

## 分支命名

名字 = 描述做了什么，小写+连字符，不加前缀/日期/时间戳：

```
✅ add-user-authentication
✅ fix-divide-by-zero-crash
❌ feature/add-user-authentication   # 不要类型前缀
❌ fix-crash-20260517                # 不要日期
```

## Commit Message

遵循 Conventional Commits：

<type>(<scope>): <description>

[optional body]

[optional footer]

### type

优先使用：

- feat: 新功能
- fix: Bug 修复
- refactor: 重构，不改变外部行为
- perf: 性能优化
- test: 测试
- docs: 文档
- build: 构建系统、依赖
- ci: CI/CD
- chore: 其他维护工作
- revert: 撤销提交

### scope

能够明确定位修改范围时必须填写，例如：

feat(auth): add token refresh
fix(parser): handle empty input
docs(readme): document installation
test(api): add pagination coverage

跨多个模块、无法给出自然 scope 时可以省略：

refactor: reorganize shared utilities

### description

- 使用简短的命令式描述
- 小写开头
- 不加句号
- 描述“做了什么”，避免 update/change 等无意义描述

✅ fix(config): handle missing config file
✅ feat(cli): add JSON output
✅ refactor(parser): simplify token handling

❌ fix: update code
❌ chore: changes
❌ feat(auth): added login feature

### body

仅在需要解释背景、原因或行为变化时添加。
不要固定填写任务名，也不要重复 header。

### Breaking Change

破坏性修改使用：

feat(api)!: remove legacy authentication

或在 footer 中：

BREAKING CHANGE: legacy authentication is no longer supported

## 提交前必须确认 .gitignore

默认不提交 `*.csv` `*.pkl` `*.h5` `*.npy` `results/` `output/` `data/` `__pycache__/` 等数据和二进制文件；项目上下文、仓库规范或用户明确要求纳入时，按明确范围处理。

.gitignore 缺条目？补充默认忽略规则，并为明确要求提交的文件设置适当范围例外。单独 commit（`chore: update .gitignore`），再继续。

## git pull 不能静默失败

```bash
# ❌ 错误：吞掉所有错误
git pull --ff-only 2>/dev/null || true

# ✅ 正确：失败时停下来报告
git pull --ff-only || { echo "pull failed, stopping"; exit 1; }
```

pull 失败意味着状态不对，不能假装没事继续往下走。

## Codex 运行时

- 如果 `.git` 被 Codex 沙箱保护，自动请求受控 Git 权限，不要求用户手动完成提交。
- 全局配置和 Skill 的修改也要保存到对应的 Git 仓库；没有可用仓库时再报告具体原因。

## 任务完成后

展示所有 commit 的 oneline log 和当前分支状态。验证通过后，将任务开发分支合并回主分支，并清理开发分支；任务要求时再推送。撤销时使用任务开始前记录的 SHA：`git reset --hard <snapshot-sha>`。

## 边界场景

| 场景                        | 处理                           |
| --------------------------- | ------------------------------ |
| 不是 git 仓库               | 停下来，问用户是否 `git init`  |
| merge 有冲突                | 暂停，列出冲突文件，等用户指示 |
| 发现敏感文件（密钥、token） | 提交前警告，用户确认后才继续   |

## 硬性禁止

- 提交密钥，token，密码等敏感信息
- commit message 写无意义词汇
- pull 失败后继续执行
- 合并前必须确认测试、工作区和冲突状态均通过
- **在 main 上改写历史** — `git reset --hard`、`git rebase`、`git push --force` 在 main 上永远禁止
- **强制删除有提交记录的分支（`git branch -D`）** — 只有用户明确选择"撤销所有改动"时，才允许对当前任务分支执行；其他分支不得触碰

> `git reset --hard` 的唯一合法场景：用户在任务完成后选择"撤销"，操作对象是当前任务的功能分支，目标 SHA 是任务开始前记录的 snapshot，且绝不在 main 上执行。

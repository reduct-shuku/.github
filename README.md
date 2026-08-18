# Shuku · 术库 Organization 社区健康文件

发现真正值得使用的 Skills。

Find skills worth using.

本仓库是 [Shuku · 术库](https://github.com/reduct-shuku) 的公共 `.github` 仓库，用于维护 Organization 首页和默认社区协作规范。

Shuku 是一个由 [ReductTech](https://github.com/ReductTech) 发起的 GitHub 原生 Skill 社区。

我们围绕真实的学习、科研、开发和工作场景，建设和维护可直接使用的 Skills。

## Agent Skill Discovery

支持网络访问的 Agent 可以从唯一的 canonical endpoint 获取当前 Skill 清单：

```text
https://reduct-shuku.github.io/.well-known/agent-skills.json
```

Registry 只提供 `name`、`description`、版本和来源定位信息。Agent 应先选择相关 Skill，再从对应仓库按需加载 `SKILL.md`，无需预先加载完整 Skill 内容。

Shuku 提供：

- 可直接安装和使用的 Skills
- 按场景组织的 Skill 仓库
- 社区共同维护的代码和知识
- 实际安装与兼容性验证

对于由 Shuku 社区维护的 Skill，代码、文档、Issue 和 Pull Request 在对应的 Shuku 仓库中协作；对于收录的外部 Skill，其源代码仍由原始仓库维护，Shuku 负责场景说明、安装指引、验证记录和社区协作内容。

## 仓库内容

- [Organization 首页](profile/README.md)
- [Agent Skills Registry](registry/README.md)
- [贡献指南](CONTRIBUTING.md)
- [评审政策](REVIEW_POLICY.md)
- [行为准则](CODE_OF_CONDUCT.md)
- [支持说明](SUPPORT.md)
- [Issue 模板](.github/ISSUE_TEMPLATE)
- [Pull Request 模板](.github/pull_request_template.md)

这些默认社区文件会在 Organization 内未单独提供对应文件的公共仓库中生效。各仓库可以根据自身范围维护更具体的规则。

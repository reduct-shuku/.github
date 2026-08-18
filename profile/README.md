# Shuku · 术库

> 发现真正值得使用的 Skills。
>
> Find skills worth using.

Shuku 是一个由 [ReductTech](https://github.com/ReductTech) 发起的 GitHub 原生 Skill 社区。

我们围绕真实的学习、科研、开发和工作场景，建设和维护可直接使用的 Skills。

## Agent Skill Discovery

支持网络访问的 Agent 可以从以下 canonical endpoint 获取 Shuku 当前提供的 Skill 清单：

```text
https://reduct-shuku.github.io/.well-known/agent-skills.json
```

Agent 只需先读取各 Skill 的 `name` 和 `description`，选择相关 Skill 后再按 registry 中的来源信息加载对应 `SKILL.md`。

## Shuku 提供

- 可直接安装和使用的 Skills
- 按场景组织的 Skill 仓库
- 社区共同维护的代码和知识
- 实际安装与兼容性验证

对于由 Shuku 社区维护的 Skill，代码、文档、Issue 和 Pull Request 在对应的 Shuku 仓库中共同维护。对于收录的外部 Skill，其源代码仍由原始仓库维护；Shuku 维护场景说明、安装指引、验证记录和必要的社区协作内容，并将源代码贡献导向正确的维护仓库。

## 按应用场景浏览

- [education-skills](https://github.com/reduct-shuku/education-skills)：教育与学习场景
- `research-skills`：规划中
- `developer-skills`：规划中
- `productivity-skills`：规划中
- `creator-skills`：规划中
- `business-skills`：规划中

## 推荐状态

| 状态 | 含义 |
| --- | --- |
| **Listed** | 已完成基础信息核对并进入目录。 |
| **Reviewed** | 已按照公开评审维度完成资料与使用方式审阅。 |
| **Verified** | 已在注明的版本和环境中完成可复现的实际任务验证。 |
| **Featured** | 在已评审或已验证项目中，因特定场景价值、内容质量或社区参考价值而获得阶段性展示。 |

状态定义、评审维度与更新规则见 [评审政策](https://github.com/reduct-shuku/.github/blob/main/REVIEW_POLICY.md)。状态反映有记录的评审进度，不构成对项目质量、安全性或持续可用性的保证。

## 首个收录项目

### [intuitive-deep-learning](https://github.com/ReductTech/intuitive-deep-learning)

- 分类：Education / Artificial Intelligence / Deep Learning
- [查看 Shuku 推荐页面](https://github.com/reduct-shuku/education-skills/tree/main/intuitive-deep-learning)

## 参与社区共创

你可以：

- [提交或共同建设新的 Skill](https://github.com/reduct-shuku/.github/issues/new?template=submit-skill.yml)
- [修正已有 Skill 信息](https://github.com/reduct-shuku/.github/issues/new?template=correct-listing.yml)
- [提交实际使用与验证报告](https://github.com/reduct-shuku/.github/issues/new?template=verification-report.yml)
- 按照 [贡献指南](https://github.com/reduct-shuku/.github/blob/main/CONTRIBUTING.md) 完善 Skill 代码、文档和知识内容

如需修改 Skill 代码、报告缺陷或讨论版本发布，请先查看推荐页面标注的维护仓库：Shuku 社区维护的 Skill 在对应的 Shuku 仓库协作，外部 Skill 前往其原始仓库协作。

## 关联项目披露

推荐人、评审者和贡献者应披露与项目之间可能影响判断的关系，包括维护、商业、雇佣、投资、孵化和赞助关系。关联关系本身不阻止收录，但必须清楚标注，以便社区理解信息来源并独立判断。

由 ReductTech 发起或维护的项目会在相应推荐页面明确披露，不因发起方关系自动获得更高推荐状态。

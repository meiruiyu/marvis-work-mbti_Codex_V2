# Marvis 工作版 MBTI Skill 使用说明

## 交付给 Marvis 的文件

交付 `marvis-work-mbti.zip`。解压后的顶层目录必须仍叫 `marvis-work-mbti`，并以其中的 `SKILL.md` 作为唯一 Skill 入口。

如果 Marvis 当前不支持 ZIP 导入，就把完整的 `marvis-work-mbti` 文件夹交给产研注册。不要只交 `SKILL.md`，因为脚本、评分配置、Schema、报告模板和 16 张人格图片都由它引用。

## 不需要交付的目录

`work-mbti-output` 是本地试跑结果，不是 Skill。它可能包含用户的 `evidence.json`、`score.json`、报告和测试反馈，不能随 Skill 发布。

原始的 `16工作人格形象` 文件夹已复制进 Skill 的 `assets/personalities/`。后续交付不再依赖这个外部文件夹。

## 运行流程

1. 用户明确授权一个或多个工作目录。
2. 采集器输出脱敏 `evidence.json`。
3. 评分器输出 `score.json`。
4. 报告器读取人格类型并自动选择对应的 `assets/personalities/<TYPE>.png`，填充固定 `900×1200` HTML/CSS 模板。
5. Chrome/Chromium 对模板做确定性截图，生成最终 `report.png`；`report.html` 只作为中间预览，不交给大模型重新生图。
6. 同步生成 `data_collection.csv`、`evidence_table.csv` 和 `data_manifest.json`。
7. 测试期在报告生成后收集心理 MBTI 和 1-7 分反馈；提交后自动生成 `feedback.json` 并刷新研究数据表。

内测流程分两态：首次扫描后是 `awaiting_feedback`；只有反馈文件生成、研究表刷新、最终产物校验通过后才是 `complete`。最终 PNG 不得出现 AI 平台水印、模型 Logo 或外链素材，右下角只保留 Marvis 活动标签。

运行结果应写到 Skill 外的独立目录，并在下次扫描时通过 `--exclude` 排除，防止报告再次被当成工作证据。

## 两种评分模式

- 测试期：`beta_blind`。不向评分器提供心理 MBTI，用于测量真实命中率。
- 正式 Campaign：`campaign_compare`。提供心理 MBTI 作为生活基线，只有高覆盖强证据才允许翻转，最多翻两个字母。

## Marvis 需要提供的宿主能力

- 本地文件扫描和明确授权目录。
- Python 3 运行环境。
- Chrome/Chromium 无头截图能力。
- Python 标准库校验最终 PNG 尺寸和文件有效性，不需要额外图像生成依赖。
- 可选：端侧文档语义标签、应用活跃度代理。缺失时对应指标从分母移除，不计零分。

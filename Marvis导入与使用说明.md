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
4. 报告器读取人格类型并自动选择对应的 `assets/personalities/<TYPE>.png`，生成 `report.json` 和固定 3:4 `report.png`；不再生成 HTML 报告。
5. 同步生成 `data_collection.csv`、`evidence_table.csv` 和 `data_manifest.json`。
6. 测试期在报告生成后收集心理 MBTI 和 1-7 分反馈；提交后自动生成 `feedback.json` 并刷新研究数据表。

运行结果应写到 Skill 外的独立目录，并在下次扫描时通过 `--exclude` 排除，防止报告再次被当成工作证据。

## 两种评分模式

- 测试期：`beta_blind`。不向评分器提供心理 MBTI，用于测量真实命中率。
- 正式 Campaign：`campaign_compare`。提供心理 MBTI 作为生活基线，只有高覆盖强证据才允许翻转，最多翻两个字母。

## Marvis 需要提供的宿主能力

- 本地文件扫描和明确授权目录。
- Python 3 运行环境。
- Pillow 图像渲染能力与中文字体；不依赖浏览器截图。
- 可选：端侧文档语义标签、应用活跃度代理。缺失时对应指标从分母移除，不计零分。

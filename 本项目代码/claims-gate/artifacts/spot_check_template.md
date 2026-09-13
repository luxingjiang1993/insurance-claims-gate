# Judge–human 合成抽检表（模板）

**性质：** SPEC P1-7 占位。供个人用合成「标注 A / 标注 B / 裁决」对 SC 夹具做手工对照演练。

**延后（本票不做）：** 真实核赔员标注、真实用户作业中心实测、≥300 人工金标全量运营（PRD M3）。合成表**不得**冒充金标运营。

**不阻塞：** 轨 A `machine_check` 绿门；本表失败/空缺不影响默认 CI。

`Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS`

## 列说明

| 列 | 含义 |
|----|------|
| case_id | 夹具案件号（如 CLM-SC01-001） |
| 系统裁决 | 系统 `decision_type`（如 supplement / reject_draft / approve_recommend） |
| 合成标注A | 个人扮演标注员 A 的合成标签 |
| 合成标注B | 个人扮演标注员 B 的合成标签 |
| 合成裁决 | 双人分歧时的第三人裁决（合成） |
| 是否一致 | 合成裁决与系统裁决是否一致（true/false） |
| 备注 | 演练说明；须标明「合成」 |

## 空表（复制后手填）

| case_id | 系统裁决 | 合成标注A | 合成标注B | 合成裁决 | 是否一致 | 备注 |
|---------|----------|-----------|-----------|----------|----------|------|
|         |          |           |           |          |          |      |

机读同构见 `spot_check_sample_sc01.json`；一致率字段名：`judge_human_agreement`（校验报告 / ledger 事件可挂 null）。

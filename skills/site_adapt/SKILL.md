# site_adapt 多站点规则适配技能

作用：指导 Agent 如何识别和适配不同音乐站点的公开 API 与字段映射。

## 调用场景
- 新增或切换目标音乐站点
- 站点 API 返回格式异常
- 需要选择正确的 spider_rules 配置

## 执行步骤
1. 识别 source（qq / netease）
2. 加载 config/spider_rules/{source}.json
3. 返回 endpoints 与 field_mapping 摘要

## 调用示例
```
skill: site_adapt
args: {"source": "qq", "data_type": "hot_chart"}
```

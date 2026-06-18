# data_clean 数据清洗技能

作用：对原始音乐数据进行去重、字段统一、空值过滤，输出标准 TrackRecord 格式。

## 调用场景
- 各站点返回字段名不一致
- 存在重复歌曲记录
- 需要统一 duration、play_count 等字段格式

## 执行步骤
1. 接收 raw_data（list 或 dict）和 source 站点标识
2. 按 field_mapping 映射到统一 schema
3. 去重（track_id + title）
4. 过滤空 title 记录
5. 输出清洗后的 tracks 列表

## 调用示例
```
skill: data_clean
args: {"raw_data": [...], "source": "qq"}
```

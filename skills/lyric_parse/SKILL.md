# lyric_parse 歌词解析技能

作用：解析 LRC 格式歌词，提取时间轴与纯文本。

## 调用场景
- 原始歌词为 LRC 格式
- 需要纯文本歌词用于标签分类
- 需要时间轴用于展示

## 执行步骤
1. 接收 lyric_raw 字符串
2. 解析 [mm:ss.xx] 时间戳
3. 输出 lines（带时间轴）和 plain_text（纯文本）

## 调用示例
```
skill: lyric_parse
args: {"lyric_raw": "[00:12.00]窗外的麻雀..."}
```

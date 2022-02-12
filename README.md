# get_kaisou_data
从main.js与api_start2.json中提取舰娘改造条件的脚本

## 使用方法

poi->舰娘信息->过滤器->可以改造：是
导出数据->当前列表->导出到文件->dock.csv

放置于同目录下

```bash
python3 get_kaisou_data.py
```

将自动下载最新的`api_start2.json`和`main.js`，并计算出改修所需特殊素材


注2：脚本运行需要几分钟时间，请稍事等待。

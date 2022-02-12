from math import fabs
import re
import json
import requests
import pandas as pd

kaisou_data = {}
"""
kaisou_data 改造所需素材

key: cur_ship_id 改前id

value: a dict: {
    "api_id": after_ship_id,        # 改造后id
    "cur_ship_id": cur_ship_id,     # 当前id
    "ammo": ship["api_afterbull"],  # 改造弹耗
    "steel": ship["api_afterfuel"], # 改造钢耗（为什么api里写的是fuel油？？？）
    "drawing": 0,                   # 图纸          暂置0
    "catapult": 0,                  # 甲板          暂置0
    "report": 0,                    # 详报          暂置0
    "devkit": 0,                    # 开发紫菜      暂置0
    "buildkit": 0,                  # 喷火          暂置0
    "aviation": 0,                  # 新航空紫菜    暂置0
    "hokoheso": 0,                  # 新火炮紫菜    暂置0
    "arms":     0,                  # 新兵装紫菜    暂置0
}
"""


id2name = {}
"""
key: 船的id
value: 船的名字
"""


id2sortno = {}
"""
key: 船的id
value: sortno, 图鉴编号
"""


# main_js_url = 'http://ooi.moe/kcs2/js/main.js'
# 2020.04: Because of c2's technology progress,
# We use this one: https://raw.githubusercontent.com/kcwikizh/kancolle-main/master/dist/main.js
main_js_url = 'https://raw.githubusercontent.com/kcwikizh/kancolle-main/master/dist/main.js'
main_js_path = './main.js'
api_start2_json_url = 'http://api.kcwiki.moe/start2'
api_start2_json_path = './api_start2.json'

# step 0: download latest api_start2.json and main.js
print('step 0: download latest api_start2.json and main.js')
with open(api_start2_json_path, 'w', encoding='utf8') as f:
    print("Downloading api_start2.json")
    f.write(requests.get(api_start2_json_url).text)
with open(main_js_path, 'w', encoding='utf8') as f:
    print("Downloading main.js")
    f.write(requests.get(main_js_url).text)


# step 1: get id2name and id2sortno from api_start2.json
print('step 1: get id2name dict from api_start2.json')
with open(api_start2_json_path, 'r', encoding='utf8') as f:
    api_start2 = json.load(f)
    for ship in api_start2["api_mst_ship"]:
        id_ = ship["api_id"]
        name = ship["api_name"]
        sortno = ship.get("api_sortno", -1)     # 深海不存在api_sortno
        id2name[id_] = name
        id2sortno[id_] = sortno


# step 2.1: parse api_start2.json, get all KaiSou-able ships , get ammo and steel cost
print('step 2.1: parse api_start2.json, get all KaiSou-able ships, get ammo and steel cost')
with open(api_start2_json_path, 'r', encoding='utf8') as f:
    api_start2 = json.load(f)
    for ship in api_start2["api_mst_ship"]:
        if ship["api_id"] > 1500:
            continue      # 深海舰id>=1501
        after_ship_id = int(ship["api_aftershipid"])
        if after_ship_id:
            cur_ship_id = ship["api_id"]
            kaisou_data[cur_ship_id] = {
                'name':id2name[cur_ship_id],
                "api_id": after_ship_id,        # 改造后id
                "cur_ship_id": cur_ship_id,     # 当前id
                "ammo": ship["api_afterbull"],  # 改造弹耗
                "steel": ship["api_afterfuel"], # 改造钢耗（为什么api里写的是fuel油？？？）
                "drawing": 0,                   # 图纸      暂置0
                "catapult": 0,                  # 甲板      暂置0
                "report": 0,                    # 详报      暂置0
                "devkit": 0,                    # 开发紫菜  暂置0
                "buildkit": 0,                  # 喷火      暂置0
                "aviation": 0,                  # 新航空紫菜暂置0
                "hokoheso": 0,                  # 新火炮紫菜暂置0
                "arms": 0,                      # 新兵装紫菜暂置0
            }


# step 2.2: parse api_start2.json again, get api_id, cur_ship_id, drawing, catapult, report, aviation, and arms (key: cur_ship_id)
print('step 2.2: parse api_start2.json again, get api_id, cur_ship_id, drawing, catapult, report, aviation (key: cur_ship_id)')
with open(api_start2_json_path, 'r', encoding='utf8') as f:
    api_start2 = json.load(f)
    for item in api_start2["api_mst_shipupgrade"]:
        api_id = item["api_id"]
        cur_ship_id = item["api_current_ship_id"]
        if 0 == cur_ship_id:
            continue        # 原生舰船，非改造而来
        kaisou_data[cur_ship_id]["drawing"] = item["api_drawing_count"]
        kaisou_data[cur_ship_id]["catapult"] = item["api_catapult_count"]
        kaisou_data[cur_ship_id]["report"] = item["api_report_count"]
        kaisou_data[cur_ship_id]["aviation"] = item["api_aviation_mat_count"]
        kaisou_data[cur_ship_id]["arms"] = item["api_arms_mat_count"]


# step 3.1: parse main.js, get newhokohesosizai
print('step 3.1: parse main.js, get newhokohesosizai')
rex_hokoheso_func = re.compile(r'''Object.defineProperty\(\w+.prototype, *["']newhokohesosizai["'], *{\s*'?get'?: *function\(\) *{\s*switch *\(this.mst_id_after\) *{\s*(((case *\d+:\s*)+return *\d+;\s*)+)''', re.M)
rex_hokoheso_item = re.compile(r'((case *\d+:\s*)+)return *(\d+);\s*')
rex_case = re.compile(r'case *(\d+):')

with open(main_js_path, 'r', encoding='utf8') as f:
    ctx = f.read()
    match = rex_hokoheso_func.search(ctx)
    for m in rex_hokoheso_item.finditer(match.group(1)):
        hokoheso_num = int(m.group(3))
        for m_c in rex_case.finditer(m.group(1)):
            api_id = int(m_c.group(1))
            for k, v in kaisou_data.items():        # 此处可优化，但现在我太困了
                # 算了不优化了，这一部分素材是根据“改后的舰船”决定的，可能由多种路径改造而来
                # 最简明的写法就是遍历一遍
                if v['api_id'] == api_id:           
                    v['hokoheso'] = hokoheso_num
                    print(f"{cur_ship_id=}\t{api_id=}\t{hokoheso_num=}")



# step 3.2: parse main.js again, get DevKit and BuildKit
print('step 3.2: parse main.js again, get DevKit and BuildKit')
rex_devkit = re.compile(r'\w+.prototype._getRequiredDevkitNum *= *function\(\w+, *\w+, *\w+\) *{\s*switch *\(\w+\) *{\s*(((case *\d+:\s*)+return *\d+;\s*)+)')
rex_buildkit = re.compile(r'\w+.prototype._getRequiredBuildKitNum *= *function\(\w+\) *{\s*switch *\(\w+\) *{\s*(((case *\d+:\s*)+return *\d+;\s*)+)')
rex_case_ret = re.compile(r'((case *\d+:\s*)+)return *(\d+);\s*')
rex_case = re.compile(r'case *(\d+):')

def add_kaisou_key_value(key_name, rex_func):
    with open(main_js_path, 'r', encoding='utf8') as f:
        ctx = f.read()
        match = rex_func.search(ctx)
        for m_ct in rex_case_ret.finditer(match.group(1)):
            value = int(m_ct.group(3))
            for m_c in rex_case.finditer(m_ct.group(1)):
                c = int(m_c.group(1))
                if c in kaisou_data:
                    kaisou_data[c][key_name] = value
                else:
                    print(f'ERROR: key "{c}" is not in kaisou_data!')

add_kaisou_key_value('devkit', rex_devkit)
add_kaisou_key_value('buildkit', rex_buildkit)


# step 4: get DevKit with another rule. 
#         (At 2021-09-04, only 503: 鈴谷改二 -> 鈴谷航改二 and 504: 熊野改二 -> 熊野航改二 use this rule)
print('step 4: get DevKit with another rule.')
'''
i: steel cost
e: blue print/drawing cost
t: cur_ship_id
this._USE_DEVKIT_GROUP_ = [503, 504];
default:
    return 0 != e && -1 == this._USE_DEVKIT_GROUP_.indexOf(t) ?
        0 :
        i < 4500 ?
        0 :
        i < 5500 ?
        10 :
        i < 6500 ?
        15 :
        20;
'''
rex_use_devkit_group = re.compile(r'this._USE_DEVKIT_GROUP_ *= *\[\s*((\d+,?\s*)+)\]', re.M)
use_devkit_group = []
with open(main_js_path, 'r', encoding='utf8') as f:
    ctx = f.read()
    match = rex_use_devkit_group.search(ctx)
    for m in re.finditer(r'\d+', match.group(1)):
        use_devkit_group.append(int(m.group()))

for k, v in kaisou_data.items():
    if v["devkit"] != 0:
        continue        # 属于上述case的情况，已赋值
    if 0 != v["drawing"] and k not in use_devkit_group:
        v["devkit"] = 0
    else:
        steel = v["steel"]
        v["devkit"] = 0 if steel < 4500 else 10 if steel < 5500 else 15 if steel < 6500 else 20


# print(kaisou_data)

with open("kaisou_dict.json",'w+') as f:
    json.dump(kaisou_data,f,ensure_ascii=False)

name2id = {}

for id,name in id2name.items():
    name2id[name]=id

dockyard = pd.read_csv('dock.csv')

with open('result.csv','w+') as f:
    #         ("drawing",     "改装设计图"), 
    #         ("buildkit",    "高速建造材"),
    #         ("devkit",      "开发资材"),
    #         ("catapult",    "试制甲板用弹射器"),
    #         ("report",      "战斗详报"),
    #         ("aviation",    "新型航空兵装资材"),
    #         ("hokoheso",    "新型火炮兵装资材"),
    #         ("arms",        "新型兵装资材"),
    f.write('名称,改装设计图,高速建造资材,开发资材,试制甲板用弹射器,战斗详报,新型航空兵装资材,新型火炮兵装资材,新型兵装资材\n')
    for _,id in enumerate(dockyard['舰名']):
        try:
            ship = kaisou_data[name2id[id]]
            f.write("{},{},{},{},{},{},{},{},{}\n".format(ship['name'],ship['drawing'],ship['buildkit'],ship['devkit'],ship['catapult'],ship['report'],ship['aviation'],ship['hokoheso'],ship['arms']))
        except :
            pass
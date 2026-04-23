import json
import random

RANDOM_FIELDS = ["Seed", "Random Seed", "seed", "random_seed"]


def value_match_type(value, widget_type):
    """判断值是否与 widget_type 匹配，除了 INT, FLOAT 以外，一律视为字符串"""
    if widget_type == "INT":
        return isinstance(value, int)
    elif widget_type == "FLOAT":
        return isinstance(value, (int, float))
    else:
        return isinstance(value, str)


def convert_workflow_to_api(workflow, change_random=True):
    """
    将工作流转换为 API 调用的所需格式

    Args:
        workflow: 工作流 JSON文件内容
        change_random: 是否改变随机数字段，默认 True
    """
    # 输出为 JSON 格式
    result = {}
    # output 暂存
    output_map = {}
    # 待修改的 LinkMap（link_id -> (要修改的对象, 要修改的字段)）
    link_map = {}
    # 1. 提取 nodes 节点（数组）
    nodes = workflow.get("nodes", [])
    # 2. 遍历 nodes 节点，提取所需信息
    for node in nodes:
        # id 作为键
        id = node.get("id", "")
        # 节点出入度
        degree_cnt = 0
        # type 作为 class_type
        class_type = node.get("type", "")
        # inputs 逐个处理，保留原有结构
        wf_inputs = node.get("inputs", [])
        widgets = node.get("widgets_values", [])
        wid_ind = 0
        inputs = {}
        for inp in wf_inputs:
            # key 为 input 的 name
            key = inp.get("name", "")
            # link 指向一个 Link Id 的，暂时记录下来
            link_id = inp.get("link")
            if link_id:
                inputs[key] = link_id
                link_map[link_id] = (inputs, key)
                degree_cnt += 1
            else:
                # 未指向节点的，且有 widget 字段存在，从 widgets 中获取一个类型匹配的值，不匹配的直接跳过
                if inp.get("widget") is not None:
                    while wid_ind < len(widgets):
                        if not value_match_type(widgets[wid_ind], inp.get("type")):
                            wid_ind += 1
                            continue
                        inputs[key] = widgets[wid_ind]
                        if change_random and key in RANDOM_FIELDS:
                            inputs[key] = random.randint(0, 2**64 - 1)
                        wid_ind += 1
                        break
                # 否则不写任何值（即移除该字段）
                # else:
                #     inputs[key] = ""
        # 存在 outputs 节点的，数组中的每个元素的 links 字段为一个存储 LinkId 的数组，需要记下来，后续去除 LinkId 字段需要使用
        outputs = node.get("outputs", [])
        output_map[id] = [o.get("links", []) for o in outputs]
        for out in outputs:
            degree_cnt += len(out.get("links", []))
        # 节点出入度为0（孤节点）的，删除
        if degree_cnt == 0:
            continue
        # 结果的基础结构
        result[id] = {
            "class_type": class_type,
            "inputs": inputs,
            # 可省略
            # "_meta": {
            #     "title": class_type
            # }
        }
    # 3. 双重循环遍历，将 outputs 中的 LinkId 替换为节点 ID，并纠正索引
    # 存在 outputs 节点的，每个都要处理
    for from_id, link_id_arrs in output_map.items():
        # 每个 linkId 都要找到其指向的节点
        for link_index, link_ids in enumerate(link_id_arrs):
            # 每个 linkId 都要处理
            for link_id in link_ids:
                # 根据保存的 LinkMap，找到要修改的对象和字段
                obj, field = link_map[link_id]
                # 替换 LinkId 为节点 ID，并纠正索引
                obj[field] = [str(from_id), link_index]
    # 4. 按节点 ID 顺序排序后，将键转为字符串类型后，返回结果
    result = dict(sorted(result.items()))
    return {str(k): v for k, v in result.items()}


# 逐级验证转换是否符合预期
if __name__ == "__main__":
    # 输入文件
    input_file = "test/inp.json"
    # 比对文件
    output_file = "test/out.json"

    # 递归比对节点
    def compare_node(node1, node2):
        """递归比对节点"""
        if isinstance(node1, dict) and isinstance(node2, dict):
            for key, value in node1.items():
                if key in node2:
                    if isinstance(value, dict):
                        if not compare_node(value, node2[key]):
                            return False
                    elif value != node2[key]:
                        print(f"节点 {key} 的值不一致")
                        return False
                else:
                    print(f"节点 {key} 缺少字段")
                    return False
            return True
        else:
            print("节点类型不一致")
            return False

    # 读取输入输出文件
    with open(input_file, "r", encoding="utf-8") as f:
        workflow = json.load(f)
        # 转换为 API 格式
        api_workflow = convert_workflow_to_api(workflow, change_random=False)
    with open(output_file, "r", encoding="utf-8") as f:
        expected_workflow = json.load(f)
        # 递归验证节点是否一致
        if not compare_node(api_workflow, expected_workflow):
            print("转换验证失败")
            exit(1)
        print("转换验证通过")

# TODO: 启动一个转发服务，通过转换函数调用工作流
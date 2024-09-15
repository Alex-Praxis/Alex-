import random
import json
import os
from datetime import date  # 用于获取当前日期

SAVE_FILE = 'game_state.json'

# 初始化变量
prize_pool = []
total_won_value = 0  # 已抽取奖品的总价值
total_voucher = 0  # 总代金券金额
total_pool_value = 3000  # 总奖池价值
prize_id_counter = 1  # 奖品编号计数器
letter_counter = 0  # 字母计数器
draw_history = []  # 抽奖历史记录


# 定义函数：计算奖品的概率
def calculate_probability(prize_value):
    return prize_value / total_pool_value if total_pool_value > 0 else 0


# 生成编号，使用字母加数字的组合，例如 A1, B2, C3 等
def generate_prize_id():
    global prize_id_counter, letter_counter
    letter = chr(65 + letter_counter)  # 从 'A' 开始，递增字母
    prize_id = f"{letter}{prize_id_counter}"
    prize_id_counter += 1
    if prize_id_counter > 99:  # 达到一定数量后，字母变动
        prize_id_counter = 1
        letter_counter += 1
    return prize_id


# 批量交互输入奖品
def add_prizes_interactive():
    print("请输入奖品信息，每个奖品格式为 '名称,价值,限制'，用空格分隔不同奖品，输入 'done' 完成:")
    while True:
        prizes_input = input("批量输入奖品 (例: 苹果,5,1 鼠标,300,1 礼品卡,50,无限): ")
        if prizes_input.lower() == 'done':
            break
        prizes_list = prizes_input.split()
        for prize in prizes_list:
            try:
                prize_name, prize_value, limit_value = prize.split(',')
                prize_value = int(prize_value)
                if limit_value.isdigit():
                    limit_value = int(limit_value)
                else:
                    limit_value = limit_value.lower()

                if check_prize_name_exists(prize_name):
                    print(f"输入错误：奖品名称 '{prize_name}' 已经存在，请重新输入。")
                else:
                    add_prize(prize_name, prize_value, limit_value)
            except ValueError:
                print(f"输入格式有误: {prize}")


# 检查奖品名称是否已存在
def check_prize_name_exists(prize_name):
    for prize in prize_pool:
        if prize_name == prize['name']:
            return True
    return False


# 添加奖品的核心逻辑
def add_prize(prize_name, prize_value, limit_value):
    fragments = decide_fragments(prize_value)
    fragment_value = prize_value / fragments  # 将奖品价值均分为多个碎片
    prize_pool.append({
        'id': generate_prize_id(),  # 生成唯一编号
        'name': prize_name,
        'total_value': prize_value,  # 奖品总价值
        'fragment_value': fragment_value,  # 每个碎片价值
        'total_fragments': fragments,  # 总碎片数
        'remaining_fragments': fragments  # 剩余碎片数
    })
    update_probabilities()
    save_game_state()


# 动态决定碎片数
def decide_fragments(total_value):
    if total_value <= 100:
        return 1  # 不拆分
    elif total_value <= 500:
        return 2  # 拆分为 2
    elif total_value <= 2000:
        return 4  # 拆分为 4
    else:
        return 8  # 拆分为 8

# 更新奖品的概率
def update_probabilities():
    # 确保使用手动设定的 total_pool_value 作为奖池总价值
    if total_pool_value > 0:
        for prize in prize_pool:
            # 每个奖品的概率 = (奖品剩余碎片的总价值) / (总奖池价值)
            prize['probability'] = (prize['fragment_value'] * prize['remaining_fragments']) / total_pool_value
    else:
        # 如果总奖池价值为0，设置所有奖品的概率为0
        for prize in prize_pool:
            prize['probability'] = 0

    # 计算未中奖的概率，保证总概率等于1
    total_prob = sum(prize['probability'] for prize in prize_pool)
    if total_prob < 1:
        return 1 - total_prob  # 返回未中奖的概率
    else:
        return 0  # 如果总概率大于等于1，没有未中奖的可能性


# 合并移除奖品的功能（单个和批量）
def remove_prizes():
    prize_ids = input("请输入要移除的奖品编号（支持单个或批量，用空格或逗号分隔）: ")

    if ',' in prize_ids:
        prize_ids = prize_ids.split(',')
    else:
        prize_ids = prize_ids.split()

    removed_prizes = []
    for prize_id in prize_ids:
        prize_id = prize_id.strip()
        result = remove_prize_by_id(prize_id)
        removed_prizes.append(result)

    save_game_state()
    return "\n".join(removed_prizes)


# 移除奖品及其所有碎片，通过编号移除
def remove_prize_by_id(prize_id):
    prize_to_remove = next((p for p in prize_pool if p['id'] == prize_id), None)
    if prize_to_remove:
        prize_pool.remove(prize_to_remove)
        update_probabilities()
        return f"奖品编号 '{prize_to_remove['name']}' 已被移除。"
    return f"未找到编号为 {prize_id} 的奖品。"


# 保存游戏状态
def save_game_state():
    game_state = {
        'prize_pool': prize_pool,
        'total_won_value': total_won_value,
        'total_voucher': total_voucher,
        'total_pool_value': total_pool_value,
        'prize_id_counter': prize_id_counter,  # 保存奖品编号计数器
        'letter_counter': letter_counter,  # 保存字母计数器
        'draw_history': draw_history  # 保存抽奖历史
    }
    with open(SAVE_FILE, 'w') as file:
        json.dump(game_state, file)


# 加载游戏状态
def load_game_state():
    global prize_pool, total_won_value, total_voucher, total_pool_value, prize_id_counter, letter_counter, draw_history
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as file:
            game_state = json.load(file)
            prize_pool = game_state.get('prize_pool', [])
            total_won_value = game_state.get('total_won_value', 0)
            total_voucher = game_state.get('total_voucher', 0)
            total_pool_value = game_state.get('total_pool_value', 3000)
            prize_id_counter = game_state.get('prize_id_counter', 1)
            letter_counter = game_state.get('letter_counter', 0)
            draw_history = game_state.get('draw_history', [])

            for prize in prize_pool:
                if 'fragment_value' not in prize:
                    prize['fragment_value'] = prize['total_value'] / prize['total_fragments']
                if 'remaining_fragments' not in prize:
                    prize['remaining_fragments'] = prize['total_fragments']
            update_probabilities()




# 抽奖逻辑
def player_draw():
    global total_won_value, total_voucher, prize_pool

    if not prize_pool:
        return "奖池中没有奖品了。"

    # 计算奖品的累计概率
    cumulative_probabilities = []
    current_sum = 0
    for prize in prize_pool:
        current_sum += prize['probability']
        cumulative_probabilities.append((prize, current_sum))

    # 计算未中奖概率
    no_win_probability = update_probabilities()

    # 生成一个 0 到 1 之间的随机数
    rand_value = random.uniform(0, 1)

    # 如果随机值小于未中奖概率，则未中奖
    if rand_value <= no_win_probability:
        total_voucher += 2
        draw_history.append({"result": "未中奖", "voucher_awarded": 2, "date": date.today().strftime("%Y-%m-%d")})
        save_game_state()
        return f"未中奖，您获得了 2 元代金券，当前代金券总额：{total_voucher} RMB。"

    # 否则，遍历奖品，找到抽中的奖品
    for prize, cumulative_probability in cumulative_probabilities:
        if no_win_probability < rand_value <= no_win_probability + cumulative_probability:  # 如果随机数落在该奖品的概率范围内
            prize['remaining_fragments'] -= 1  # 减少碎片数
            total_won_value += prize['fragment_value']  # 增加抽中奖品的价值

            # 记录中奖碎片到历史
            draw_history.append({
                "result": "中奖",
                "prize": prize['name'],
                "fragment_won": prize['total_fragments'] - prize['remaining_fragments'],
                "total_fragments": prize['total_fragments'],
                "value": prize['fragment_value'],
                "date": date.today().strftime("%Y-%m-%d")
            })

            # 如果所有碎片已抽完，移除奖品
            if prize['remaining_fragments'] == 0:
                prize_pool.remove(prize)

            # 更新概率并保存状态
            update_probabilities()
            save_game_state()
            return f"您抽中了 {prize['name']} 的一个碎片！已抽中 {prize['total_fragments'] - prize['remaining_fragments']}/{prize['total_fragments']} 碎片。"




# 修改奖品的名称、价值和碎片数
def modify_prize(prize_id):
    prize_to_modify = next((p for p in prize_pool if p['id'] == prize_id), None)
    if prize_to_modify:
        new_name = input(f"输入新的奖品名称 (当前: {prize_to_modify['name']}): ")
        new_value = int(input(f"输入新的奖品价值 (当前: {prize_to_modify['total_value']} RMB): "))
        new_fragments = int(input(f"输入新的碎片数量 (当前: {prize_to_modify['total_fragments']}): "))

        prize_to_modify['name'] = new_name
        prize_to_modify['total_value'] = new_value
        prize_to_modify['total_fragments'] = new_fragments
        prize_to_modify['fragment_value'] = new_value / new_fragments
        prize_to_modify['remaining_fragments'] = new_fragments

        update_probabilities()
        save_game_state()
        return f"奖品 {new_name} 修改成功！"
    return f"未找到编号为 {prize_id} 的奖品。"


# 查看抽奖历史
def view_draw_history():
    if not draw_history:
        return "没有抽奖历史。"
    history_str = "\n".join(
        [f"{entry['date']} - {entry['result']}: {entry.get('prize', '无')} - {entry.get('voucher_awarded', '')}" for
         entry in draw_history])
    return f"抽奖历史:\n{history_str}"


# 查看已抽取奖品的总价值
def view_won_prize_total():
    return f"已抽取奖品总价值: {total_won_value} RMB"


# 查看代金券总额
def view_voucher_total():
    return f"当前代金券总额: {total_voucher} RMB"


# 查看用户拥有的碎片
def view_fragments():
    fragment_info = []
    for prize in prize_pool:
        if prize['remaining_fragments'] < prize['total_fragments']:
            fragment_info.append(
                f"{prize['name']} - 已拥有 {prize['total_fragments'] - prize['remaining_fragments']} / {prize['total_fragments']} 碎片")
    if not fragment_info:
        return "您没有任何碎片。"
    return "\n".join(fragment_info)


def main_menu():
    global total_pool_value
    load_game_state()

    while True:
        print("\n===================== 抽奖系统 =====================")
        print(f"当前总奖池价值: {total_pool_value} RMB")
        print(f"已抽取奖品总价值: {total_won_value} RMB")
        print(f"当前代金券总额: {total_voucher} RMB")
        print("--------------------------------------------------")
        print("奖池中的奖品（编号: 名称 - 剩余碎片/总碎片）：")
        for prize in prize_pool:
            print(f"- {prize['id']}: {prize['name']} - {prize['remaining_fragments']}/{prize['total_fragments']} 碎片")

        print("\n===================== 操作选项 =====================")
        print("1. 添加奖品 (批量)        \t5. 查看抽奖历史")
        print("2. 移除奖品（单个或批量） \t6. 查看已抽取奖品总额")
        print("3. 修改奖品               \t7. 查看代金券总额")
        print("4. 抽奖                   \t8. 查看我的碎片")
        print("9. 修改奖池总价值         \t10. 退出")
        print("=====================================================")

        choice = input("请输入选择 (1-10): ")

        if choice == "1":
            add_prizes_interactive()

        elif choice == "2":
            print(remove_prizes())

        elif choice == "3":
            prize_id = input("请输入要修改的奖品编号: ")
            print(modify_prize(prize_id))

        elif choice == "4":
            print(player_draw())

        elif choice == "5":
            print(view_draw_history())

        elif choice == "6":
            print(view_won_prize_total())

        elif choice == "7":
            print(view_voucher_total())

        elif choice == "8":
            print(view_fragments())

        elif choice == "9":
            try:
                new_value = int(input("输入新的总奖池价值 (RMB): "))
                total_pool_value = new_value
                update_probabilities()
                save_game_state()
            except ValueError:
                print("输入有误，请输入一个数字。")

        elif choice == "10":
            print("退出程序，保存状态。")
            break

        else:
            print("无效选择，请重新输入。")


# 程序入口
if __name__ == "__main__":
    main_menu()

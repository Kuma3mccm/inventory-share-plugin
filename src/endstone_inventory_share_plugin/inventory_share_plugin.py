import os
import re
import ast

import pymysql
from endstone import *
from endstone.event import *
from endstone.inventory import *
from endstone.plugin import Plugin


def get_item(all_item: list, item_num: int, item: ItemStack) -> list:
    if item:
        item_id = item.type
        item_amount = item.amount
        if item.item_meta.has_display_name:
            item_name = item.item_meta.display_name
        else:
            item_name = "None"
        if item.item_meta.has_lore:
            item_lore = item.item_meta.lore
        else:
            item_lore = "None"
        all_item.append({'num': item_num, 'item': item_id, 'amount': item_amount, 'name': item_name, 'lore': item_lore})
    else:
        item_id = "None"
        item_amount = 0
        item_name = "None"
        item_lore = "None"
        all_item.append({'num': item_num, 'item': item_id, 'amount': item_amount, 'name': item_name, 'lore': item_lore})
    return all_item


def connect_db(sql_host, sql_port, sql_user, sql_pass, db_name):
    # MySQLに接続
    conn = pymysql.connect(
        host=sql_host,
        port=int(sql_port),
        user=sql_user,
        password=sql_pass
    )

    # カーソルを取得
    cursor = conn.cursor()

    # データベースを選択
    cursor.execute(f"USE {db_name}")

    return conn, cursor


def get_player_item(item, all_item, item_num):
    if item:
        item_id = item.type
        item_amount = item.amount
        if item.item_meta.has_display_name:
            item_name = item.item_meta.display_name
        else:
            item_name = "None"
        if item.item_meta.has_lore:
            item_lore = item.item_meta.lore
        else:
            item_lore = "None"
        all_item.append({'num': item_num, 'item': item_id, 'amount': item_amount, 'name': item_name, 'lore': item_lore})
        # print(str(self.server.get_player(target.name).inventory.get_item(item_num)))
    else:
        item_id = "None"
        item_amount = 0
        item_name = "None"
        item_lore = "None"
        all_item.append({'num': item_num, 'item': item_id, 'amount': item_amount, 'name': item_name, 'lore': item_lore})
        # print(str(self.server.get_player(target.name).inventory.get_item(item_num)))


class InventorySharePlugin(Plugin):
    api_version = "0.6"

    def __init__(self):
        super().__init__()
        self.sql_host: str = ""
        self.sql_port: int = 0
        self.sql_user: str = ""
        self.sql_pass: str = ""
        self.sql_db_name: str = ""

    def load_config(self) -> None:
        self.sql_host = self.config["sql_host"]
        self.sql_port = self.config["sql_port"]
        self.sql_user = self.config["sql_user"]
        self.sql_pass = self.config["sql_pass"]
        self.sql_db_name = self.config["sql_db_name"]

    def on_load(self) -> None:
        load_text = f"{ColorFormat.AQUA}InventorySharePlugin is loaded!{ColorFormat.RESET}"
        self.logger.info(load_text)

    def on_enable(self) -> None:
        enable_text = f"{ColorFormat.AQUA}InventorySharePlugin is enabled!{ColorFormat.RESET}"
        self.logger.info(enable_text)
        self.save_default_config()
        self.load_config()

        if not os.path.exists("plugins/inventory_share_plugin/config.toml"):
            self.logger.error(
                "config.toml not found")
        self.register_events(self)

    def on_disable(self) -> None:
        disable_text = f"{ColorFormat.AQUA}InventorySharePlugin is disabled!{ColorFormat.RESET}"
        self.logger.info(disable_text)

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent) -> None:
        self.logger.info(f"Join Events")
        target = event.player

        # MySQLに接続
        conn, cursor = connect_db(self.sql_host, self.sql_port, self.sql_user, self.sql_pass, self.sql_db_name)

        # データベースを検索
        data = "SELECT player_inv FROM player_data WHERE player_xuid = %s"
        cursor.execute(data, target.xuid)
        v = cursor.fetchall()
        if v:
            inventory_data = v[0]  # SQLから取得したデータ
            if isinstance(inventory_data, tuple):
                inventory_data = inventory_data[0]  # タプルから文字列を取得

            pattern = re.compile(
                r'§eitem_slot:(-?\d+)\s+'
                r'item:(\S+)\s+'
                r'amount:(\d+)\s+'
                r'name:(\S+)\s+'
                r'lore:(None|\[.*?\])',
                re.DOTALL
            )

            matches = pattern.findall(inventory_data)

            inv = self.server.get_player(target.name).inventory

            clear = ItemStack("minecraft:air", 1)

            inv.clear()
            inv.helmet = clear
            inv.chestplate = clear
            inv.leggings = clear
            inv.boots = clear
            inv.item_in_off_hand = clear

            for match in matches:
                slot = int(match[0])
                item_type = match[1]
                amount = int(match[2])
                name = match[3]
                lore = match[4]
                if item_type == "None":
                    continue

                # print(f"{slot} {item_type} {amount} {name} {lore}")

                # print(int(slot))
                if int(slot) >= 0:
                    inv.set_item(int(slot), ItemStack(str(item_type), int(amount)))
                elif int(slot) == -1:
                    inv.helmet = ItemStack(str(item_type), int(amount))
                elif int(slot) == -2:
                    inv.chestplate = ItemStack(str(item_type), int(amount))
                elif int(slot) == -3:
                    inv.leggings = ItemStack(str(item_type), int(amount))
                elif int(slot) == -4:
                    inv.boots = ItemStack(str(item_type), int(amount))
                elif int(slot) == -5:
                    inv.item_in_off_hand = ItemStack(str(item_type), int(amount))

                if name != "None":
                    if slot >= 0:
                        item = inv.get_item(int(slot))
                    elif slot == -1:
                        item = inv.helmet
                    elif slot == -2:
                        item = inv.chestplate
                    elif slot == -3:
                        item = inv.leggings
                    elif slot == -4:
                        item = inv.boots
                    elif slot == -5:
                        item = inv.item_in_off_hand
                    meta = item.item_meta
                    meta.display_name = name

                    item.set_item_meta(meta)

                    if slot >= 0:
                        inv.set_item(int(slot), item)
                    elif slot == -1:
                        inv.helmet = item
                    elif slot == -2:
                        inv.chestplate = item
                    elif slot == -3:
                        inv.leggings = item
                    elif slot == -4:
                        inv.boots = item
                    elif slot == -5:
                        inv.item_in_off_hand = item

                if lore != "None":
                    if slot >= 0:
                        item = inv.get_item(int(slot))
                    elif slot == -1:
                        item = inv.helmet
                    elif slot == -2:
                        item = inv.chestplate
                    elif slot == -3:
                        item = inv.leggings
                    elif slot == -4:
                        item = inv.boots
                    elif slot == -5:
                        item = inv.item_in_off_hand
                    lores = ast.literal_eval(lore)
                    meta = item.item_meta
                    meta.lore = lores

                    item.set_item_meta(meta)

                    if slot >= 0:
                        inv.set_item(int(slot), item)
                    elif slot == -1:
                        inv.helmet = item
                    elif slot == -2:
                        inv.chestplate = item
                    elif slot == -3:
                        inv.leggings = item
                    elif slot == -4:
                        inv.boots = item
                    elif slot == -5:
                        inv.item_in_off_hand = item

        # 接続を閉じる
        cursor.close()
        conn.close()
        return

    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent) -> None:

        target = event.player

        # MySQLに接続
        conn, cursor = connect_db(self.sql_host, self.sql_port, self.sql_user, self.sql_pass, self.sql_db_name)

        # インベントリ保存イベント
        all_item = []
        try:
            for item_num in range(36):
                item = self.server.get_player(target.name).inventory.get_item(item_num)
                get_player_item(item, all_item, item_num)
            item = self.server.get_player(target.name).inventory.helmet
            get_player_item(item, all_item, -1)
            item = self.server.get_player(target.name).inventory.chestplate
            get_player_item(item, all_item, -2)
            item = self.server.get_player(target.name).inventory.leggings
            get_player_item(item, all_item, -3)
            item = self.server.get_player(target.name).inventory.boots
            get_player_item(item, all_item, -4)
            item = self.server.get_player(target.name).inventory.item_in_off_hand
            get_player_item(item, all_item, -5)

            output_item = ""
            for item_info in all_item:
                message = "-" * 20 + "\n"
                message += f'{ColorFormat.YELLOW}item_slot:{item_info["num"]} \n item:{item_info["item"]} \n amount:{item_info["amount"]} \n name:{item_info["name"]} \n lore:{item_info["lore"]} \n'
                output_item += message

            # データベースを検索
            data = "UPDATE player_data SET player_inv = %s WHERE player_xuid = %s"
            cursor.execute(data, (output_item, target.xuid))
            conn.commit()
            self.logger.info(f'Save inventory')

        except:
            self.logger.error(f'Failed save inventory')


        # 接続を閉じる
        cursor.close()
        conn.close()
        return

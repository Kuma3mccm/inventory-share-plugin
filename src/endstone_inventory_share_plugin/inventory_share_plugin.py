import os
import re
import ast
import pymysql

from endstone import *
from endstone.event import *
from endstone.inventory import *
from endstone.plugin import Plugin


def get_item_data(item: ItemStack, item_num: int) -> dict:
    if item:
        return {
            'num': item_num,
            'item': item.type,
            'amount': item.amount,
            'name': item.item_meta.display_name if item.item_meta.has_display_name else "None",
            'lore': item.item_meta.lore if item.item_meta.has_lore else "None"
        }
    return {'num': item_num, 'item': "None", 'amount': 0, 'name': "None", 'lore': "None"}


def connect_db(host, port, user, password, db_name):
    conn = pymysql.connect(host=host, port=int(port), user=user, password=password)
    cursor = conn.cursor()
    cursor.execute(f"USE {db_name}")
    return conn, cursor


def set_item_with_meta(inv, slot, item_type, amount, name, lore):
    item = ItemStack(str(item_type), int(amount))

    if name != "None" or lore != "None":
        meta = item.item_meta
        if name != "None":
            meta.display_name = name
        if lore != "None":
            meta.lore = ast.literal_eval(lore)
        item.set_item_meta(meta)

    if slot >= 0:
        inv.set_item(slot, item)
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


class InventorySharePlugin(Plugin):
    api_version = "0.6"

    def __init__(self):
        super().__init__()
        self.sql_host = ""
        self.sql_port = 0
        self.sql_user = ""
        self.sql_pass = ""
        self.sql_db_name = ""

    def load_config(self):
        self.sql_host = self.config["sql_host"]
        self.sql_port = self.config["sql_port"]
        self.sql_user = self.config["sql_user"]
        self.sql_pass = self.config["sql_pass"]
        self.sql_db_name = self.config["sql_db_name"]

    def on_load(self):
        self.logger.info(f"{ColorFormat.AQUA}InventorySharePlugin is loaded!{ColorFormat.RESET}")

    def on_enable(self):
        self.logger.info(f"{ColorFormat.AQUA}InventorySharePlugin is enabled!{ColorFormat.RESET}")
        self.save_default_config()
        self.load_config()
        if not os.path.exists("plugins/inventory_share_plugin/config.toml"):
            self.logger.error("config.toml not found")
        self.register_events(self)

    def on_disable(self):
        self.logger.info(f"{ColorFormat.AQUA}InventorySharePlugin is disabled!{ColorFormat.RESET}")

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        self.logger.info("Join Events")
        target = event.player
        conn, cursor = connect_db(self.sql_host, self.sql_port, self.sql_user, self.sql_pass, self.sql_db_name)

        cursor.execute("SELECT player_inv FROM player_data WHERE player_xuid = %s", target.xuid)
        result = cursor.fetchone()

        if result:
            inventory_data = result[0]
            matches = re.findall(
                r'§eitem_slot:(-?\d+)\s+item:(\S+)\s+amount:(\d+)\s+name:(\S+)\s+lore:(None|\[.*?\])',
                inventory_data, re.DOTALL
            )

            inv = self.server.get_player(target.name).inventory
            inv.clear()
            for slot in ['helmet', 'chestplate', 'leggings', 'boots', 'item_in_off_hand']:
                setattr(inv, slot, ItemStack("minecraft:air", 1))

            for slot_str, item_type, amount, name, lore in matches:
                set_item_with_meta(inv, int(slot_str), item_type, int(amount), name, lore)

        cursor.close()
        conn.close()

    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent):
        target = event.player
        conn, cursor = connect_db(self.sql_host, self.sql_port, self.sql_user, self.sql_pass, self.sql_db_name)

        try:
            inv = self.server.get_player(target.name).inventory
            all_items = [get_item_data(inv.get_item(i), i) for i in range(36)]
            all_items += [get_item_data(getattr(inv, slot), idx) for idx, slot in zip(range(-1, -6, -1), ['helmet', 'chestplate', 'leggings', 'boots', 'item_in_off_hand'])]

            output = "".join(
                f"{'-'*20}\n{ColorFormat.YELLOW}item_slot:{i['num']} \n item:{i['item']} \n amount:{i['amount']} \n name:{i['name']} \n lore:{i['lore']} \n"
                for i in all_items
            )

            cursor.execute("UPDATE player_data SET player_inv = %s WHERE player_xuid = %s", (output, target.xuid))
            conn.commit()
            self.logger.info('Save inventory')

        except Exception as e:
            self.logger.error(f'Failed save inventory: {e}')

        cursor.close()
        conn.close()

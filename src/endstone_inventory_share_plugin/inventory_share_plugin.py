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
            'lore': item.item_meta.lore if item.item_meta.has_lore else "None",
            'damage': item.item_meta.damage if item.item_meta.has_damage else 0,
            'enchants': item.item_meta.enchants if item.item_meta.has_enchants else {}
        }
    return {
        'num': item_num,
        'item': "None",
        'amount': 0,
        'name': "None",
        'lore': "None",
        'damage': 0,
        'enchants': {}
    }


def connect_db(host, port, user, password, db_name):
    conn = pymysql.connect(host=host, port=int(port), user=user, password=password)
    cursor = conn.cursor()
    cursor.execute(f"USE {db_name}")
    return conn, cursor


def set_item_with_meta(inv, slot, item_type, amount, name, lore, damage, enchants):
    item = ItemStack(str(item_type), int(amount))

    if name != "None" or lore != "None" or damage != 0 or any(enchants):
        meta = item.item_meta
        if name != "None":
            meta.display_name = name
        if lore != "None":
            meta.lore = ast.literal_eval(lore)
        if damage != 0:
            meta.damage = damage
        if any(enchants):
            meta.enchants.clear()
            for enchant_key, level in enchants.items():
                meta.add_enchant(enchant_key, int(level), True)
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
    api_version = "0.7"

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

    def set_login_status(self, xuid, status: bool):
        # MySQLに接続
        conn, cursor = connect_db(self.sql_host,self.sql_port,self.sql_user,self.sql_pass,self.sql_db_name)

        cursor.execute("SELECT is_logged_in FROM player_data WHERE player_xuid = %s", xuid)
        result = cursor.fetchone()

        if result:
            cursor.execute("UPDATE player_data SET is_logged_in = %s WHERE player_xuid = %s", (str(status), xuid))
        else:
            cursor.execute("INSERT INTO player_data (player_xuid, is_logged_in) VALUES (%s, 'True')", xuid)

        conn.commit()
        conn.close()

    def get_login_status(self, xuid) -> bool:
        conn, cursor = connect_db(self.sql_host,self.sql_port,self.sql_user,self.sql_pass,self.sql_db_name)
        cursor.execute("SELECT is_logged_in FROM player_data WHERE player_xuid = %s", xuid)
        result = cursor.fetchone()
        conn.close()
        return result[0] == 1 if result else False

    def on_load(self):
        self.logger.info(f"{ColorFormat.AQUA}InventorySharePlugin is loaded!{ColorFormat.RESET}")

    def on_enable(self):
        self.logger.info(f"{ColorFormat.AQUA}InventorySharePlugin is enabled!{ColorFormat.RESET}")
        self.save_default_config()
        self.load_config()

        players = self.server.online_players

        for player in players:
            xuid = player.xuid
            self.set_login_status(xuid,True)

        if not os.path.exists("plugins/inventory_share_plugin/config.toml"):
            self.logger.error("config.toml not found")
        self.register_events(self)

    def on_disable(self):
        players = self.server.online_players

        for player in players:
            xuid = player.xuid
            self.set_login_status(xuid,False)

        self.logger.info(f"{ColorFormat.AQUA}InventorySharePlugin is disabled!{ColorFormat.RESET}")

    @event_handler
    def on_player_login(self, event: PlayerLoginEvent):
        self.logger.info("Login Events")
        target = event.player
        conn, cursor = connect_db(self.sql_host, self.sql_port, self.sql_user, self.sql_pass, self.sql_db_name)

        if self.get_login_status(target.xuid):
            target.kick("You cannot connect to the server from this device because another device is connected to the server.")
            return

        self.set_login_status(target.xuid, True)

        conn.commit()

        cursor.close()
        conn.close()

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        self.logger.info("Join Events")
        target = event.player
        self.set_login_status(target.xuid, False)
        conn, cursor = connect_db(self.sql_host, self.sql_port, self.sql_user, self.sql_pass, self.sql_db_name)

        cursor.execute("SELECT is_logged_in FROM player_data WHERE player_xuid = %s", (target.xuid,))
        result = cursor.fetchone()

        if result:
            cursor.execute("UPDATE player_data SET is_logged_in = 'True' WHERE player_xuid = %s", (target.xuid,))
        else:
            cursor.execute("INSERT INTO player_data (player_xuid, is_logged_in) VALUES (%s, 'True')", (target.xuid,))

        cursor.execute("SELECT player_inv FROM player_data WHERE player_xuid = %s", (target.xuid,))
        result = cursor.fetchone()

        if result and result[0]:
            inventory_data = result[0]
            matches = re.findall(
                r'§eitem_slot:(-?\d+)\s+item:(\S+)\s+amount:(\d+)\s+name:(\S+)\s+lore:(None|\[.*?\])\s+damage:(\d+)\s+enchants:({.*?})',
                inventory_data,
                re.DOTALL
            )

            inv = self.server.get_player(target.name).inventory
            inv.clear()
            for slot in ['helmet', 'chestplate', 'leggings', 'boots', 'item_in_off_hand']:
                setattr(inv, slot, ItemStack("minecraft:air", 1))

            for slot_str, item_type, amount, name, lore, damage, enchants_str in matches:
                if item_type == "None":
                    continue

                try:
                    enchants = ast.literal_eval(enchants_str)
                except Exception:
                    enchants = {}
                set_item_with_meta(inv, int(slot_str), item_type, int(amount), name, lore, int(damage), enchants)

        cursor.close()
        conn.close()

    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent):
        target = event.player
        if self.get_login_status(target.xuid):
            self.logger.info(f"{target.name} was kicked because they were connected to another server.")
            self.set_login_status(target.xuid, False)
            return
        else:
            conn, cursor = connect_db(self.sql_host, self.sql_port, self.sql_user, self.sql_pass, self.sql_db_name)
            cursor.execute("UPDATE player_data SET is_logged_in = 'False' WHERE player_xuid = %s", (target.xuid,))
            conn.commit()

            try:
                inv = self.server.get_player(target.name).inventory
                all_items = [get_item_data(inv.get_item(i), i) for i in range(36)]
                all_items += [get_item_data(getattr(inv, slot), idx) for idx, slot in zip(range(-1, -6, -1), ['helmet', 'chestplate', 'leggings', 'boots', 'item_in_off_hand'])]

                output = "".join(
                    f"{'-' * 20}\n"
                    f"{ColorFormat.YELLOW}item_slot:{i['num']} \n"
                    f" item:{i['item']} \n"
                    f" amount:{i['amount']} \n"
                    f" name:{i['name']} \n"
                    f" lore:{i['lore']} \n"
                    f" damage:{i['damage']} \n"
                    f" enchants:{i['enchants']} \n"
                    for i in all_items
                )

                cursor.execute("UPDATE player_data SET player_inv = %s WHERE player_xuid = %s", (output, target.xuid))
                conn.commit()
                self.logger.info('Save inventory')

            except Exception as e:
                self.logger.error(f'Failed save inventory: {e}')

            cursor.close()
            conn.close()
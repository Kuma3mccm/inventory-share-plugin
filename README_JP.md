# Inventory share plugin
[Endstone](https://github.com/EndstoneMC/endstone "Endstone")で使用できるSQLを使用した複数サーバー間でのインベントリ共有プラグインです。

[English](https://github.com/Kuma3mccm/inventory-share-plugin/blob/master/README.md)

​
初めてのプラグインなので最適化がされていないと思います。
​
## 使用方法
1. Endstoneのpluginsフォルダに[最新のリリース](https://github.com/Kuma3mccm/inventory-share-plugin/releases/latest)からダウンロードした実行ファイルを入れ、一度サーバーを起動します。
2. `plugins/inventory_share_plugin/config.toml`が生成されるので内容を自身で変更します。
3. `create_db.sql`を実行してデータベースとテーブルを作成します。
4. サーバーを再起動もしくはリロードします。
5. :partying_face: 

## 注意
このプラグインはまだ開発段階です。\
このプラグインを使用して発生したいかなる損失も責任を負いかねます。

## 実装予定
- [ ] エンダーチェストの内部を共有する。(1.4.0)

## 既知の問題
- NBTを必要とするアイテムはNBTが記録されません。

inventory-share-plugin by Kuma3mccm is licensed under the Apache License, Version2.0

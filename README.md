# Inventory share plugin
This is an inventory sharing plugin between multiple servers that uses SQL available in [Endstone](https://github.com/EndstoneMC/endstone "Endstone")

[日本語版](https://github.com/Kuma3mccm/inventory-share-plugin/blob/master/README_JP.md)

I think it isn't optimized because it's my first plugin.

## How to use
1. Put the executable file downloaded from the [latest release](https://github.com/Kuma3mccm/inventory-share-plugin/releases/latest) into the plugins folder of Endstone and start the server once.
2. Since`plugins/inventory_share_plugin/config.toml` is generated, I will change the content myself.
3. Execute `create_db.sql` to create a database and tables in SQL.
4. Restart or reload the server.
5. :partying_face: 

## Note 
This plugin is still in the development stage.\
We cannot be held responsible for any losses incurred from using this plugin. 
## Milestone
- [ ] Share the contents of the Ender Chest. (1.4.0)
## Known Issues 
- Items that require NBT do not record NBT.

inventory-share-plugin by Kuma3mccm is licensed under the Apache License, Version2.0

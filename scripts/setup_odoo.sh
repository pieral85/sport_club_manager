# /!\ This is a WIP /!\

# TODO Make a pull of the different Odoo repos (odoo, enterprise, themes, "custo")
odoo_odoo_dir=~/Documents/TFE/main
odoo_custom_dir=~/Documents/TFE/extra

# echo "$odoo_custom_dir"

ls "$odoo_custom_dir"

# find /home/pierre/Documents/TFE/extra -name "patches" -type d
find /home/pierre/Documents/TFE/extra -name "patches" -type d | while read -r pid ; do
    echo "Executing patch(es) in folder $pid"
    ls "$pid"
done

def migrate(cr, version):
    # Set noupdate property of "account.tax.template" records to False
    cr.execute("""UPDATE period SET active=true""")

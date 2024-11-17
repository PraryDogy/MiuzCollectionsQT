def get_stmt(self):

    q = sqlalchemy.select(
        THUMBS.c.src,
        THUMBS.c.hash_path,
        THUMBS.c.mod,
        THUMBS.c.coll,
        THUMBS.c.fav
        )

    q = q.limit(150)
    q = q.order_by(-THUMBS.c.mod)

    prod_stmt = THUMBS.c.src.not_ilike("%/PROCUCT/%")
    mod_stmt = THUMBS.c.src.not_ilike("%/MODEL/%")

    q = q.where(
        sqlalchemy.and_(sqlalchemy.or_(prod_stmt, mod_stmt))
        )

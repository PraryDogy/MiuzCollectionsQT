def get_values(full_src, full_hash, size, birth, mod, resol):
    return {
        "short_src": full_src,
        "short_hash": full_hash,
        "size": size,
        "birth": birth,
        "mod": mod,
        "resol": resol,
        "coll": full_src,
        "fav": 0,
        "brand": full_src
    }

a = get_values(*[None for i in range(0, 6)])
print(a)

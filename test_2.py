finder_images = [i for i in range(0, 50)]
del_images = [i for i in range(0, 10)]

if len(del_images) > len(finder_images) * 0.5:
    print("опасное удаление")

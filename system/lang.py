class Lng:
    months = [
        {
            "1": "Январь",
            "10": "Октябрь",
            "11": "Ноябрь",
            "12": "Декабрь",
            "2": "Февраль",
            "3": "Март",
            "4": "Апрель",
            "5": "Май",
            "6": "Июнь",
            "7": "Июль",
            "8": "Август",
            "9": "Сентябрь"
        },
        {
            "1": "January",
            "10": "October",
            "11": "November",
            "12": "December",
            "2": "February",
            "3": "March",
            "4": "April",
            "5": "May",
            "6": "June",
            "7": "July",
            "8": "August",
            "9": "September"
        }
    ]
    months_genitive_case = [
        {
            "1": "января",
            "10": "октября",
            "11": "ноября",
            "12": "декабря",
            "2": "февраля",
            "3": "марта",
            "4": "апреля",
            "5": "мая",
            "6": "июня",
            "7": "июля",
            "8": "августа",
            "9": "сентября"
        },
        {
            "1": "january",
            "10": "october",
            "11": "november",
            "12": "december",
            "2": "february",
            "3": "march",
            "4": "april",
            "5": "may",
            "6": "june",
            "7": "july",
            "8": "august",
            "9": "september"
        }
    ]
    weekdays = [
        {
            "0": "понедельник",
            "1": "вторник",
            "2": "среда",
            "3": "четверг",
            "4": "пятница",
            "5": "суббота",
            "6": "воскресенье"
        },
        {
            "0": "monday",
            "1": "tuesday",
            "2": "wednesday",
            "3": "thursday",
            "4": "friday",
            "5": "saturday",
            "6": "sunday"
        }
    ]
    weekdays_short = [
        {
            "0": "пн",
            "1": "вт",
            "2": "ср",
            "3": "чт",
            "4": "пт",
            "5": "сб",
            "6": "вс"
        },
        {
            "0": "mon",
            "1": "tue",
            "2": "wed",
            "3": "thu",
            "4": "fri",
            "5": "sat",
            "6": "sun"
        }
    ]
    file_size = ("Размер", "Size")
    info = ("Инфо", "Info")
    loading = ("Загрузка...", "Loading...")
    no_photo = ("Нет фотографий", "No photos")
    open_settings_window = ("Открыть настройки", "Open settings window")
    paste = ("Вставить", "Paste")
    place = ("Место", "Place")
    reload_gui = ("Обновить", "Update")
    reset = ("Сбросить", "Reset")
    resol = ("Разрешение", "Resolution")
    reveal_in_finder = ("Показать в Finder", "Reveal in Finder")
    save_to_downloads = ("Сохранить в загрузки", "Save to Downloads")
    save_as = ("Сохранить как", "Save as")
    search = ("Поиск", "Search")
    search_dates = (
        "Поиск фотографий по датам.\n"
        "Управляйте датами с клавишами вверх/вниз.",
        "Searching for photos by dates.\n"
        "Control dates with up/down keys."
    )
    settings = ("Настройки", "Settings")
    total = ("Всего", "Total")
    type_ = ("Тип", "Type")
    open = ("Открыть", "Open")
    recents = ("Недавние", "Recents")
    type_jpg = ("jpg, png", "jpg, png")
    type_tiff = ("tiff, psd", "tiff, psd")
    thumb_path = ("Данные", "Data")
    calculating = ("Вычисляю", "Calculating")
    delete = ("Удалить", "Remove")
    copy_name = ("Скопировать имя", "Copy filename")
    attention = ("Внимание!", "Warning!")
    delete_forever = ("Удалить безвозвратно файлы", "Delete forever files")
    theme_auto = ("Авто", "Auto")
    theme_dark = ("Темная", "Dark")
    theme_light = ("Светлая", "Light")
    start_date = ("Дата начала", "Start date")
    end_date = ("Дата окончания", "End date")
    move = ("Переместить", "Move files")
    drop_only_files = ("Можно загружать только файлы.", "Only files can be uploaded.")
    filters = ("Фильтры", "Filters")
    help = ("Справка", "Help")
    help_descr = ("Показать окно справки", "Show help window")
    back = ("Назад", "Back")
    next_ = ("Далее", "Next")
    read_file_error = ("Ошибка чтения файла", "Error file read")
    folders = ("Папки", "Folders")
    open_default = ("Открыть по умолчанию", "Open by default")
    open_in = ("Открыть в приложении", "Open in application")
    folder_name_immutable = (
        "Имя папки (нельзя изменить после сохранения)",
        "Folder name (cannot be changed after saving)"
    )
    save = ("Сохранить", "Save")
    new_folder = ("Новая папка", "New folder")
    enter_folder_name = ("Укажите имя папки с коллекциями", "Enter collections folder name")
    select_folder_path = ("Укажите путь к папке с коллекциями", "Select path to the collections folder")
    folder_path = ("Путь к папке с коллекциями", "Collections folder path")
    general = ("Основные", "General")
    restart = ("Перезапуск", "Restart")
    at_least_one_folder_required = (
        "Нужна хотя бы одна папка с коллекциями",
        "At least one collection folder required"
    )
    confirm_delete_folder = ("Вы уверены, что хотите удалить папку?", "Are you sure you want to delete the folder?")
    upload_path = ("Директория загрузки", "Upload path")
    collections = ("Коллекции", "Collections")
    upload = ("Загрузка", "Upload")
    collection = ("Коллекция", "Collection")
    images = ("Изображения", "Images")
    menu = ("Меню", "Menu")
    dates = ("Календарь", "Calendar")
    favorites = ("Избранное", "Favorites")
    cancel = ("Отмена", "Cancel")
    no_connection = ("Нет подключения", "No connection")
    no_connection_descr = (
        "- Подключитесь к диску с коллекциями\
        \n- Добавьте новый путь к коллекциям\
        \nв настройках.",
        "- Connect to disk with collections\
        \n- Add a new path to collections\
        \nin the settings."
    )
    ok = ("Ок", "Ok")
    folder_name = ("Имя папки", "Folder name")
    collections_folder_path = (
        "Путь к папке с коллекциями: перетащите сюда папку или укажите\n"
        "путь с новой строки.",
        "Path to the collections folder: drag a folder here or enter a path\n"
        "on a new line."
    )
    ignore_list_descr = (
        "Игнор лист: перетащите сюда папку или укажите имя с новой\n"
        "строки.",
        "Ignore list: drag a folder here or enter a name on a new line."
    )
    ignore_list = ("Игнор лист", "Ignore list")
    minutes = ("минут", "minutes")
    search_interval = ("Интервал поиска новых изображений", "Interval for checking new images")
    fast_image_search = ("Быстрый поиск изображений (бета)", "Fast image search (beta)")
    disable = ("Выключить", "Disable")
    enable = ("Включить", "Enable")
    show = ("Показать", "Show")
    show_system_files = ("Показать системные файлы в Finder", "Show system files in Finder")
    help_ = ("Помощь", "Help")
    show_help_window = ("Показать окно справки", "Show help window")
    russian = ("Русский", "English")
    language = ("Язык", "Language")
    reset_settings = ("Сбросить настройки", "Reset settings")
    copying = ("Копирование", "Copying")
    from_ = ("из", "from")
    in_ = ("в", "in")
    date_format = ("день.месяц.год", "day.month.year")
    copy = ("Копировать", "Copy")
    copy_all = ("Копировать все", "Copy all")
    add_to_favorites = ("Добавить в избранное", "Add to favorites")
    remove_from_favorites = ("Удалить из избранного", "Remove from favorites")
    copy_filepath = ("Скопировать путь", "Copy filepath")
    cut = ("Вырезать", "Cut")
    adding = ("Добавляю", "Add")
    deleting = ("Удаляю", "Deleting")
    search_in = ("Поиск в папке", "Search in folder")
    updating_folder = ("Обновление папки", "Updating folder")
    changed = ("Изменен", "Changed")
    file_name = ("Имя файла", "File name")
    show_about = ("Об авторе", "About")
    folder_name_error = ("Имя папки должно быть уникальным", "Folder name must be unique")
    name_taken = ("Уже занято", "Already taken")
    name = ("Имя", "Name")
    collection_folder = ("Папка с коллекциями", "Collections folder")
    image = ("Изображение", "Image")
    other_folders = ("Прочие папки", "Other folders")
    sort = ("Сорт.", "Sort")
    help_text = (
        "Папка с коллекциями:\n"
        "- Может содержать подпапки (коллекции)\n"
        "- Может содержать изображения без подпапок\n"
        "\n"
        "Фильтры:\n"
        "- Изображения в папке \"1 IMG\"\n"
        "- Изображения в папке \"2 MODEL IMG\"\n"
        "- Любые другие изображения (не в \"1 IMG\" и \"2 MODEL IMG\")",
        "Collection folder:\n"
        "- Can contain subfolders (collections)\n"
        "- Can contain images without subfolders\n"
        "\n"
        "Filters:\n"
        "- Images in \"1 IMG\" folder\n"
        "- Images in \"2 MODEL IMG\" folder\n"
        "- Any other images (not in \"1 IMG\" or \"2 MODEL IMG\")"
    )

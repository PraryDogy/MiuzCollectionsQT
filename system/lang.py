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
    months_gen = [
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
    paste = ("Вставить (⌘ + V)", "Paste (⌘ + V)")
    paste_objects = ("Вставить объекты (⌘ + V)", "Paste objects (⌘ + V)")
    place = ("Место", "Place")
    scan_folder = ("Искать изображения", "Find images")
    update_grid = ("Обновить", "Update")
    reset = ("Сбросить", "Reset")
    resol = ("Разрешение", "Resolution")
    reveal_in_finder = ("Показать в Finder", "Reveal in Finder")
    save_to_downloads = ("Сохранить в загрузки", "Save to Downloads")
    save_as = ("Сохранить как", "Save as")
    search = ("Поиск", "Search")
    search_dates = (
        "Поиск фотографий по датам.",
        "Searching for photos by dates."
    )
    settings = ("Настройки", "Settings")
    total = ("Всего", "Total")
    type_ = ("Тип", "Type")
    open = ("Открыть", "Open")
    recents = ("Недавние", "Recents")
    type_jpg = ("jpg, png", "jpg, png")
    type_tiff = ("tiff, psd", "tiff, psd")
    thumb_path = ("Данные", "Data")
    delete = ("Удалить", "Remove")
    copy_name = ("Скопировать имя", "Copy filename")
    copy_names = ("Скопировать имя объектов", "Copy object names")
    attention = ("Внимание!", "Warning!")
    delete_forever = ("Удалить безвозвратно файлы", "Delete forever files")
    theme_auto = ("Авто", "Auto")
    theme_dark = ("Темная", "Dark")
    theme_light = ("Светлая", "Light")
    start_date = ("Дата начала", "Start date")
    end_date = ("Дата окончания", "End date")
    cut = ("Вырезать (⌘ + X)", "Cut (⌘ + X)")
    drop_only_files = ("Можно загружать только файлы.", "Only files can be uploaded.")
    filters = ("Фильтры", "Filters")
    back = ("Назад", "Back")
    next_ = ("Далее", "Next")
    read_file_error = ("Ошибка чтения файла", "Error file read")
    folders = ("Папки", "Folders")
    folder = ("Папка", "Folder")
    open_default = ("Открыть по умолчанию", "Open by default")
    open_in = ("Открыть в приложении", "Open in application")
    alias_immutable = (
        "Имя (нельзя изменить после сохранения)",
        "Name (cannot be changed after saving)"
    )
    save = ("Сохранить", "Save")
    new_folder = ("Новая папка", "New folder")
    enter_alias_warning = (
        "Поле \"Имя\" обязательно для заполнения.",
        "Alias field is required."
    )
    select_folder_path = ("Укажите путь к папке с изображениями", "Select path to the images folder")
    folder_path = ("Путь к папке с изображениями", "Images folder path")
    general = ("Основные", "General")
    restart = ("Перезапуск", "Restart")
    at_least_one_folder_required = (
        "Нужна хотя бы одна папка с изображениями.",
        "At least one images folder required."
    )
    confirm_delete_folder = ("Вы уверены, что хотите удалить папку?", "Are you sure you want to delete the folder?")
    images = ("Изображения", "Images")
    menu = ("Меню", "Menu")
    dates = ("Календарь", "Calendar")
    favorites = ("Избранное", "Favorites")
    cancel = ("Отмена", "Cancel")
    no_connection = ("Нет подключения", "No connection")
    no_connection_full = ("Нет подключения к папке с изображениями.", "No connection to images folder.")
    folder_access_error = (
        "Не удалось получить доступ к папке с изображениями.\n"
        "Возможные причины:\n"
        "- Диск не подключён\n"
        "- Указанный путь недоступен\n\n"
        "Решение: откройте настройки и добавьте новый путь к папке с изображениями.",
        
        "Unable to access the images folder.\n"
        "Possible reasons:\n"
        "- Disk is not connected\n"
        "- The specified path is unavailable\n\n"
        "Solution: open settings and add a new path to the images folder."
    )
    ok = ("Ок", "Ok")
    alias = ("Имя", "Name")
    images_folder_path = (
        "Путь к папке с изображениями: перетащите сюда папку или укажите путь с новой строки.",
        "Path to the images folder: drag a folder here or enter a path on a new line."
    )
    ignore_list_descr = (
        "Игнор лист: перетащите сюда папку или укажите имя с новой строки.",
        "Ignore list: drag a folder here or enter a name on a new line."
    )
    ignore_list = ("Игнор лист", "Ignore list")
    minutes = ("минут", "minutes")
    search_interval = ("Интервал поиска новых изображений", "Interval for checking new images")
    fast_image_search = ("Быстрый поиск изображений (бета)", "Fast image search (beta)")
    disable = ("Выключить", "Disable")
    enable = ("Включить", "Enable")
    show = ("Показать", "Show")
    show_system_files = ("Системные файлы в Finder", "System files in Finder")
    russian = ("Русский", "English")
    language = ("Язык", "Language")
    language_max = ("Сменить язык (Change language)", "Change language (Сменить язык)")
    erase_data = ("Сбросить все данные", "Reset all data")
    copying = ("Копирование", "Copying")
    from_ = ("из", "from")
    in_ = ("в", "in")
    date_format = ("день.месяц.год", "day.month.year")
    copy = ("Копировать (⌘ + C)", "Copy (⌘ + C)")
    copy_all = ("Копировать все", "Copy all")
    add_to_favorites = ("Добавить в избранное", "Add to favorites")
    remove_from_favorites = ("Удалить из избранного", "Remove from favorites")
    copy_filepath = ("Скопировать путь", "Copy filepath")
    copy_filepaths = ("Скопировать путь до объектов", "Copy file paths to objects")
    adding = ("Добавляю", "Add")
    add = ("Добавить", "Add")
    deleting = ("Удаляю", "Deleting")
    search_in = ("Поиск в папке", "Search in folder")
    updating = ("Обновление", "Updating")
    changed = ("Изменен", "Changed")
    file_name = ("Имя файла", "File name")
    show_about = ("Об авторе", "About")
    alias_error = ("Имя должно быть уникальным", "Name must be unique")
    already_taken = ("Уже используется", "Is already taken")
    image = ("Изображение", "Image")
    other_folders = ("Прочие папки", "Other folders")
    sort_by_mod = ("По дате изменения", "Date modification")
    sort_by_recent = ("По дате добавления", "Date added")
    sort_by_mod_short = ("Дата изм.", "Date mod.")
    sort_by_recent_short = ("Дата доб.", "Date add.")
    reset_data = ("Сбросить данные", "Reset data")
    data_was_reset = (
        "Данные сброшены. Поиск изображений.",
        "Data reset. Searching images."
    )
    setup = ("Настроить", "Setup")
    preparing = ("Подготовка", "Preparing")
    on_ignore_list = ("В игнор листе", "on the ignore list")
    copy_name_same_dir = (
        "Копирование невозможно — файлы уже находятся в этой папке",
        "Copy operation not allowed — the files is already in this folder"
    )
    drop_event_denied_msg = (
        "Завершите поиск, затем перетащите файлы",
        "Finish the search, then drag the files"
    )
    save_text_long = (
        "Изменения сохранены. Приложение будет перезапущено.",
        "Changes saved. The application will restart."
    )
    save_new_folder = (
        "Сохраните и нажмите «Перезапуск», чтобы применить изменения.",
        "Save and press \"Restart\" to apply changes."
    )
    filters_descr = (
        "Фильтры:\n"
        "• Показывают файлы, путь которых содержит указанный текст.\n"
        "• Каждый фильтр вводится с новой строки.\n"
        "Пример:\n"
        "• Добавьте фильтр \".jpg\" и нажмите \"Сохранить\".\n"
        "• В приложении выберите фильтр \".jpg\" — будут показаны все .jpg файлы.",
        "Filters:\n"
        "• Show files whose path contains the specified text.\n"
        "• Enter each filter on a new line.\n"
        "Example:\n"
        "• Add the filter \".jpg\" and click \"Save\".\n"
        "• In the app, select the \".jpg\" filter — all .jpg files will be displayed."
    )
    all_images = ("Все изображения", "All images")
    only_this_folder = ("Показать только в этой папке", "Show only this folder")
    contents = ("Содержимое", "Contents")
    hide_digits = ("Скрывать нумерацию", "Hide numbering")
    expand_all = ("Развернуть всё", "Expand All")
    collapse_all = ("Свернуть всё", "Collapse All")
    forward = ("Вперед", "Forward")
    details = ("Подробнее", "Details")
    data_size = ("Размер данных", "Data size")
    calculating = ("Вычисление", "Calculating")
    reset_mf = (
        "Сбросить все данные папки.",
        "Reset all folder data ."
    )
    reset_mf_long = (
        "Кэшированные изображения будут удалены и созданы заново.",
        "Cached images will be deleted and recreated."
    )
    remove_folder = (
        "Удалить папку из приложения.",
        "Remove folder from app."
    )
    remove_folder_long = (
        "Все данные папки будут удалены. Исходные изображения сохранятся.",
        "All folder data will be deleted. Original images will remain intact."
    )
    reset_filters = (
        "Сбросить фильтры.",
        "Reset filters."
    )
    reset_filters_long = (
        "Фильтры будут сброшены к значениям по умолчанию.",
        "All filters will be reset to their default values.",
    )
    erase_data_long = (
        "Все кэшированные изображения будут удалены, а настройки приложения "
        "сброшены до значений по умолчанию",
        "All cached images will be deleted and app settings will be reset "
        "to defaults."
    )
    location = ("Расположение", "Location")
    modified = ("Изменен", "Modified")
    statistic = ("Статистика данных", "Data statistics")
    level_up = ("Наверх", "Level up")
    connect_to_server = ("Подключение к серверу (⌘ + K)", "Connect to server (⌘ + K)")
    connect = ("Подкл.", "Connect")
    server = ("Адрес сервера", "Server address")
    # server_favs = ("Избранные серверы", "Favorites")
    login = ("логин", "login")
    password = ("пароль", "password")
    upload_in = ("Загрузить в ...", "Upload in ...")
    upload_descr = (
        "Вы загрузите изображения в коллекции.\nНажмите Oк.",
        "You will upload images to collections.\nClick Ok."
    )
    swipe_text = ("\u2039 Проведите мышкой \u203A", "\u2039 Drag with mouse \u203A")
    rotate = ("Повернуть", "Rotate")
    clockwise = ("Повернуть по ч.с.", "Rotate cw")
    counter_clockwise = ("Повернуть против ч.с.", "Rotate ccw")

    replace = ("Замена", "Replace")
    replace_one = ("Заменить", "Replace")
    replace_all = ("Заменить все", "Replace all")
    stop = ("Стоп", "Stop")
    replace_existing_files = ("Заменить существующие файлы?", "Replace existing files?")
    copy_error = ("Произошла ошибка при копировании", "An error occurred while copying")
    error = ("Ошибка", "Error")
    next_search = ("Поиск новых изображений через", "Search new images in")
    string_limit = (
        "Имя — 5-30 символов.",
        "Name — up to 5-30 characters.",
    )
    valid_message = (
        "Имя может содержать только русские и английские буквы, "
        "цифры и пробелы.",
        "The name may contain only Russian and English letters, "
        "digits and spaces.",
    )
    folder_name = (
        "Имя:\n"
        "• уникальное\n"
        "• 5-30 символов\n"
        "• русские и английские буквы, цифры и пробелы",
        "Folder name:\n"
        "• unique\n"
        "• up to 5-30 characters\n"
        "• Russian and English letters, digits, and spaces",
    )
    folder_not_exists = (
        "Добавьте существующий путь к папке.",
        "Please provide an existing folder path.",
    )
    folder_path_exists = (
        "Папка с таким путем уже добавлена.\nИмя папки:",
        "A folder with this path has already been added.\nFolder name:",
    )
    first_load_title = (
        "Начальная настройка",
        ""
    )
    update_thumb = (
        "Обновить данные",
        "Update data"
    )
    advanced = (
        "Дополнительно",
        "Advanced"
    )

    selected_objects = (
        "Выделено объектов",
        "Selected objects"
    )
    edit = (
        "Редактировать",
        "Edit"
    )
    confirm_delete = (
        "Вы уверены, что хотите удалить данные этого сервера?",
        "Are you sure you want to delete this server's data?",
    )
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
        "Поиск фотографий по датам",
        "Searching for photos by dates"
    )
    settings = ("Настройки", "Settings")
    total = ("Всего", "Total")
    total_files = ("Всего файлов", "Total files")
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
    remove_file_question = ("Удалить безвозвратно файл", "Delete forever file")
    remove_files_question = ("Удалить безвозвратно файлы", "Delete forever files")
    macintosh_theme = ("Macintosh", "Macintosh")
    theme = ("Тема", "Theme")
    dark_theme = ("Темная", "Dark")
    light_theme = ("Светлая", "Light")
    start_date = ("Дата начала", "Start date")
    end_date = ("Дата окончания", "End date")
    cut = ("Вырезать (⌘ + X)", "Cut (⌘ + X)")
    drop_only_files = ("Можно загружать только файлы", "Only files can be uploaded")
    filters = ("Фильтры", "Filters")
    back = ("Назад", "Back")
    next_ = ("Далее", "Next")
    read_file_error = ("Ошибка чтения файла", "Error file read")
    catalogs = ("Каталоги", "Catalogs")
    folder = ("Каталог изображений", "Image catalog")
    open_default = ("Открыть по умолчанию", "Open by default")
    open_in = ("Открыть в приложении", "Open in application")
    alias_immutable = (
        "Имя (нельзя изменить после сохранения)",
        "Name (cannot be changed after saving)"
    )
    save = ("Сохранить", "Save")
    new_folder = ("Новый каталог", "New catalog")
    enter_alias_warning = (
        "Поле \"Имя\" обязательно для заполнения",
        "Alias field is required"
    )
    select_folder_path = (
        "Укажите путь к каталогу с изображениями",
        "Select path to the images catalog"
    )
    folder_path = ("Путь к каталогу", "Catalog path")
    general = ("Основные", "General")
    restart = ("Перезапуск", "Restart")
    at_least_one_folder_required = (
        "Нужен хотя бы один каталог с изображениями",
        "At least one image catalog is required"
    )
    images = ("Изображения", "Images")
    menu = ("Меню", "Menu")
    dates = ("Календарь", "Calendar")
    favorites = ("Избранное", "Favorites")
    cancel = ("Отмена", "Cancel")
    no_connection = ("Нет подключения", "No connection")
    no_connection_full = ("Нет подключения к каталогу", "No connection to the catalog")
    folder_access_error = (
        "Не удалось получить доступ к каталогу с изображениями.\n"
        "Возможные причины:\n"
        "- Диск не подключён\n"
        "- Указанный путь недоступен\n\n"
        "Решение: откройте настройки и добавьте новый путь к каталогу.",
        
        "Unable to access the images catalog.\n"
        "Possible reasons:\n"
        "- Disk is not connected\n"
        "- The specified path is unavailable\n\n"
        "Solution: open settings and add a new path to the catalog."
    )
    ok = ("Ок", "Ok")
    alias = ("Имя", "Name")
    images_folder_path = (
        "Путь к каталогу с изображениями: перетащите сюда папку или укажите путь с новой строки",
        "Path to the images catalog: drag a folder here or enter a path on a new line"
    )
    ignore_list_descr = (
        "Игнор лист: перетащите сюда папку или укажите имя с новой строки",
        "Ignore list: drag a folder here or enter a name on a new line"
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
    copy_file = ("Копировать файл (⌘ + C)", "Copy file (⌘ + C)")
    copy_files = ("Копировать файлы (⌘ + C)", "Copy files (⌘ + C)")
    copy = ("Cкопировать (⌘ + C)", "Copy (⌘ + C)")
    copy_all = ("Копировать все", "Copy all")
    add_to_favorites = ("Добавить в избранное", "Add to favorites")
    remove_from_favorites = ("Удалить из избранного", "Remove from favorites")
    copy_filepath = ("Скопировать путь к файлу", "Copy filepath")
    copy_dirpath = ("Скопировать путь", "Copy path")
    copy_filepaths = ("Скопировать путь к файлам", "Copy file paths to files")
    adding = ("Добавляю", "Add")
    add = ("Добавить", "Add")
    deleting = ("Удаляю", "Deleting")
    search_in = ("Поиск в каталоге", "Search in catalog")
    indexing = ("Индексация файлов", "Indexing files")
    changed = ("Изменен", "Changed")
    file_name = ("Имя файла", "File name")
    show_about = ("О приложении", "Аbout the app")
    alias_error = ("Имя должно быть уникальным", "Name must be unique")
    already_taken = (
        "Каталог с таким именем уже существует. Имя должно быть уникальным",
        "A directory with this name already exists. The name must be unique"
    )
    image = ("Изображение", "Image")
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
    hide_digits = ("Скрыть нумерацию", "Hide numbering")
    show_digits = ("Показать нумерацию", "Show numbering")
    show_digits_all = ("Показать нумерацию везде", "Show numbering everywhere")
    expand_all = ("Развернуть всё", "Expand All")
    collapse_all = ("Свернуть всё", "Collapse All")
    forward = ("Вперед", "Forward")
    details = ("Подробнее", "Details")
    data_size = ("Размер данных", "Data size")
    calculating = ("Вычисление", "Calculating")
    reset_mf = (
        "Исправить ошибки в каталоге",
        "Fix errors in the catalog"
    )
    app_will_restarted = (
        "Приложение будет перезапущено. Нажмите ок, чтобы продолжить.",
        "The application will restart. Click OK to continue."
    )
    remove_folder = (
        "Удалить каталог изображений",
        "Delete the image catalog"
    )
    reset_filters = (
        "Сбросить фильтры",
        "Reset filters"
    )
    reset_filters_long = (
        "Фильтры будут сброшены к значениям по умолчанию",
        "All filters will be reset to their default values",
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
    swipe_text = ("\u2039 Проведите мышкой \u203A", "\u2039 Drag with mouse \u203A")
    rotate = ("Повернуть", "Rotate")
    clockwise = ("Повернуть по ч.с. (⌘ + →)", "Rotate cw (⌘ + →)")
    counter_clockwise = ("Повернуть против ч.с. (⌘ + ←)", "Rotate ccw (⌘ + ←)")

    replace = ("Замена", "Replace")
    replace_one = ("Заменить", "Replace")
    replace_all = ("Заменить все", "Replace all")
    stop = ("Стоп", "Stop")
    replace_existing_files = ("Заменить существующие файлы?", "Replace existing files?")
    copy_error = ("Произошла ошибка при копировании", "An error occurred while copying")
    error = ("Ошибка", "Error")
    next_search = ("Поиск новых изображений через", "Search new images in")
    string_limit = (
        "Длина имени должна составлять от 5 до 30 символов",
        "The name length should be from 5 to 30 characters",
    )
    valid_message = (
        "Имя может содержать только русские и английские буквы, "
        "цифры и пробелы",
        "The name may contain only Russian and English letters, "
        "digits and spaces",
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
    first_load_title = (
        "Начальная настройка",
        ""
    )
    update_thumb = (
        "Обновить изображение",
        "Update image"
    )
    update_thumbs = (
        "Обновить изображения",
        "Update images"
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
    show_in_folder = (
        "Показать в коллекциях",
        "Show in collections"
    )
    set_server_alias = (
        "Задайте псевдоним",
        "Set an alias"
    )
    path_hint_texts = (
        "Перетащите каталог сюда или нажмите для выбора",
        "Drag and drop a catalog here or click to browse"
    )
    access_error_text = (
        "Нет доступа к каталогу изображений",
        "Unable to access the image directory"  # Более технически точно
    )
    network_error_text = (
        "Сетевой диск не подключен или неправильно указан путь.",
        "Network drive not connected or the path is incorrect."
    )
    hide_digits_full = (
        "Скрывает числовые префиксы только у папок первого уровня. Нумерация вложенных подпапок сохраняется.",
        "Hides numeric prefixes for top-level folders only. Numbering of nested subfolders remains unchanged."
    )
    bad_smb = (
        "Путь к каталогу изображений указан неверно.",
        "The image directory path is incorrect."
    )
    export_settings = (
        "Экспорт настроек",
        "Export settings"
    )
    import_settings = (
        "Импорт настроек",
        "Import settings"
    )
    export_full = (
        "Полная копия",
        "Full copy"
    )
    export_settings_only = (
        "Только настройки",
        "Settings only"
    )
    export_descr = (
        "Выберите вариант экспорта:"
        "\n- Только настройки — сохраняются настройки приложения, "
        "\nфильтры, данные серверов, каталоги изображений."
        "\n- Полный экспорт — дополнительно сохраняются"
        "\nкэшированные изображения.",

        "Choose an export option:"
        "\n• Export settings — saves application settings, filter lists, "
        "server data, and image directory lists."
        "\n• Full export — also includes cached images."
    )
    confirm_mf_path = (
        "Вы уверены, что правильно указали путь?"
        "\nНеправильный путь приведет к удалению всего каталога.",
        "Are you sure you specified the path correctly?"
        "\nAn incorrect path will result in the deletion of the entire directory.",
    )
    progress = (
        "Прогресс",
        "Progress"
    )
    image_search = (
        "Поиск изображений",
        "Image search"
    )
    start = (
        "Старт",
        "Start"
    )
    image_search_drop = (
        "Перетяните сюда цветное изображение",
        "Drop color image here"
    )
    close = (
        "Закрыть",
        "Close"
    )
    only_color = (
        "Поддерживаются только цветные изображения",
        "Only color images are supported"
    )
    accuracy = (
        "Точность",
        "Accuracy"
    )
    close_search = (
        "Закрыть поиск",
        "Close search"
    )
    upload_list = (
        "Список загружаемых файлов",
        "Upload list"
    )
    dest_folder = (
        "Целевая папка",
        "Destination folder"
    )
    allow = (
        "Разрешить",
        "Allow"
    )

    deny = (
        "Запретить",
        "Deny"
    )
    dangerous_text = (
        "Обнаружено опасное действие!\nВозможно, неверно указан путь к каталогу изображений.\nНажмите «Разрешить», чтобы продолжить, или «Запретить», чтобы указать правильный путь.",
        "Dangerous action detected!\nThe image directory path might be incorrect.\nClick \"Allow\" to continue, or \"Deny\" to specify the correct path."
    )

    sort_standart = (
        "Стандартная сортировка",
        "Default sorting"
    )
    sort_alphabet = (
        "Сортировка по алфавиту",
        "Alphabetical sorting"
    )

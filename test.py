Официального «красивого» списка всех внутренних имен (objectName) в одной таблице в документации Qt нет. Они разбросаны по примерам стилизации (Customizing Widgets) или спрятаны в исходном коде.
Вот полный список имен объектов внутри QCalendarWidget, который можно использовать для QSS:
Основные элементы (NavigationBar)
#qt_calendar_navigationbar — вся верхняя панель (контейнер).
#qt_calendar_prevmonth — кнопка «Предыдущий месяц» (стрелочка влево).
#qt_calendar_nextmonth — кнопка «Следующий месяц» (стрелочка вправо).
#qt_calendar_monthbutton — кнопка выбора месяца (текст с названием месяца).
#qt_calendar_yearbutton — кнопка выбора года (цифры года).
#qt_calendar_yearbutton (внутри QSpinBox) — если год выбирается через спинбокс.
Внутренние меню (при клике на месяц/год)
QMenu#qt_calendar_monthmenu — выпадающее меню со списком месяцев.
QSpinBox#qt_calendar_yearedit — поле ввода года (появляется при клике на год).
Сетка и заголовки (Body)
QAbstractItemView#qt_calendar_calendarview — основная таблица с числами.
#qt_calendar_calendarview QHeaderView — заголовки (дни недели сверху и номера недель слева).
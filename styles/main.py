class Themes:
    current = None

    @classmethod
    def set_theme(cls, name: str):
        with open(f"styles/{name}.css", mode="r", encoding="utf-8") as file:
            cls.current = file.read()


class Names:
    menu_btn = "menu_btn"
    menu_btn_bordered = "menu_btn_bordered"
    menu_btn_selected = "menu_btn_selected"
    menu_btn_selected_bordered = "menu_btn_selected_bordered"
    menu_scrollbar = "menu_scrollbar"
    menu_scrollbar_qwidget = "menu_scrollbar_qwidget"
    menu_fake_widget = "menu_fake_widget"

    topbar_btn = "topbar_btn"
    topbar_btn_selected = "topbar_btn_selected"
    topbar_btn_bordered = "topbar_btn_bordered"

    filter_bar_frame = "filter_bar_frame"

    thumbnail_normal = "thumbnail_normal"
    thumbnail_selected = "thumbnail_selected"
    th_reset_dates_btn = "th_reset_dates_btn"
    th_reset_search_btn = "th_reset_search_btn"
    th_reset_filters_btn = "th_reset_filters_btn"
    th_show_all_btn = "th_show_all_btn"
    th_title = "th_title"
    th_title_selected = "th_title_selected"
    th_scrollbar = "th_scrollbar"
    th_scroll_widget = "th_scroll_widget"

    st_bar_frame = "st_bar_frame"
    st_bar_jpg = "st_bar_jpg"
    st_bar_jpg_sel = "st_bar_jpg_sel"
    st_bar_tiff = "st_bar_tiff"
    st_bar_tiff_sel = "st_bar_tiff_sel"

    navi_zoom = "navi_zoom"
    navi_switch = "navi_switch"

    smb_browse_btn = "smb_browse_btn"
    smb_browse_btn_selected = "smb_browse_btn_selected"

    base_btn = "base_btn"
    base_input = "base_input"
    title_bar = "title_bar"
    central_widget = "central_widget"
    base_bottom_widget = "base_bottom_widget"
    separator = "separator"
    img_view_bg = "img_view_bg"

    up_btn = "up_btn"

    text_edit = "text_edit"

    progress = "progress"
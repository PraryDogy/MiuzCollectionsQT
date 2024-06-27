class Themes:
    current = None

    @staticmethod
    def set_theme(name: str):
        with open(f"styles/{name}.css", mode="r", encoding="utf-8") as file:
            Themes.current = file.read()


class Names:
    menu_btn = "menu_btn"
    menu_btn_bordered = "menu_btn_bordered"
    menu_btn_selected = "menu_btn_selected"
    menu_btn_selected_bordered = "menu_btn_selected_bordered"
    menu_scrollbar = "menu_scrollbar"
    menu_scrollbar_qwidget = "menu_scrollbar_qwidget"
    menu_fake_widget = "menu_fake_widget"

    dates_btn = "dates_btn"
    dates_btn_selected = "dates_btn_selected"
    dates_btn_bordered = "dates_btn_bordered"

    filter_btn = "filter_btn"
    filter_btn_selected = "filter_btn_selected"
    filter_bar_frame = "filter_bar_frame"

    thumbnail_normal = "thumbnail_normal"
    thumbnail_selected = "thumbnail_selected"
    th_reset_dates_btn = "th_reset_dates_btn"
    th_reset_search_btn = "th_reset_search_btn"
    th_reset_filters_btn = "th_reset_filters_btn"
    th_show_all_btn = "th_show_all_btn"
    th_title = "th_title"
    th_scrollbar = "th_scrollbar"
    th_scroll_widget = "th_scroll_widget"

    notification_widget = "notification_widget"
    notification_font_color = "notification_font_color"

    st_bar_frame = "st_bar_frame"
    st_bar_jpg = "st_bar_jpg"
    st_bar_jpg_sel = "st_bar_jpg_sel"
    st_bar_tiff = "st_bar_tiff"
    st_bar_tiff_sel = "st_bar_tiff_sel"

    btn_jpg = "btn_jpg"
    btn_jpg_selected = "btn_jpg_selected"
    btn_tiff = "btn_tiff"
    btn_tiff_selected = "btn_tiff_selected"

    navi_zoom = "navi_zoom"
    navi_switch = "navi_switch"

    info_base_label = "info_base_label"
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

    drop_widget = "drop_widget"
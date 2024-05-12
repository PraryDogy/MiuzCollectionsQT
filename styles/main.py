with open("styles/styles.css") as file:
    default_theme = file.read()

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


class Styles:
    big_radius = 8
    small_radius = 6
    title_font_size = "18pt"
    blue_color = "#2e59cb"
    btn_base_color = "#303030"

    base_bg_color = "#1e1e1e"
    base_radius = 10

    # context
    context_bg_color = "#333333"
    context_border_color = "#5d5d5d"

    # st_bar
    st_bar_bg_color = "#242424"
    st_bar_x_colr = "#303030"
    st_bar_sel = "#676767"

    # menu
    menu_w = 210
    menu_bg_color = "#333333"
    menu_sel_item_color = "#525252"

    # thumbnails
    thumbs_bg_color = "#1e1e1e"
    thumbs_item_w = 120
    thumbs_item_h = 28
    thumbs_up_color = "#333333"
    thumbs_item_color = "#303030"

    # topbar
    topbar_marg = (5, 0, 5, 0)
    topbar_bg_color = "#242424"
    topbar_item_w = 80
    topbar_item_h = 28
    topbar_items_space = 5
    topbar_search_bg = "#131313"


    # info win
    info_bg_color = "#1e1e1e"

    @staticmethod
    def get_scroll_style(color: str):
        return f"""
                QScrollBar:vertical {{
                    background-color: transparent;
                    width: 10px;
                    padding-right:2px;
                    padding-top: 2px;
                    padding-bottom: 2px;}}
                QScrollBar::handle:vertical {{
                    background-color: #525252;
                    border-radius: 4px;}}
                QScrollBar::handle:vertical:hover {{
                    background-color: #676767;
                    border-radius: 4px;}}
                QScrollBar::add-line:vertical {{
                    height: 0px;}}
                QScrollBar::sub-line:vertical {{
                    height: 0px;}}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    height: 0px;}}
                """

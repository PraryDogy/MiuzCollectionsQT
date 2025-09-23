# class FavItem(QTreeWidgetItem):
#     def __init__(self):
#         super().__init__([Lng.favorites[Cfg.lng]])
#         self.setData(0, Qt.ItemDataRole.UserRole, None)


# class TreeSep(QTreeWidgetItem):
#     def __init__(self):
#         super().__init__()
#         self.setDisabled(True)
#         self.setSizeHint(0, QSize(0, 10))
#         self.setData(0, Qt.ItemDataRole.UserRole, None)


# class TreeWid(QTreeWidget):
#     clicked_ = pyqtSignal(str)
#     no_connection = pyqtSignal(Mf)
#     update_grid = pyqtSignal()
#     restart_scaner = pyqtSignal()
#     hh = 25

#     def __init__(self):
#         super().__init__()
#         self.root_dir: str = None
#         self.last_dir: str = None
#         self.selected_path: str = None
#         self.setHeaderHidden(True)
#         self.setAutoScroll(False)
#         self.itemClicked.connect(self.on_item_click)

#     def init_ui(self, root_dir: str):
#         self.clear()
#         self.root_dir = root_dir
#         self.last_dir = root_dir

#         # верхние кастомные элементы
#         custom_item = FavItem()
#         custom_item.setSizeHint(0, QSize(0, self.hh))
#         self.insertTopLevelItem(0, custom_item)

#         sep = TreeSep()
#         self.insertTopLevelItem(1, sep)

#         # корневая директория
#         basename = os.path.basename(root_dir)
#         root_item = QTreeWidgetItem([basename])
#         root_item.setSizeHint(0, QSize(0, self.hh))
#         root_item.setData(0, Qt.ItemDataRole.UserRole, root_dir)
#         root_item.setToolTip(0, basename + "\n" + root_dir)
#         self.addTopLevelItem(root_item)

#         worker = SortedDirsLoader(root_dir)
#         worker.sigs.finished_.connect(
#             lambda data, item=root_item: self.add_children(item, data)
#         )
#         UThreadPool.start(worker)

#     def on_item_click(self, item: QTreeWidgetItem, col: int):
#         clicked_dir = item.data(0, Qt.ItemDataRole.UserRole)
#         if isinstance(item, TreeSep):
#             return
#         elif clicked_dir == self.last_dir:
#             return
#         elif isinstance(item, FavItem):
#             self.last_dir = clicked_dir
#             self.selected_path = clicked_dir
#             self.clicked_.emit(Static.NAME_FAVS)
#         else:
#             self.last_dir = clicked_dir
#             self.selected_path = clicked_dir
#             self.clicked_.emit(clicked_dir)
#             if item.childCount() == 0:
#                 worker = SortedDirsLoader(clicked_dir)
#                 worker.sigs.finished_.connect(
#                     lambda data, item=item: self.add_children(item, data)
#                 )
#                 UThreadPool.start(worker)
#             item.setExpanded(True)

#     def refresh_tree(self):
#         if not self.root_dir:
#             return
#         self.init_ui(self.root_dir)

#     def add_children(self, parent_item: QTreeWidgetItem, data: Dict[str, str]) -> None:
#         parent_item.takeChildren()
#         for path, name in data.items():
#             child: QTreeWidgetItem = QTreeWidgetItem([name])
#             child.setSizeHint(0, QSize(0, self.hh))
#             child.setData(0, Qt.ItemDataRole.UserRole, path)
#             child.setToolTip(0, name + "\n" + path)
#             parent_item.addChild(child)
#         parent_item.setExpanded(True)

#         if not self.selected_path:
#             return

#         paths = self.generate_path_hierarchy(self.selected_path)
#         if paths:
#             items = self.findItems(
#                 "*", Qt.MatchFlag.MatchRecursive | Qt.MatchFlag.MatchWildcard
#             )
#             for it in items:
#                 for x in paths:
#                     if it.data(0, Qt.ItemDataRole.UserRole) == x:
#                         self.setCurrentItem(it)
#                         break

#     def generate_path_hierarchy(self, full_path):
#         parts = []
#         path = full_path
#         while True:
#             parts.append(path)
#             parent = os.path.dirname(path)
#             if parent == path:  # достигли корня
#                 break
#             path = parent
#         return parts

#     def view(self, path: str):
#         self.clicked_.emit(path)

#     def reveal(self, path: str):
#         if os.path.exists(path):
#             subprocess.Popen(["open", path])
#         else:
#             self.no_connection.emit(Mf.current)

#     def contextMenuEvent(self, a0):
#         item = self.itemAt(a0.pos())
#         if item:
#             path: str = item.data(0, Qt.ItemDataRole.UserRole)

#             menu = UMenu(a0)
#             view = QAction(Lng.open[Cfg.lng], menu)
#             view.triggered.connect(
#                 lambda: self.view(path)
#             )
#             menu.addAction(view)

#             update_grid = QAction(Lng.update_grid[Cfg.lng], menu)
#             update_grid.triggered.connect(self.update_grid)
#             menu.addAction(update_grid)

#             restart_scaner = QAction(Lng.scan_folder[Cfg.lng], menu)
#             restart_scaner.triggered.connect(self.restart_scaner.emit)
#             menu.addAction(restart_scaner)

#             menu.addSeparator()

#             reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
#             reveal.triggered.connect(
#                     lambda: self.reveal(path)
#                 )
#             menu.addAction(reveal)

#             menu.show_umenu()
#         return super().contextMenuEvent(a0)
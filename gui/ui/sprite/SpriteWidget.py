from typing import List
from .AnimPropertiesWidget import AnimPropertiesWidgetUI
from PySide6 import QtCore, QtWidgets, QtGui


class SpriteWidgetUI(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(SpriteWidgetUI, self).__init__(*args, **kwargs)

        self.context_menu = QtWidgets.QMenu()

        self.v_layout = QtWidgets.QVBoxLayout()

        self.tab_widget = QtWidgets.QTabWidget()
        self.v_layout.addWidget(self.tab_widget, 4)

        self.images_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(self.images_tab, "Images")

        self.images_layout = QtWidgets.QVBoxLayout()

        self.image_list = QtWidgets.QListView()
        self.image_list.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self.image_list.setViewMode(QtWidgets.QListView.ViewMode.ListMode)
        self.image_list.setMovement(QtWidgets.QListView.Movement.Snap)
        self.image_list.setIconSize(QtCore.QSize(100, 100))
        self.image_list.setWrapping(False)
        self.image_list.setDragDropMode(QtWidgets.QListView.DragDropMode.InternalMove)
        self.image_list.setSelectionMode(QtWidgets.QListView.SelectionMode.SingleSelection)
        self.image_list.setAcceptDrops(True)
        self.image_list.setDragEnabled(True)
        self.image_list.setDropIndicatorShown(True)
        self.image_list.selectionChanged = self.image_list_selection_ui
        self.image_list.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self.image_list_context_menu)
        self.images_layout.addWidget(self.image_list, 1)

        self.image_view = QtWidgets.QLabel()
        self.image_view.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.images_layout.addWidget(self.image_view, 3)

        self.images_tab.setLayout(self.images_layout)

        self.animations_tab = QtWidgets.QWidget()
        self.anim_layout = QtWidgets.QVBoxLayout()

        self.anim_list = QtWidgets.QListView()
        self.anim_list.setFlow(QtWidgets.QListView.Flow.TopToBottom)
        self.anim_list.setViewMode(QtWidgets.QListView.ViewMode.ListMode)
        self.anim_list.setMovement(QtWidgets.QListView.Movement.Snap)
        self.anim_list.setWrapping(False)
        self.anim_list.setDragDropMode(QtWidgets.QListView.DragDropMode.InternalMove)
        self.anim_list.setSelectionMode(QtWidgets.QListView.SelectionMode.SingleSelection)
        self.anim_list.setAcceptDrops(True)
        self.anim_list.setDragEnabled(True)
        self.anim_list.setDropIndicatorShown(True)
        self.anim_list.selectionChanged = self.anim_change_selection_ui
        self.anim_list.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.anim_list.customContextMenuRequested.connect(self.anim_context_menu)
        self.anim_layout.addWidget(self.anim_list, 1)

        self.anim_data_tab = QtWidgets.QTabWidget()

        self.frame_edit_widget = QtWidgets.QWidget()
        self.frame_edit_layout = QtWidgets.QHBoxLayout()

        self.frame_list = QtWidgets.QListView()
        self.frame_list.setFlow(QtWidgets.QListView.Flow.TopToBottom)
        self.frame_list.setViewMode(QtWidgets.QListView.ViewMode.ListMode)
        self.frame_list.setIconSize(QtCore.QSize(100, 100))
        self.frame_list.setMovement(QtWidgets.QListView.Movement.Snap)
        self.frame_list.setWrapping(False)
        self.frame_list.setDragDropMode(QtWidgets.QListView.DragDropMode.InternalMove)
        self.frame_list.setSelectionMode(QtWidgets.QListView.SelectionMode.SingleSelection)
        self.frame_list.setAcceptDrops(True)
        self.frame_list.setDragEnabled(True)
        self.frame_list.setDropIndicatorShown(True)
        self.frame_list.selectionChanged = self.frame_change_selection_ui
        self.frame_list.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.frame_list.customContextMenuRequested.connect(self.frame_context_menu)
        self.frame_edit_layout.addWidget(self.frame_list, 1)

        self.frame_edit_data = QtWidgets.QWidget()
        self.frame_edit_data_layout = QtWidgets.QVBoxLayout()

        self.frame_preview = QtWidgets.QLabel()
        self.frame_edit_data_layout.addWidget(self.frame_preview)

        self.frame_properties_layout = QtWidgets.QGridLayout()

        self.frame_next_index_label = QtWidgets.QLabel("Next Index")
        self.frame_properties_layout.addWidget(self.frame_next_index_label, 0, 0)
        self.frame_next_index_input = QtWidgets.QSpinBox()
        self.frame_next_index_input.valueChanged.connect(self.frame_next_index_changed)
        self.frame_properties_layout.addWidget(self.frame_next_index_input, 0, 1)

        self.frame_image_index_label = QtWidgets.QLabel("Image Index")
        self.frame_properties_layout.addWidget(self.frame_image_index_label, 1, 0)
        self.frame_image_index_input = QtWidgets.QSpinBox()
        self.frame_image_index_input.valueChanged.connect(self.frame_image_index_changed)
        self.frame_properties_layout.addWidget(self.frame_image_index_input, 1, 1)

        self.frame_duration_label = QtWidgets.QLabel("Duration")
        self.frame_properties_layout.addWidget(self.frame_duration_label, 2, 0)
        self.frame_duration_input = QtWidgets.QSpinBox()
        self.frame_duration_input.valueChanged.connect(self.frame_duration_changed)
        self.frame_properties_layout.addWidget(self.frame_duration_input, 2, 1)

        self.frame_edit_data_layout.addLayout(self.frame_properties_layout)

        self.frame_edit_data.setLayout(self.frame_edit_data_layout)
        self.frame_edit_layout.addWidget(self.frame_edit_data, 1)
        self.frame_edit_data.hide()

        self.frame_edit_widget.setLayout(self.frame_edit_layout)
        self.anim_data_tab.addTab(self.frame_edit_widget, "Frames")

        self.anim_properties = self.get_anim_properties_widget()
        self.anim_data_tab.addTab(self.anim_properties, "Properties")

        self.anim_layout.addWidget(self.anim_data_tab, 2)

        self.animations_tab.setLayout(self.anim_layout)

        self.tab_widget.addTab(self.animations_tab, "Animations")

        self.variables_table = QtWidgets.QTableView()
        self.tab_widget.addTab(self.variables_table, "Variables")

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self.save_btn_click)
        self.v_layout.addWidget(self.save_btn, 1)

        self.setLayout(self.v_layout)

    def get_anim_properties_widget(self):
        return AnimPropertiesWidgetUI(self)

    def image_list_selection_ui(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        QtWidgets.QListView.selectionChanged(self.image_list, selected, deselected)
        if selected.indexes():
            self.image_list_selection(selected.indexes()[0])
        else:
            self.image_list_selection(QtCore.QModelIndex())

    def image_list_selection(self, selected: QtCore.QModelIndex):
        pass

    def image_list_context_menu(self, point: QtCore.QPoint):
        pass

    def save_btn_click(self):
        pass

    def anim_change_selection_ui(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        QtWidgets.QListView.selectionChanged(self.anim_list, selected, deselected)
        if selected.indexes():
            self.anim_change_selection(selected.indexes()[0])
        else:
            self.anim_change_selection(QtCore.QModelIndex())

    def anim_change_selection(self, selected: QtCore.QModelIndex):
        pass

    def anim_context_menu(self, point: QtCore.QPoint):
        pass

    def frame_change_selection_ui(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        QtWidgets.QListView.selectionChanged(self.anim_list, selected, deselected)
        if selected.indexes():
            self.frame_change_selection(selected.indexes()[0])
        else:
            self.frame_change_selection(QtCore.QModelIndex())

    def frame_change_selection(self, selected: QtCore.QModelIndex):
        pass

    def frame_context_menu(self, point: QtCore.QPoint):
        pass

    def frame_next_index_changed(self, value: int):
        pass

    def frame_image_index_changed(self, value: int):
        pass

    def frame_duration_changed(self, value: int):
        pass

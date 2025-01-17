from ..ui.BackgroundWidget import BackgroundWidgetUI
from formats.graphics.bg import BGImage


class BackgroundEditor(BackgroundWidgetUI):
    def __init__(self, *args, **kwargs):
        super(BackgroundEditor, self).__init__(*args, **kwargs)

    def set_image(self, bg_image: BGImage):
        self.image_preview.setPixmap(bg_image.extract_image_qt())

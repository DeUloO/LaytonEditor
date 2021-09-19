import pg_utils.sound.SADLStreamPlayer
import pg_utils.sound.SMDLStreamPlayer
from pg_utils.rom.rom_extract import load_sadl, load_smd


class EventSound:
    def __init__(self):
        self.sadl_player = pg_utils.sound.SADLStreamPlayer.SADLStreamPlayer()
        self.sadl_player.set_volume(0.5)
        self.bg_player = pg_utils.sound.SMDLStreamPlayer.SMDLStreamPlayer()
        self.bg_player.set_volume(0.5)
        self.loops = False

    def play_smdl(self, path):
        smd_obj, presets = load_smd(path)
        self.bg_player.set_preset_dict(presets)
        self.bg_player.start_sound(smd_obj)

    def stop_smdl(self):
        self.bg_player.stop()

    def play_sadl(self, path):
        sadl = load_sadl(path)
        self.sadl_player.start_sound(sadl, self.loops)

    def stop_sadl(self):
        self.sadl_player.stop()

    def update_(self, dt: float):
        self.sadl_player.update_(dt)
        self.bg_player.update_(dt)

    def fade(self, is_fade_in, frames):
        time = frames / 1000.0
        self.bg_player.fade(time, is_fade_in)
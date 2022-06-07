from pg_utils.rom.RomSingleton import RomSingleton
import formats.puzzle as pzd
from pg_utils.TwoScreenRenderer import TwoScreenRenderer
import pg_engine as pge
import pygame as pg

from pg_utils.rom.rom_extract import load_smd
from pg_utils.sound.SMDLStreamPlayer import SMDLStreamPlayer

from .PuzzleHints import PuzzleHints
from .PuzzleWinScreen import PuzzleWinScreen


class PuzzlePlayer(TwoScreenRenderer):
    def __init__(self, puzzle_data: pzd.Puzzle):
        super(PuzzlePlayer, self).__init__()

        self.text_pos = 0
        self.between_letters = 0.017
        self.current_between_letters = 0.0
        self.puzzle_data = puzzle_data

        self.inp = pge.Input()

        self.sprite_loader: pge.SpriteLoader = RomSingleton().get_sprite_loader()
        self.font_loader: pge.FontLoader = RomSingleton().get_font_loader()

        self.top_bg = pge.Sprite()
        self.sprite_loader.load(f"data_lt2/bg/nazo/system/nazo_text{puzzle_data.bg_location_id}.arc", self.top_bg,
                                sprite_sheet=False)

        self.btm_bg = pge.Sprite()
        if not puzzle_data.bg_lang:
            self.sprite_loader.load(f"data_lt2/bg/nazo/q{puzzle_data.internal_id}.arc", self.btm_bg, sprite_sheet=False)
        else:
            self.sprite_loader.load(f"data_lt2/bg/nazo/?/q{puzzle_data.internal_id}.arc", self.btm_bg,
                                    sprite_sheet=False)

        self.top_text = pge.Text(position=[-256//2 + 8, -192 // 2 + 23],
                                 center=[pge.Alignment.LEFT, pge.Alignment.TOP],
                                 color=pg.Color(0, 0, 0),
                                 line_spacing=2)
        self.font_loader.load("fontq", 10, self.top_text)

        self.header_top_left = []
        for i in range(4):
            header_item = pge.Sprite(center=[pge.Alignment.TOP, pge.Alignment.LEFT])
            self.sprite_loader.load(f"data_lt2/ani/nazo/system/?/nazo_text.arc", header_item, sprite_sheet=True)
            if i == 0:
                header_item.set_tag("nazo")
                header_item.position = [-256 // 2 + 5, -192 // 2 + 4]
            else:
                i -= 1
                p_num = puzzle_data.number
                for a in range(2 - i):
                    p_num //= 10
                header_item.set_tag(str(p_num % 10))
                header_item.position = [-256 // 2 + 23 + i * 7, -192 // 2 + 5]
            self.header_top_left.append(header_item)

        btn_off = "off"
        btn_on = "on"

        current_y = -192 // 2
        self.hints_btn = pge.Button(center=[pge.Alignment.RIGHT, pge.Alignment.TOP],
                                    position=[256 // 2, current_y], not_pressed_tag="0_off",
                                    pressed_tag="0_on")
        self.sprite_loader.load("data_lt2/ani/system/btn/?/hint.arc", self.hints_btn, sprite_sheet=True)

        current_y += self.hints_btn.get_world_rect().h
        self.quit_btn = pge.Button(center=[pge.Alignment.RIGHT, pge.Alignment.TOP],
                                   position=[256 // 2, current_y], not_pressed_tag=btn_off,
                                   pressed_tag=btn_on)
        self.sprite_loader.load("data_lt2/ani/system/btn/?/atode.arc", self.quit_btn, sprite_sheet=True)

        current_y += self.quit_btn.get_world_rect().h
        self.memo_btn = pge.Button(center=[pge.Alignment.RIGHT, pge.Alignment.TOP],
                                   position=[256//2, current_y], not_pressed_tag=btn_off,
                                   pressed_tag=btn_on)
        self.sprite_loader.load("data_lt2/ani/system/btn/?/memo.arc", self.memo_btn, sprite_sheet=True)

        self.submit_btn = pge.Button(center=[pge.Alignment.RIGHT, pge.Alignment.BOTTOM],
                                     position=[256//2, 192//2], not_pressed_tag=btn_off,
                                     pressed_tag=btn_on)
        self.sprite_loader.load("data_lt2/ani/system/btn/?/hantei.arc", self.submit_btn, sprite_sheet=True)

        self.hints = PuzzleHints(self.puzzle_data, self.sprite_loader, self.font_loader)
        self.on_hints = False

        smd, presets = load_smd("data_lt2/sound/BG_035.SMD")
        self.puzzle_bg_music = SMDLStreamPlayer()
        self.puzzle_bg_music.set_volume(0.5)
        self.puzzle_bg_music.set_preset_dict(presets)
        self.puzzle_bg_music.start_sound(smd, loops=True)

        self.win_screen = PuzzleWinScreen(self.puzzle_data, self.sprite_loader, self.font_loader, self.hints,
                                          self.puzzle_bg_music)
        self.on_win = False

        self.run_gds()

    def run_gds_cmd(self, cmd):
        pass

    def run_gds(self):
        for cmd in self.puzzle_data.gds.commands:
            self.run_gds_cmd(cmd)

    def solution_submitted(self, dt):
        if self.submit_btn.pressed(self.btm_camera, dt):
            return True
        return False

    def check_solution(self):
        return self.inp.get_key(pg.K_y)

    def unload(self):
        self.puzzle_bg_music.stop()

    def update(self, dt: float):
        self.puzzle_bg_music.update(dt)

        if self.on_hints:
            self.on_hints = self.hints.update(dt)
            if not self.on_hints:
                self.hints_btn.not_pressed_tag = f"{self.hints.used}_off"
                self.hints_btn.pressed_tag = f"{self.hints.used}_on"
        elif self.on_win:
            self.hints_btn.animate(dt)
            self.quit_btn.animate(dt)
            self.memo_btn.animate(dt)
            self.submit_btn.animate(dt)
            self.on_win = self.win_screen.update(dt)
        else:
            self.update_base(dt)

    def update_base(self, dt: float):
        self.hints_btn.animate(dt)
        self.quit_btn.animate(dt)
        self.memo_btn.animate(dt)
        self.submit_btn.animate(dt)

        if self.text_pos < len(self.puzzle_data.text):
            self.current_between_letters += dt
            while self.current_between_letters > self.between_letters:
                self.text_pos += 1
                self.current_between_letters -= self.between_letters
            if self.inp.get_mouse_down(1):
                self.text_pos = len(self.puzzle_data.text)
            self.text_pos = min(self.text_pos, len(self.puzzle_data.text))
            self.top_text.text = self.puzzle_data.text[:self.text_pos]
            return

        if self.hints_btn.pressed(self.btm_camera, dt):
            self.hints.view_hint(min(2, self.hints.used))
            self.on_hints = True
            return
        self.quit_btn.pressed(self.btm_camera, dt)
        self.memo_btn.pressed(self.btm_camera, dt)
        if self.solution_submitted(dt):
            self.win_screen.enter(self.check_solution())
            self.on_win = True
            self.puzzle_bg_music.fade(1, False)

    def draw(self):
        self.top_bg.draw(self.top_camera)
        for header in self.header_top_left:
            header.draw(self.top_camera)
        self.top_text.draw(self.top_camera)

        if self.on_hints:
            self.hints.draw()
        elif self.on_win:
            self.draw_base()
            self.win_screen.draw()
        else:
            self.draw_base()

    def draw_base(self):
        self.btm_bg.draw(self.btm_camera)
        self.hints_btn.draw(self.btm_camera)
        self.quit_btn.draw(self.btm_camera)
        self.memo_btn.draw(self.btm_camera)
        self.submit_btn.draw(self.btm_camera)

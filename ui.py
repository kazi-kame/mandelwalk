import pygame
import pygame_gui
from config import (
    DASHBOARD_RESOLUTION,
    ZOOM_SPEED_MIN, ZOOM_SPEED_MAX,
    ZOOM_TARGETS, MAX_FRAMES, MIN_DURATION_SECONDS
)

class UIManager:
    def __init__(self, screen):
        self.screen = screen
        self.W, self.H = DASHBOARD_RESOLUTION
        self.manager = pygame_gui.UIManager(DASHBOARD_RESOLUTION)

        # theme colors (subtle dark + accent)
        self.bg_color = (18, 20, 24)
        self.accent = (80, 200, 120)

        # defaults
        self.is_playing = False
        self.zoom_speed = 1.05
        self.duration = 20
        self.colormap = "inferno"
        self.fps = 60
        self.target = "seahorse_valley"

        # layout helpers (center-aligned columns)
        center_x = self.W // 2
        left_col_x = center_x - 320
        right_col_x = center_x + 40
        title_w = 600

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((center_x - title_w // 2, 30), (title_w, 40)),
            text="Mandelbrot Zoom Simulator",
            manager=self.manager,
        )

        # Zoom speed
        self.zoom_speed_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((left_col_x, 110), (520, 30)),
            text=f"Zoom Speed: {self.zoom_speed:.3f}",
            manager=self.manager,
        )
        self.zoom_speed_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((left_col_x, 145), (520, 30)),
            start_value=(self.zoom_speed - ZOOM_SPEED_MIN) / (ZOOM_SPEED_MAX - ZOOM_SPEED_MIN),
            value_range=(0.0, 1.0),
            manager=self.manager,
        )

        # FPS
        self.fps_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((left_col_x, 205), (520, 30)),
            text=f"Frame Rate: {self.fps} FPS",
            manager=self.manager,
        )
        self.fps_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((left_col_x, 240), (520, 30)),
            start_value=(self.fps - 24) / (120 - 24),
            value_range=(0.0, 1.0),
            manager=self.manager,
        )

        # Duration (frame-capped by FPS)
        self.duration_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((left_col_x, 300), (520, 30)),
            text="",
            manager=self.manager,
        )
        self.duration_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((left_col_x, 335), (520, 30)),
            start_value=1.0,
            value_range=(0.0, 1.0),
            manager=self.manager,
        )

        # Colormap
        self.colormap_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((right_col_x, 110), (240, 30)),
            text=f"Colormap: {self.colormap}",
            manager=self.manager,
        )
        self.colormap_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=["inferno", "electric", "lava", "ice", "gold", "psychedelic"],
            starting_option=self.colormap,
            relative_rect=pygame.Rect((right_col_x, 145), (240, 40)),
            manager=self.manager,
        )

        # Target
        self.target_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((right_col_x, 220), (240, 30)),
            text=f"Zoom Target: {self.target.replace('_', ' ').title()}",
            manager=self.manager,
        )
        self.target_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=list(ZOOM_TARGETS.keys()),
            starting_option=self.target,
            relative_rect=pygame.Rect((right_col_x, 255), (240, 40)),
            manager=self.manager,
        )

        # Play
        self.play_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((center_x - 100, self.H - 110), (200, 50)),
            text="Start Navigator",
            manager=self.manager,
        )

        self._sync_duration_from_slider()

    def _max_duration_for_fps(self):
        return max(MIN_DURATION_SECONDS, MAX_FRAMES / max(1, self.fps))

    def _sync_duration_from_slider(self):
        max_dur = self._max_duration_for_fps()
        self.duration = int(round(MIN_DURATION_SECONDS + self.duration_slider.get_current_value() * (max_dur - MIN_DURATION_SECONDS)))
        self.duration = max(MIN_DURATION_SECONDS, min(int(max_dur), self.duration))
        self.duration_label.set_text(f"Duration: {self.duration}s (max at {self.fps} FPS)")
        est_frames = self.duration * self.fps
        if est_frames > MAX_FRAMES:
            self.duration = int(MAX_FRAMES // self.fps)
            self.duration = max(MIN_DURATION_SECONDS, self.duration)
            self.duration_label.set_text(f"Duration: {self.duration}s (max at {self.fps} FPS)")

    def process_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.play_button:
            self.is_playing = True

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.zoom_speed_slider:
                self.zoom_speed = ZOOM_SPEED_MIN + event.value * (ZOOM_SPEED_MAX - ZOOM_SPEED_MIN)
                self.zoom_speed_label.set_text(f"Zoom Speed: {self.zoom_speed:.3f}")

            elif event.ui_element == self.fps_slider:
                # 24..120 FPS
                self.fps = int(round(24 + event.value * (120 - 24)))
                self.fps = max(24, min(120, self.fps))
                self.fps_label.set_text(f"Frame Rate: {self.fps} FPS")
                self._sync_duration_from_slider()

            elif event.ui_element == self.duration_slider:
                self._sync_duration_from_slider()

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.colormap_dropdown:
                self.colormap = event.text
                self.colormap_label.set_text(f"Colormap: {self.colormap}")
            elif event.ui_element == self.target_dropdown:
                self.target = event.text
                self.target_label.set_text(f"Zoom Target: {self.target.replace('_', ' ').title()}")

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self):
        self.screen.fill(self.bg_color)
        self.manager.draw_ui(self.screen)

    def get_play_state(self):
        return self.is_playing

    def get_all_settings(self):
        return {
            "zoom_factor": self.zoom_speed,
            "duration": self.duration,
            "colormap": self.colormap,
            "fps": self.fps,
            "target": self.target,
        }
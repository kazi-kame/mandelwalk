import pygame
import pygame_gui
from config import WIDTH, HEIGHT, REGIONS, COLORMAPS
from config import HEIGHT_SCALE_DEFAULT, HEIGHT_SCALE_MIN, HEIGHT_SCALE_MAX
from config import FALL_DEPTH_MIN, FALL_DEPTH_MAX, VOID, ADVANCED_DEFAULTS
from config import WORLD_SCALE_MIN, WORLD_SCALE_MAX

W, H = WIDTH, HEIGHT
CX   = W // 2


class Dashboard:
    def __init__(self, screen):
        self.screen  = screen
        self.manager = pygame_gui.UIManager((W, H))
        self._build()
        self.ready   = False

        self.region              = "seahorse_valley"
        self.colormap            = "inferno"
        self.speed               = 0.8
        self.fov                 = 75.0
        self.height_scale        = HEIGHT_SCALE_DEFAULT
        self.fall_depth          = VOID["fall_depth"]
        self.eye_height          = ADVANCED_DEFAULTS["eye_height"]
        self.slab_thickness      = ADVANCED_DEFAULTS["slab_thickness"]
        self.world_scale         = ADVANCED_DEFAULTS["world_scale"]
        self.ground_follow_speed = ADVANCED_DEFAULTS["ground_follow_speed"]

    def _build(self):
        col_l = CX - 480
        col_r = CX + 80
        label_h = 24
        ctrl_h  = 34

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((CX - 180, 20), (360, 42)),
            text="MandelWalk",
            manager=self.manager,
        )
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((CX - 220, 58), (440, 24)),
            text="Walk the boundary. Fall into the void.",
            manager=self.manager,
        )

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_l, 100), (200, label_h)),
            text="Region",
            manager=self.manager,
        )
        self.region_desc = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_l, 166), (420, label_h)),
            text=REGIONS["seahorse_valley"]["description"],
            manager=self.manager,
        )
        self.region_drop = pygame_gui.elements.UIDropDownMenu(
            options_list=[v["label"] for v in REGIONS.values()],
            starting_option=REGIONS["seahorse_valley"]["label"],
            relative_rect=pygame.Rect((col_l, 128), (420, ctrl_h)),
            manager=self.manager,
        )
        self._region_label_map = {v["label"]: k for k, v in REGIONS.items()}

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_r, 100), (220, label_h)),
            text="Colormap",
            manager=self.manager,
        )
        self.cmap_drop = pygame_gui.elements.UIDropDownMenu(
            options_list=COLORMAPS,
            starting_option="inferno",
            relative_rect=pygame.Rect((col_r, 128), (300, ctrl_h)),
            manager=self.manager,
        )

        self.speed_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_l, 216), (420, label_h)),
            text="Movement Speed:  0.80",
            manager=self.manager,
        )
        self.speed_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((col_l, 244), (420, ctrl_h)),
            start_value=0.8,
            value_range=(0.1, 5.0),
            manager=self.manager,
        )

        self.fov_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_r, 216), (300, label_h)),
            text="FOV:  75°",
            manager=self.manager,
        )
        self.fov_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((col_r, 244), (300, ctrl_h)),
            start_value=75.0,
            value_range=(45.0, 110.0),
            manager=self.manager,
        )

        self.hscale_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_l, 300), (420, label_h)),
            text=f"Cliff Height:  {HEIGHT_SCALE_DEFAULT:.2f}",
            manager=self.manager,
        )
        self.hscale_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((col_l, 328), (420, ctrl_h)),
            start_value=HEIGHT_SCALE_DEFAULT,
            value_range=(HEIGHT_SCALE_MIN, HEIGHT_SCALE_MAX),
            manager=self.manager,
        )

        self.fall_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_r, 300), (300, label_h)),
            text=f"Void Depth:  {VOID['fall_depth']:.0f}",
            manager=self.manager,
        )
        self.fall_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((col_r, 328), (300, ctrl_h)),
            start_value=VOID["fall_depth"],
            value_range=(FALL_DEPTH_MIN, FALL_DEPTH_MAX),
            manager=self.manager,
        )

        self.eye_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_l, 384), (420, label_h)),
            text=f"Eye Height:  {ADVANCED_DEFAULTS['eye_height']:.2f}",
            manager=self.manager,
        )
        self.eye_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((col_l, 412), (420, ctrl_h)),
            start_value=ADVANCED_DEFAULTS["eye_height"],
            value_range=(0.03, 0.45),
            manager=self.manager,
        )

        self.slab_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_r, 384), (300, label_h)),
            text=f"Slab Thickness:  {ADVANCED_DEFAULTS['slab_thickness']:.2f}",
            manager=self.manager,
        )
        self.slab_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((col_r, 412), (300, ctrl_h)),
            start_value=ADVANCED_DEFAULTS["slab_thickness"],
            value_range=(0.05, 1.8),
            manager=self.manager,
        )

        self.scale_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_l, 468), (420, label_h)),
            text=f"World Scale:  {ADVANCED_DEFAULTS['world_scale']:.2f}",
            manager=self.manager,
        )
        self.scale_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((col_l, 496), (420, ctrl_h)),
            start_value=ADVANCED_DEFAULTS["world_scale"],
            value_range=(WORLD_SCALE_MIN, WORLD_SCALE_MAX),
            manager=self.manager,
        )

        self.gfollow_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((col_r, 468), (300, label_h)),
            text=f"Ground Follow:  {ADVANCED_DEFAULTS['ground_follow_speed']:.1f}",
            manager=self.manager,
        )
        self.gfollow_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((col_r, 496), (300, ctrl_h)),
            start_value=ADVANCED_DEFAULTS["ground_follow_speed"],
            value_range=(4.0, 24.0),
            manager=self.manager,
        )

        self.enter_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((CX - 130, 616), (260, 48)),
            text="Enter the Set",
            manager=self.manager,
        )

    def process_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.enter_btn:
                self.ready = True

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.region_drop:
                key = self._region_label_map[event.text]
                self.region = key
                self.region_desc.set_text(REGIONS[key]["description"])
            elif event.ui_element == self.cmap_drop:
                self.colormap = event.text

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.speed_slider:
                self.speed = event.value
                self.speed_label.set_text(f"Movement Speed:  {self.speed:.2f}")
            elif event.ui_element == self.fov_slider:
                self.fov = event.value
                self.fov_label.set_text(f"FOV:  {self.fov:.0f}°")
            elif event.ui_element == self.hscale_slider:
                self.height_scale = event.value
                self.hscale_label.set_text(f"Cliff Height:  {self.height_scale:.2f}")
            elif event.ui_element == self.fall_slider:
                self.fall_depth = event.value
                self.fall_label.set_text(f"Void Depth:  {self.fall_depth:.0f}")
            elif event.ui_element == self.eye_slider:
                self.eye_height = event.value
                self.eye_label.set_text(f"Eye Height:  {self.eye_height:.2f}")
            elif event.ui_element == self.slab_slider:
                self.slab_thickness = event.value
                self.slab_label.set_text(f"Slab Thickness:  {self.slab_thickness:.2f}")
            elif event.ui_element == self.scale_slider:
                self.world_scale = event.value
                self.scale_label.set_text(f"World Scale:  {self.world_scale:.2f}")
            elif event.ui_element == self.gfollow_slider:
                self.ground_follow_speed = event.value
                self.gfollow_label.set_text(f"Ground Follow:  {self.ground_follow_speed:.1f}")

    def update(self, dt):
        self.manager.update(dt)

    def draw(self):
        self.manager.draw_ui(self.screen)

    def get_settings(self):
        return {
            "region":              self.region,
            "colormap":            self.colormap,
            "speed":               self.speed,
            "fov":                 self.fov,
            "height_scale":        self.height_scale,
            "fall_depth":          self.fall_depth,
            "eye_height":          self.eye_height,
            "slab_thickness":      self.slab_thickness,
            "world_scale":         self.world_scale,
            "ground_follow_speed": self.ground_follow_speed,
        }
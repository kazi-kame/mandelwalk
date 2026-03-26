import pygame
import sys
from ui import Dashboard
from config import WIDTH, HEIGHT, FPS, TITLE, VOID

def run_dashboard():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    ui    = Dashboard(screen)

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            else:
                ui.process_events(event)

        ui.update(dt)
        screen.fill((18, 18, 23))
        ui.draw()
        pygame.display.flip()

        if ui.ready:
            settings = ui.get_settings()
            settings["water_y"] = VOID["water_y"]
            pygame.display.quit()
            return settings
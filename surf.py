import pygame, math, pygame.freetype


def append_surfs(surf1, surf2, spacing=0, vertical=False):
    if vertical:
        surf = pygame.Surface((max(surf1.get_width(), surf2.get_width()), surf1.get_height() + surf2.get_height() + spacing),
                              pygame.SRCALPHA)

        surf.blit(surf1, (0, 0))
        surf.blit(surf2, (0, surf1.get_height() + spacing))
    else:
        surf = pygame.Surface((surf1.get_width() + surf2.get_width() + spacing, max(surf1.get_height(), surf2.get_height())),
                              pygame.SRCALPHA)

        surf.blit(surf1, (0, 0))
        surf.blit(surf2, (surf1.get_width() + spacing, 0))
    return surf


# Font loading
fonts = {
    "l": pygame.freetype.Font("font/nasalization-rg.otf", 72),
    "m": pygame.freetype.Font("font/nasalization-rg.otf", 36),
    "s": pygame.freetype.Font("font/nasalization-rg.otf", 18)
}

def generate_text(string, color=(255, 255, 255), size="s", spacing=0):
    if "\n" in string:
        return append_surfs(
            generate_text(string[0: string.find("\n")], color, size, spacing),
            generate_text(string[string.find("\n") + 1:], color, size, spacing),
            spacing,
            True
        )
    return fonts[size].render(string, color)[0]

def change_surf_color(rgb, surf):
    for x in range(surf.get_width()):
        for y in range(surf.get_height()):
            rgba = surf.get_at((x, y))
            if rgba[3] > 0:
                surf.set_at((x, y), (*rgb, rgba[3]))
    return surf


def generate_circle_surf(diameter, color):
    surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    surf.fill(color)

    surf_center = pygame.Vector2(diameter // 2, diameter // 2)
    max_dist = diameter // 2

    for x in range(diameter):
        for y in range(diameter):
            r, g, b = surf.get_at((x, y))[0:3]
            if r or g or b:
                dist = (pygame.Vector2(x, y) - surf_center).magnitude()
                if dist <= max_dist:
                    a = 255
                elif math.floor(dist) <= max_dist:
                    a = int((1 - dist + max_dist) * 255)
                else:
                    a = 0
                surf.set_at((x, y), (r, g, b, a))
    return surf

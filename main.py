# main.py
# Ben Morrison

import pygame, math, pygame.gfxdraw, pygame.freetype
from random import randint, random, random as ran
from pygame import Vector2
from pprint import pprint as pp

# Pygame setup and application stuff

game_name = "SolarSim"
pygame.init()
display, clock = pygame.display.Info(), pygame.time.Clock()
width, height = display.current_w, display.current_h
center_x, center_y = width // 2, height // 2
center = pygame.Vector2(center_x, center_y)
win = pygame.display.set_mode((width, height))
pygame.display.set_caption(game_name)
pressed, mods = pygame.key.get_pressed, pygame.key.get_mods

# Have to do this after initializing pygame
import surf

# Circle stuff
body_circle = surf.generate_circle_surf(511, (255, 0, 255))

class Camera:
    def __init__(self, position, scale, tracking=None):
        self.position = Vector2(position)
        self._scale = scale
        self.tracking = tracking

        self.shake_vector = Vector2()
        self.shake_amount = 0

    def tick(self, delta):
        if self.shake_amount:
            print("shaking")
            self.shake_amount = max(self.shake_amount - delta * self.shake_amount, 1)
        if self.tracking:
            self.position = Vector2(self.tracking.position)

    def world_position(self, position: Vector2):
        return (position - center) / self._scale + self.position

    def render_position(self, position: Vector2, ignore_translation=False):

        angle = random() * 2 * math.pi
        shake = self.shake_amount * Vector2(math.cos(angle), math.sin(angle))

        position = (position - self.position) * self._scale + center + shake

        return Vector2(position.x, position.y)

    def get_scale(self):
        return self._scale

    def scale(self, num):
        return num * self._scale

    def change_scale(self, increase):
        if increase:
            self._scale *= 2
        else:
            self._scale *= (1/2)

    def shake(self, force: float):
        self.shake_amount += math.sqrt(force) ** 2

class Body:
    def __init__(self, position, velocity, mass, bodies, uuid=None, skip_surf_gen=False):
        self.uuid = uuid
        if self.uuid is None:
            self.uuid = "".join(["abcdefghijklmnopqrstuvwxyz"[randint(0, 25)] for _ in range(5)])

        self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        self.ghosted = False

        self._velocity = self.velocity
        self._position = self.position

        self.mass = mass
        self.radius = math.sqrt(mass / math.pi) * 100

        self.name_surf = surf.generate_text(self.uuid)

        self.bodies = bodies  # Pointer to the bodies list

    def tick(self, delta):
        net_force = Vector2()
        collided = None
        for body in self.bodies:
            dir_vec = body.position - self.position
            if not (self.ghosted or body.ghosted) and body != self and dir_vec.magnitude() < (self.radius + body.radius):
                collided = body
                body.ghosted = True
                self.ghosted = True

            if body != self and dir_vec:
                # print(dir_vec.magnitude())
                net_force += dir_vec.normalize() * (6.67e3 * 2) * body.mass / dir_vec.magnitude() ** 2

        self._velocity = self.velocity + net_force * delta
        self._position = self.position + self._velocity * delta

        return collided

    def update_physics(self):
        self.velocity = self._velocity
        self.position = self._position

    def impart_force(self, force: Vector2):
        self.velocity += force / self.mass

# Functions

def render_prediction(end_pos, left_click, bodies, create_mass, scale):
    com = left_click - (sum([body.position for body in bodies], start=Vector2()) / len(bodies))
    velocity = (left_click - camera.world_position(Vector2(end_pos)))
    if velocity.x or velocity.y:
        velocity = velocity.normalize() * velocity.magnitude() / (com.magnitude() / 500)
    test_body = Body(left_click, velocity, create_mass, bodies, skip_surf_gen=True)

    # Deep copying bodies
    test_bodies = []
    for body in bodies:
        test_bodies.append(Body(body.position, body.velocity, body.mass, test_bodies, skip_surf_gen=True))

    # for body in test_bodies:
    #     body.impart_force(-velocity * create_mass / len(bodies))

    test_bodies.append(test_body)

    lines, last_pos = [], camera.render_position(test_body.position)
    last_angle, count = (last_pos - center).normalize(), 0
    for i in range(1000):
        for body in test_bodies:
            body.tick(0.1 / scale)
        for body in test_bodies:
            body.update_physics()

        current_pos = camera.render_position(test_body.position)

        # if (current_pos - center).angle_to(last_angle) > math.pi:

        lines.append((last_pos, current_pos))
        last_pos = current_pos

    return lines


camera = Camera(Vector2(), 1)


def solarsim():
    # Cursor management
    # TODO: Make a cursor mask and everything

    # Setting up loop variables
    running, paused, time, game_time = True, False, 0, 0

    last_second = time
    last_tenth = time

    time_scale = 1

    bodies = []
    create_mass, left_click = 2, None
    clicked_on, moving = None, None

    bodies.append(Body((0, 0), (0, 0), 4096, bodies, uuid="sun"))

    # Rendering
    text_surf = surf.generate_text("", (255, 255, 255))
    prediction_lines = []

    while running:
        delta = clock.tick() / 1000

        # Event handling
        clicked = False
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            # Mouse Events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if mods() == pygame.KMOD_LSHIFT:
                        left_click = camera.world_position(event.pos)
                    else:
                        moving = pygame.mouse.get_pos()

            elif event.type == pygame.MOUSEBUTTONUP:
                if moving and event.button == 1:
                    clicked = True
                    camera.position -= (Vector2(pygame.mouse.get_pos()) - Vector2(moving)) / camera.get_scale()
                    moving = None
                if left_click and event.button == 1:
                    com = left_click - (sum([body.position * body.mass for body in bodies], start=Vector2()) / (len(bodies) * sum([body.mass for body in bodies])))
                    velocity = (left_click - camera.world_position(event.pos))
                    if velocity.x or velocity.y:
                        velocity = velocity.normalize() * velocity.magnitude() / (com.magnitude() / 500)

                    bodies.append(Body(left_click, velocity, create_mass, bodies))

                    # for body in bodies:
                    #     body.impart_force(-velocity * create_mass / len(bodies))

                    left_click = None
                elif left_click and event.button == 3:  # Right click
                    left_click = None

                elif mods() == pygame.KMOD_LSHIFT:
                    pass

            elif event.type == pygame.MOUSEWHEEL:

                if mods() == pygame.KMOD_NONE:
                    if event.y:
                        # if not camera.tracking:
                        #     camera.position = camera.world_position(Vector2(pygame.mouse.get_pos()))
                        camera.change_scale(event.y >= 0)

                elif mods() == pygame.KMOD_LSHIFT:
                    if event.y > 0:
                        create_mass *= 2
                    elif event.y < 0:
                        create_mass /= 2

                # elif mods() == pygame.KMOD_LCTRL:
                #     if event.y > 0:
                #         create_mass *= 2
                #     elif event.y < 0:
                #         create_mass /= 2

            # Key Events
            elif event.type == pygame.KEYUP:
                key = event.key
                # print(event.unicode)
                if key == pygame.K_ESCAPE:
                    return -1
                elif key == pygame.K_p:
                    paused = not paused
                elif key == pygame.K_r:
                    camera.position = Vector2()
                    camera.tracking = None
                    return 0
                elif key == pygame.K_SPACE:
                    camera.position = Vector2()
                    camera.tracking = None
                elif key == pygame.K_LCTRL:
                    if left_click:
                        left_click = None
                elif key == pygame.K_LEFTBRACKET:
                    time_scale /= 2
                elif key == pygame.K_RIGHTBRACKET:
                    time_scale *= 2
                elif key == pygame.K_n:
                    time_scale *= -1
            elif event.type == pygame.KEYDOWN:
                pass

        # Pressed Button Handling
        camera_dir = Vector2()
        if pressed()[pygame.K_w]:
            camera_dir += (0, 1)
        if pressed()[pygame.K_a]:
            camera_dir += (1, 0)
        if pressed()[pygame.K_s]:
            camera_dir += (0, -1)
        if pressed()[pygame.K_d]:
            camera_dir += (-1, 0)

        if camera_dir:
            camera.position += camera_dir.normalize() * (1 / camera.get_scale()) * delta

        # Ticking
        if moving:
            new_moving = pygame.mouse.get_pos()
            camera.position -= (Vector2(new_moving) - Vector2(moving)) / camera.get_scale()
            moving = new_moving

        second_elapsed = time > last_second + 1
        tenth_elapsed = time > last_tenth + .1

        if not paused:
            game_time += delta
            # camera.tick(delta)

            collisions = []
            for body in bodies:
                collided = body.tick(delta * time_scale * 100)
                if collided:
                    collisions.append((body, collided))

            for body in bodies:
                body.ghosted = False
                body.update_physics()

            for body1, body2 in collisions:  # handling collisions
                i1, i2 = bodies.index(body1), bodies.index(body2)
                if i2 < i1:
                    body1, body2 = body2, body1
                    i1, i2 = i2, i1

                bodies.pop(i2)
                bodies.pop(i1)

                new_mass = body1.mass + body2.mass
                new_velocity = (body1.velocity * body1.mass + body2.velocity * body2.mass) / new_mass
                new_position = (body1.position * body1.mass + body2.position * body2.mass) / new_mass

                new_body = Body(new_position, new_velocity, new_mass, bodies, uuid=body1.uuid)
                bodies.insert(i1, new_body)

                if body1 == camera.tracking or body2 == camera.tracking:
                    camera.tracking = new_body

                camera.shake(body2.mass)

        camera.tick(delta)

        # Time management
        time += delta
        if second_elapsed:
            last_second = time
            text_surf = surf.generate_text(f"fps: {1 / delta:.2f}\ndelta: {delta:.4f}\nscale: {camera.get_scale():.2f}\ntime_scale:{time_scale:.2f}", spacing=5)

        if tenth_elapsed:
            last_tenth = time

        # Drawing
        win.fill((0, 0, 0))

        for body in bodies:  # Rendering Bodies
            render_pos = camera.render_position(body.position)
            rad = int(camera.scale(body.radius))

            if 0 < render_pos.x + rad and render_pos.x - rad < win.get_width() and 0 < render_pos.y + rad and render_pos.y - rad < win.get_height():

                if (Vector2(pygame.mouse.get_pos()) - render_pos).magnitude() < rad + 10:
                    text = body.name_surf
                    win.blit(text, render_pos - Vector2(text.get_width() // 2, text.get_height() + rad + 13))
                    if clicked_on == body and clicked:
                        camera.tracking = body
                    elif clicked:
                        clicked_on = body

                if rad > 4 * width:
                    win.fill((255, 0, 255))
                else:
                    print(render_pos)
                    pygame.gfxdraw.aacircle(win, int(render_pos.x), int(render_pos.y), rad + 10, (255, 255, 255))
                    win.blit(pygame.transform.scale(body_circle, (rad * 2, rad * 2)), render_pos - Vector2(rad, rad))

                # pygame.draw.circle(win, (0, 0, 255), render_pos, rad)
                if body.velocity:
                    pygame.draw.line(win, (255, 0, 0), render_pos, render_pos + body.velocity.normalize() * 25)

        if left_click:
            start_pos = camera.render_position(left_click)
            end_pos = pygame.mouse.get_pos()

            if tenth_elapsed:
                prediction_lines = render_prediction(end_pos, left_click, bodies, create_mass, camera.get_scale())

            for line in prediction_lines:
                pygame.draw.aaline(win, (0, 0, 255, 255 // 4), *line)

            # render_prediction(end_pos, left_click, bodies, create_mass, create_size)
            pygame.draw.aaline(win, (255, 255, 255), start_pos, end_pos)

        # if mods() == pygame.KMOD_LCTRL:
        #     ctrl_surf = surf.generate_text(f"mass: {create_mass}", (255, 255, 255))
        #     win.blit(ctrl_surf, Vector2(pygame.mouse.get_pos()) + Vector2(5, -10))

        if mods() == pygame.KMOD_LSHIFT:
            shift_surf= surf.generate_text(f"mass: {create_mass}", (255, 255, 255))
            win.blit(shift_surf, Vector2(pygame.mouse.get_pos()) + Vector2(5, -10))

        if camera.tracking:
            body = camera.tracking
            planet_info = f"position: <{body.position.x:6e}, {body.position.y:6e}>\n" \
                          f"speed: {body.velocity.magnitude():.2f}\n" \
                          f"mass: {body.mass:.2f}\n" \
                          f"radius: {body.radius:.2f}"
            _surf = surf.append_surfs(
                surf.generate_text(f"{clicked_on.uuid.lower()}", (255, 255, 255), "l"),
                surf.generate_text(planet_info, (255, 255, 255), spacing=5),
                10,
                True
            )

            win.blit(_surf, (width - 400, 25))

        # Draw FPS
        win.blit(text_surf, (0, 0))

        pygame.display.update()

    return -1

def main():
    looping = True
    next_view = 0
    while looping:
        if next_view == -1:
            looping = False
        elif next_view == 0:
            next_view = solarsim()
        else:
            print(f"ERROR: View #{next_view} not found!")
            looping = False
    print("Quitting application!")


if __name__ == '__main__':
    main()

pygame.display.quit()

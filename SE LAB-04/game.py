import pygame
import random
import math
import time

WIDTH, HEIGHT = 800, 560
FPS = 60
BG = (30, 35, 25)


class Zombie:
    def __init__(self, x, y, z_type="standard"):
        self.z_type = z_type
        if z_type == "fast":
            self.size = 20
            self.speed = 2.5
            self.max_hp = 1
            self.hp = 1
            self.color = (220, 180, 40)
            self.score_value = 15
        elif z_type == "tank":
            self.size = 45
            self.speed = 0.8
            self.max_hp = 6
            self.hp = 6
            self.color = (140, 40, 40)
            self.score_value = 25
        else:  # standard
            self.size = 30
            self.speed = 1.5
            self.max_hp = 3
            self.hp = 3
            self.color = (60, 140, 60)
            self.score_value = 10

        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.wobble = random.uniform(0, 6.28)
        self.frame = 0

    def update(self, player_pos):
        px, py = player_pos
        cx, cy = self.rect.center
        dx, dy = px - cx, py - cy
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 0:
            self.rect.x += int(dx / dist * self.speed)
            self.rect.y += int(dy / dist * self.speed)
        self.frame += 1

    def hit(self, damage=1):
        self.hp -= damage
        return self.hp <= 0

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame * 0.2) * 3)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(screen, self.color, draw_rect, border_radius=5)
        
        # Draw eyes proportional to size
        eye_off1 = max(3, int(self.size * 0.2))
        eye_off2 = max(6, int(self.size * 0.6))
        eye_r = max(2, int(self.size * 0.12))
        for ex in [draw_rect.x + eye_off1, draw_rect.x + eye_off2]:
            pygame.draw.circle(screen, (240, 40, 40), (ex, draw_rect.y + eye_off1 + 2), eye_r)

        # Health bar for Tank zombies if damaged
        if self.hp < self.max_hp and self.z_type == "tank":
            bar_w = self.size
            bar_h = 4
            fill_w = int(bar_w * (self.hp / self.max_hp))
            pygame.draw.rect(screen, (50, 50, 50), (draw_rect.x, draw_rect.y - 8, bar_w, bar_h))
            pygame.draw.rect(screen, (220, 40, 40), (draw_rect.x, draw_rect.y - 8, fill_w, bar_h))


def spawn_zombie(width, height, player_rect, margin=120):
    z_type = random.choices(["standard", "fast", "tank"], weights=[0.6, 0.25, 0.15])[0]
    size = 20 if z_type == "fast" else (45 if z_type == "tank" else 30)
    while True:
        x = random.randint(0, width - size)
        y = random.randint(45, height - size)  # Avoid spawning inside top HUD
        rect = pygame.Rect(x, y, size, size)
        if not rect.colliderect(player_rect.inflate(margin, margin)):
            return Zombie(x, y, z_type)


class Barrel:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 28, 34)
        self.color = (180, 90, 30)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (220, 50, 20), self.rect.inflate(-6, -10), border_radius=3)
        # Yellow hazard band across middle
        pygame.draw.line(screen, (255, 215, 0), (self.rect.left + 2, self.rect.centery), (self.rect.right - 2, self.rect.centery), 3)


class Explosion:
    def __init__(self, x, y, radius=120, duration=25):
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.timer = duration

    def update(self):
        self.timer -= 1
        return self.timer <= 0

    def draw(self, screen):
        progress = 1.0 - (self.timer / self.duration)
        current_r = int(self.radius * progress)
        alpha = int(255 * (1.0 - progress))
        
        surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        # Outer flame ring
        pygame.draw.circle(surf, (255, 100, 20, max(0, alpha - 40)), (self.radius, self.radius), current_r)
        # Inner flash core
        pygame.draw.circle(surf, (255, 230, 80, alpha), (self.radius, self.radius), max(1, current_r // 2))
        screen.blit(surf, (self.x - self.radius, self.y - self.radius))


SPEED = 4


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.color = (60, 160, 220)
        self.bullets = []
        self.shoot_cooldown = 0
        
        # Task 1: Health system
        self.max_hp = 3
        self.hp = 3
        self.invincible_timer = 0  # In frames (60 FPS)

        # Task 2: Ammo & Reload system
        self.max_ammo = 12
        self.ammo = 12
        self.is_reloading = False
        self.reload_timer = 0  # 120 frames = 2.0s

    def move(self, keys, width, height):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = SPEED
        self.rect.x = max(0, min(width - self.rect.width, self.rect.x + dx))
        self.rect.y = max(42, min(height - self.rect.height, self.rect.y + dy))

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # Handle invincibility timer
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # Handle reload timer
        if self.is_reloading:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.ammo = self.max_ammo
                self.is_reloading = False

    def start_reload(self):
        if not self.is_reloading and self.ammo < self.max_ammo:
            self.is_reloading = True
            self.reload_timer = 120  # 2 seconds at 60 FPS

    def shoot(self, target_pos):
        if self.is_reloading:
            return
        if self.ammo <= 0:
            self.start_reload()
            return
        if self.shoot_cooldown > 0:
            return

        cx, cy = self.rect.center
        tx, ty = target_pos
        dx, dy = tx - cx, ty - cy
        dist = (dx**2 + dy**2) ** 0.5
        if dist == 0:
            return

        vx, vy = dx / dist * 10, dy / dist * 10
        self.bullets.append([cx, cy, vx, vy])
        self.ammo -= 1
        self.shoot_cooldown = 15

        if self.ammo == 0:
            self.start_reload()

    def update_bullets(self, width, height):
        live = []
        for b in self.bullets:
            b[0] += b[2]
            b[1] += b[3]
            if 0 <= b[0] <= width and 40 <= b[1] <= height:
                live.append(b)
        self.bullets = live

    def draw(self, screen):
        # Flashing effect when invincible
        if self.invincible_timer > 0 and (self.invincible_timer // 6) % 2 == 0:
            draw_color = (200, 230, 255)
        else:
            draw_color = self.color

        pygame.draw.rect(screen, draw_color, self.rect, border_radius=6)
        
        # Bullets
        for b in self.bullets:
            pygame.draw.circle(screen, (255, 220, 60), (int(b[0]), int(b[1])), 5)


def spawn_barrels(count, width, height, player_rect):
    barrels = []
    margin = 80
    while len(barrels) < count:
        bx = random.randint(50, width - 80)
        by = random.randint(80, height - 80)
        rect = pygame.Rect(bx, by, 28, 34)
        if not rect.colliderect(player_rect.inflate(margin, margin)):
            barrels.append(Barrel(bx, by))
    return barrels


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Zombie Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 18, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.reset()

    def reset(self):
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.zombies = [spawn_zombie(WIDTH, HEIGHT, self.player.rect) for _ in range(4)]
        self.barrels = spawn_barrels(4, WIDTH, HEIGHT, self.player.rect)
        self.explosions = []
        self.score = 0
        self.wave = 1
        self.kills = 0
        self.kills_to_next = 8
        self.game_over = False
        self.start_time = time.time()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    if self.game_over:
                        self.reset()
                    else:
                        self.player.start_reload()
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                if event.button == 1:  # Left click shoot
                    self.player.shoot(event.pos)
        return True

    def update(self):
        if self.game_over:
            return

        keys = pygame.key.get_pressed()
        self.player.move(keys, WIDTH, HEIGHT)
        self.player.update_bullets(WIDTH, HEIGHT)
        self.score = int(time.time() - self.start_time)

        # Update zombies movement & player collision (Task 1)
        for z in self.zombies:
            z.update(self.player.rect.center)
            if z.rect.colliderect(self.player.rect):
                if self.player.invincible_timer <= 0:
                    self.player.hp -= 1
                    self.player.invincible_timer = 90  # 1.5 seconds invincibility
                    if self.player.hp <= 0:
                        self.game_over = True

        # Bullet collisions with barrels (Task 3)
        for b in self.player.bullets[:]:
            bx, by = int(b[0]), int(b[1])
            hit_barrel = None
            for barrel in self.barrels:
                if barrel.rect.collidepoint(bx, by):
                    hit_barrel = barrel
                    break

            if hit_barrel:
                if b in self.player.bullets:
                    self.player.bullets.remove(b)
                self.barrels.remove(hit_barrel)
                
                # Explosion radius 120px
                ex_cx, ex_cy = hit_barrel.rect.center
                self.explosions.append(Explosion(ex_cx, ex_cy, radius=120))

                # Destroy nearby zombies in explosion radius
                dead_by_barrel = []
                for z in self.zombies:
                    zx, zy = z.rect.center
                    dist = math.hypot(zx - ex_cx, zy - ex_cy)
                    if dist <= 120:
                        dead_by_barrel.append(z)

                for z in dead_by_barrel:
                    if z in self.zombies:
                        self.zombies.remove(z)
                        self.kills += 1
                        self.score += z.score_value

        # Bullet collisions with zombies
        dead = []
        for z in self.zombies:
            for b in self.player.bullets[:]:
                bx, by = int(b[0]), int(b[1])
                if z.rect.collidepoint(bx, by):
                    if z.hit():
                        dead.append(z)
                    if b in self.player.bullets:
                        self.player.bullets.remove(b)

        for z in dead:
            if z in self.zombies:
                self.zombies.remove(z)
                self.kills += 1
                self.score += z.score_value

        # Update explosions
        self.explosions = [e for e in self.explosions if not e.update()]

        # Wave progression
        if self.kills >= self.kills_to_next:
            self.kills = 0
            self.wave += 1
            self.kills_to_next = 8 + self.wave * 2
            # Replenish barrels on new wave
            if len(self.barrels) < 4:
                self.barrels.extend(spawn_barrels(4 - len(self.barrels), WIDTH, HEIGHT, self.player.rect))
            for _ in range(self.wave + 3):
                self.zombies.append(spawn_zombie(WIDTH, HEIGHT, self.player.rect))

    def draw(self):
        self.screen.fill(BG)
        
        # Grid lines
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, (40, 45, 35), (x, 40), (x, HEIGHT), 1)
        for y in range(40, HEIGHT, 60):
            pygame.draw.line(self.screen, (40, 45, 35), (0, y), (WIDTH, y), 1)

        # Draw barrels & explosions
        for barrel in self.barrels:
            barrel.draw(self.screen)
        for ex in self.explosions:
            ex.draw(self.screen)

        # Draw zombies & player
        for z in self.zombies:
            z.draw(self.screen)
        self.player.draw(self.screen)

        # Top HUD bar
        hud_bg = pygame.Rect(0, 0, WIDTH, 40)
        pygame.draw.rect(self.screen, (15, 20, 15), hud_bg)

        # HP representation
        hp_hearts = "❤️" * self.player.hp + "🖤" * (self.player.max_hp - self.player.hp)
        
        # Ammo representation
        if self.player.is_reloading:
            secs_left = self.player.reload_timer / 60.0
            ammo_str = f"RELOADING ({secs_left:.1f}s)"
            ammo_color = (255, 120, 80)
        else:
            ammo_str = f"Ammo: {self.player.ammo}/{self.player.max_ammo}"
            ammo_color = (255, 220, 100) if self.player.ammo > 0 else (255, 60, 60)

        hud_text = f"HP: {hp_hearts}  |  {ammo_str}  |  Wave: {self.wave}  Score: {self.score}  Kills: {self.kills}/{self.kills_to_next}"
        hud_surf = self.font.render(hud_text, True, (180, 230, 140))
        self.screen.blit(hud_surf, (10, 10))

        # Controls hint at top right
        hint_surf = self.font.render("R: Reload | WASD: Move", True, (120, 160, 120))
        self.screen.blit(hint_surf, (WIDTH - hint_surf.get_width() - 10, 10))

        # Game Over screen
        if self.game_over:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 170))
            self.screen.blit(ov, (0, 0))
            m = self.big_font.render("DEVOURED!", True, (220, 40, 40))
            s = self.font.render(f"Wave {self.wave} | Score {self.score} | Press R to Restart", True, (220, 220, 220))
            self.screen.blit(m, (WIDTH // 2 - m.get_width() // 2, HEIGHT // 2 - 40))
            self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 20))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()

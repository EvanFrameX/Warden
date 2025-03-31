import pygame
import sys
import os
import random
import math
from typing import Callable, Any, List, Dict, Tuple, Optional, Union

class WardenEngine:
    def __init__(self, title: str = "Warden Test", width: int = 800, height: int = 600, fps: int = 60):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.running = False
        self.scenes: Dict[str, 'Scene'] = {}
        self.current_scene: Optional['Scene'] = None
        self.assets: Dict[str, Any] = {}
        self.events = Events()
        self.input = Input()
        self.audio = Audio()
        self.camera = Camera(self.width, self.height)
        self._init_colors()
        self.debug_mode = False
        
    def _init_colors(self):
        """Initialize common colors as properties."""
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'gray': (128, 128, 128),
            'dark_gray': (64, 64, 64),
            'light_gray': (192, 192, 192)
        }
        
    def color(self, name: str) -> Tuple[int, int, int]:
        """Get a color by name or RGB tuple."""
        if isinstance(name, str):
            return self.colors.get(name.lower(), (0, 0, 0))
        return name
    
    def add_scene(self, name: str, scene: 'Scene'):
        """Add a scene to the game."""
        self.scenes[name] = scene
        scene.game = self
        
    def set_scene(self, name: str):
        """Set the current active scene."""
        if name in self.scenes:
            if self.current_scene:
                self.current_scene.exit()
            self.current_scene = self.scenes[name]
            self.current_scene.enter()
        
    def load_image(self, path: str, key: str = None, scale: float = 1.0, alpha: bool = True) -> pygame.Surface:
        """
        Load an image from file.
        
        Args:
            path: Path to image file
            key: Optional key to store the asset
            scale: Scale factor (1.0 = original size)
            alpha: Whether to preserve alpha channel
            
        Returns:
            Loaded pygame Surface
        """
        try:
            if alpha:
                img = pygame.image.load(path).convert_alpha()
            else:
                img = pygame.image.load(path).convert()
                
            if scale != 1.0:
                new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                img = pygame.transform.scale(img, new_size)
                
            if key:
                self.assets[key] = img
                
            return img
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            # Return a placeholder surface
            surf = pygame.Surface((32, 32))
            surf.fill((255, 0, 255))  # Magenta error color
            return surf
    
    def load_spritesheet(self, path: str, key: str, frame_width: int, frame_height: int, 
                        scale: float = 1.0, alpha: bool = True) -> List[pygame.Surface]:
        """
        Load a spritesheet and split it into individual frames.
        
        Args:
            path: Path to spritesheet image
            key: Key to store the frames in assets
            frame_width: Width of each frame
            frame_height: Height of each frame
            scale: Scale factor for all frames
            alpha: Whether to preserve alpha channel
            
        Returns:
            List of pygame Surfaces (frames)
        """
        sheet = self.load_image(path, None, scale, alpha)
        frames = []
        sheet_width, sheet_height = sheet.get_size()
        
        for y in range(0, sheet_height, frame_height):
            for x in range(0, sheet_width, frame_width):
                rect = pygame.Rect(x, y, frame_width, frame_height)
                frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA) if alpha else pygame.Surface((frame_width, frame_height))
                frame.blit(sheet, (0, 0), rect)
                if scale != 1.0:
                    new_size = (int(frame_width * scale), int(frame_height * scale))
                    frame = pygame.transform.scale(frame, new_size)
                frames.append(frame)
        
        self.assets[key] = frames
        return frames
    
    def load_tilemap(self, path: str, key: str, tile_size: int, scale: float = 1.0) -> Dict[int, pygame.Surface]:
        """
        Load a tilemap texture and split it into individual tiles.
        
        Args:
            path: Path to tilemap image
            key: Key to store the tiles in assets
            tile_size: Size of each tile (assumes square tiles)
            scale: Scale factor for all tiles
            
        Returns:
            Dictionary mapping tile indices to surfaces
        """
        sheet = self.load_image(path, None, scale, True)
        tiles = {}
        sheet_width, sheet_height = sheet.get_size()
        tile_index = 0
        
        for y in range(0, sheet_height, tile_size):
            for x in range(0, sheet_width, tile_size):
                rect = pygame.Rect(x, y, tile_size, tile_size)
                tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                tile.blit(sheet, (0, 0), rect)
                if scale != 1.0:
                    new_size = (int(tile_size * scale), int(tile_size * scale))
                    tile = pygame.transform.scale(tile, new_size)
                tiles[tile_index] = tile
                tile_index += 1
        
        self.assets[key] = tiles
        return tiles
    
    def load_sound(self, path: str, key: str = None) -> pygame.mixer.Sound:
        try:
            sound = pygame.mixer.Sound(path)
            if key:
                self.assets[key] = sound
            return sound
        except Exception as e:
            print(f"Error loading sound {path}: {e}")
            # Return a silent sound
            return pygame.mixer.Sound(buffer=bytes([0] * 44))
    
    def create_font(self, size: int = 24, name: str = None, key: str = None) -> pygame.font.Font:
        try:
            if name:
                font = pygame.font.SysFont(name, size)
            else:
                font = pygame.font.Font(None, size)
                
            if key:
                self.assets[key] = font
                
            return font
        except Exception as e:
            print(f"Error creating font: {e}")
            return pygame.font.Font(None, size)
    
    def toggle_debug(self):
        """Toggle debug mode for visualizing collision boxes and other info."""
        self.debug_mode = not self.debug_mode
    
    def run(self):
        """Run the main game loop."""
        self.running = True
        
        while self.running:
            # Handle events
            self.events.update()
            self.input.update()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        self.toggle_debug()
                self.events.process_event(event)
                self.input.process_event(event)
            
            # Update current scene
            if self.current_scene:
                self.current_scene.update()
                self.screen.fill(self.color('black'))  # Clear screen
                self.current_scene.draw(self.screen)
                
                if self.debug_mode:
                    self.current_scene.draw_debug(self.screen)
            
            # Update display
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        # Clean up
        pygame.quit()
        sys.exit()

class Camera:
    """Simple camera system for viewport control."""
    
    def __init__(self, width: int, height: int):
        self.rect = pygame.Rect(0, 0, width, height)
        self.target = None
        self.zoom = 1.0
        self.max_zoom = 3.0
        self.min_zoom = 0.5
        self.smoothness = 0.1
        
    def follow(self, target: 'GameObject'):
        """Set a target to follow."""
        self.target = target
        
    def update(self):
        """Update camera position based on target."""
        if self.target:
            target_x = self.target.x - self.rect.width / 2
            target_y = self.target.y - self.rect.height / 2
            
            # Smooth camera movement
            self.rect.x += (target_x - self.rect.x) * self.smoothness
            self.rect.y += (target_y - self.rect.y) * self.smoothness
            
            # Apply zoom
            if hasattr(self.target, 'zoom') and self.target.zoom:
                self.set_zoom(self.target.zoom)
    
    def set_zoom(self, zoom: float):
        """Set camera zoom level."""
        self.zoom = max(self.min_zoom, min(self.max_zoom, zoom))
        self.rect.width = int(self.rect.width / self.zoom)
        self.rect.height = int(self.rect.height / self.zoom)
    
    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Apply camera transform to a rectangle."""
        return rect.move(-self.rect.x, -self.rect.y)
    
    def apply_pos(self, pos: Tuple[float, float]) -> Tuple[float, float]:
        """Apply camera transform to a position."""
        return (pos[0] - self.rect.x, pos[1] - self.rect.y)
    
    def reverse_pos(self, pos: Tuple[float, float]) -> Tuple[float, float]:
        """Reverse camera transform for a position."""
        return (pos[0] + self.rect.x, pos[1] + self.rect.y)

class Scene:
    """Base class for game scenes."""
    
    def __init__(self):
        self.game: Optional[WardenEngine] = None
        self.objects: List['GameObject'] = []
        self.ui_elements: List['UIElement'] = []
        self.particle_systems: List['ParticleSystem'] = []
        self.tilemaps: List['Tilemap'] = []
        self.physics_world = PhysicsWorld()
        self.background_color = (0, 0, 0)
        
    def enter(self):
        """Called when the scene becomes active."""
        pass
        
    def exit(self):
        """Called when the scene is no longer active."""
        pass
        
    def update(self):
        """Update scene logic."""
        self.physics_world.update()
        
        for obj in self.objects:
            obj.update()
            
        for ps in self.particle_systems:
            ps.update()
            
        for ui in self.ui_elements:
            ui.update()
    
    def draw(self, surface: pygame.Surface):
        """Draw the scene."""
        surface.fill(self.background_color)
        
        # Draw tilemaps first (background)
        for tilemap in self.tilemaps:
            tilemap.draw(surface)
        
        # Draw game objects
        for obj in sorted(self.objects, key=lambda o: o.z_index if hasattr(o, 'z_index') else 0):
            obj.draw(surface)
            
        # Draw particles
        for ps in self.particle_systems:
            ps.draw(surface)
            
        # Draw UI elements last (on top)
        for ui in self.ui_elements:
            ui.draw(surface)
    
    def draw_debug(self, surface: pygame.Surface):
        """Draw debug information if debug mode is enabled."""
        if not self.game.debug_mode:
            return
            
        # Draw collision boxes
        for obj in self.objects:
            if hasattr(obj, 'hitbox') and obj.hitbox:
                pygame.draw.rect(surface, (0, 255, 0), obj.hitbox, 1)
                
        # Draw physics bodies
        for body in self.physics_world.bodies:
            pygame.draw.rect(surface, (255, 0, 0), body.rect, 1)
            
        # Draw camera bounds
        pygame.draw.rect(surface, (0, 0, 255), self.game.camera.rect, 1)
        
        # Draw FPS counter
        fps_text = f"FPS: {int(self.game.clock.get_fps())}"
        font = self.game.create_font(20)
        text_surf = font.render(fps_text, True, (255, 255, 255))
        surface.blit(text_surf, (10, 10))

class PhysicsWorld:
    """Simple physics world for collision detection."""
    
    def __init__(self):
        self.bodies: List['PhysicsBody'] = []
        self.gravity = (0, 0.5)
        
    def update(self):
        """Update all physics bodies."""
        for body in self.bodies:
            if body.dynamic:
                body.velocity = (
                    body.velocity[0] + self.gravity[0] * body.gravity_scale,
                    body.velocity[1] + self.gravity[1] * body.gravity_scale
                )
                body.move(body.velocity[0], body.velocity[1])
            
            # Simple collision detection
            if body.collider:
                for other in self.bodies:
                    if other != body and other.collider:
                        if body.rect.colliderect(other.rect):
                            body.on_collide(other)
                            other.on_collide(body)

class PhysicsBody:
    """Physics body for collision and movement."""
    
    def __init__(self, x: float = 0, y: float = 0, width: float = 32, height: float = 32):
        self.rect = pygame.Rect(x, y, width, height)
        self.velocity = [0, 0]
        self.dynamic = True
        self.collider = True
        self.gravity_scale = 1.0
        self.friction = 0.9
        self.on_collide: Callable[['PhysicsBody'], None] = lambda other: None
        
    def move(self, dx: float, dy: float):
        """Move the body."""
        self.rect.x += dx
        self.rect.y += dy
        
    def apply_force(self, fx: float, fy: float):
        """Apply a force to the body."""
        self.velocity[0] += fx
        self.velocity[1] += fy
        
    def stop(self):
        """Stop all movement."""
        self.velocity = [0, 0]

class GameObject:
    """Enhanced base class for game objects with physics."""
    
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y
        self.z_index = 0  # Drawing order
        self.visible = True
        self.hitbox: Optional[pygame.Rect] = None
        self.physics_body: Optional[PhysicsBody] = None
        
    def update(self):
        """Update object logic."""
        if self.physics_body:
            self.x = self.physics_body.rect.x
            self.y = self.physics_body.rect.y
            if self.hitbox:
                self.hitbox.x = self.x
                self.hitbox.y = self.y
        
    def draw(self, surface: pygame.Surface):
        """Draw the object."""
        pass
    
    def add_physics(self, width: float = 32, height: float = 32, dynamic: bool = True):
        """Add physics to this object."""
        self.physics_body = PhysicsBody(self.x, self.y, width, height)
        self.physics_body.dynamic = dynamic
        if hasattr(self, 'scene') and self.scene:
            self.scene.physics_world.bodies.append(self.physics_body)
    
    def set_hitbox(self, width: float = None, height: float = None, offset_x: float = 0, offset_y: float = 0):
        """Set a collision hitbox for this object."""
        if width is None and hasattr(self, 'image') and self.image:
            width = self.image.get_width()
            height = self.image.get_height()
        self.hitbox = pygame.Rect(self.x + offset_x, self.y + offset_y, width, height)

class Sprite(GameObject):
    """Enhanced sprite class with animation support."""
    
    def __init__(self, x: float = 0, y: float = 0, image: pygame.Surface = None):
        super().__init__(x, y)
        self.image = image
        self.velocity = [0, 0]
        self.rotation = 0
        self.scale = 1.0
        self.flip_x = False
        self.flip_y = False
        self.animations: Dict[str, 'Animation'] = {}
        self.current_animation: Optional['Animation'] = None
        self.set_hitbox()
        
    def update(self):
        """Update sprite position and animation."""
        super().update()
        
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        
        if self.hitbox:
            self.hitbox.x = self.x
            self.hitbox.y = self.y
            
        if self.current_animation:
            self.current_animation.update()
            self.image = self.current_animation.current_frame()
    
    def draw(self, surface: pygame.Surface):
        """Draw the sprite with rotation and scaling."""
        if self.image and self.visible:
            img = self.image
            
            # Apply transformations
            if self.flip_x or self.flip_y:
                img = pygame.transform.flip(img, self.flip_x, self.flip_y)
            if self.rotation != 0 or self.scale != 1.0:
                img = pygame.transform.rotozoom(img, self.rotation, self.scale)
            
            # Calculate position with camera offset
            cam = self.game.camera if hasattr(self, 'game') else None
            pos = (self.x, self.y)
            if cam:
                pos = cam.apply_pos(pos)
            
            surface.blit(img, pos)
            
            # Draw hitbox in debug mode
            if hasattr(self, 'game') and self.game.debug_mode and self.hitbox:
                debug_hitbox = self.hitbox.copy()
                if cam:
                    debug_hitbox.x, debug_hitbox.y = cam.apply_pos((debug_hitbox.x, debug_hitbox.y))
                pygame.draw.rect(surface, (0, 255, 0), debug_hitbox, 1)
    
    def add_animation(self, name: str, frames: List[pygame.Surface], speed: float = 0.1, loop: bool = True):
        """Add an animation to this sprite."""
        self.animations[name] = Animation(frames, speed, loop)
        
    def play_animation(self, name: str, restart: bool = True):
        """Play an animation by name."""
        if name in self.animations:
            if self.current_animation != self.animations[name] or restart:
                self.current_animation = self.animations[name]
                self.current_animation.reset()

class Animation:
    """Animation controller for sprites."""
    
    def __init__(self, frames: List[pygame.Surface], speed: float = 0.1, loop: bool = True):
        self.frames = frames
        self.speed = speed
        self.loop = loop
        self.current_frame_index = 0
        self.time_accumulator = 0.0
        self.playing = True
        
    def update(self):
        """Update animation frame."""
        if not self.playing or len(self.frames) <= 1:
            return
            
        self.time_accumulator += self.speed
        if self.time_accumulator >= 1.0:
            self.time_accumulator = 0.0
            self.current_frame_index += 1
            
            if self.current_frame_index >= len(self.frames):
                if self.loop:
                    self.current_frame_index = 0
                else:
                    self.current_frame_index = len(self.frames) - 1
                    self.playing = False
    
    def current_frame(self) -> pygame.Surface:
        """Get current animation frame."""
        if not self.frames:
            return None
        return self.frames[self.current_frame_index]
    
    def reset(self):
        """Reset animation to first frame."""
        self.current_frame_index = 0
        self.time_accumulator = 0.0
        self.playing = True

class Particle:
    """Single particle for particle systems."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.velocity = [0, 0]
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        self.color = (255, 255, 255)
        self.size = 4
        self.alpha = 255
        self.decay = True
        
    def update(self, dt: float) -> bool:
        """Update particle and return True if still alive."""
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        
        if self.decay:
            self.lifetime -= dt
            self.alpha = int(255 * (self.lifetime / self.max_lifetime))
            
        return self.lifetime > 0
    
    def draw(self, surface: pygame.Surface):
        """Draw the particle."""
        if self.size <= 1:
            surface.set_at((int(self.x), int(self.y)), self.color[:3] + (min(255, self.alpha),))
        else:
            s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, self.color[:3] + (min(255, self.alpha)), 
                             (self.size, self.size), self.size)
            surface.blit(s, (self.x - self.size, self.y - self.size))

class ParticleSystem(GameObject):
    """Particle effect system."""
    
    def __init__(self, x: float = 0, y: float = 0, max_particles: int = 100):
        super().__init__(x, y)
        self.particles: List[Particle] = []
        self.max_particles = max_particles
        self.emission_rate = 10  # particles per second
        self.emission_accumulator = 0.0
        self.active = True
        self.emission_area = (0, 0)  # x, y variance
        
    def update(self):
        """Update all particles and emit new ones if active."""
        dt = 1.0 / 60.0  # Approximate delta time
        
        # Update existing particles
        for i in range(len(self.particles) - 1, -1, -1):
            if not self.particles[i].update(dt):
                self.particles.pop(i)
        
        # Emit new particles
        if self.active and len(self.particles) < self.max_particles:
            self.emission_accumulator += self.emission_rate * dt
            while self.emission_accumulator >= 1.0 and len(self.particles) < self.max_particles:
                self.emit_particle()
                self.emission_accumulator -= 1.0
    
    def emit_particle(self):
        """Create and add a new particle (override for custom behavior)."""
        p = Particle(
            self.x + random.uniform(-self.emission_area[0], self.emission_area[0]),
            self.y + random.uniform(-self.emission_area[1], self.emission_area[1])
        )
        p.velocity = [random.uniform(-1, 1), random.uniform(-1, 1)]
        p.color = (random.randint(200, 255), random.randint(100, 200), random.randint(0, 100))
        p.max_lifetime = random.uniform(0.5, 2.0)
        p.lifetime = p.max_lifetime
        p.size = random.randint(2, 6)
        self.particles.append(p)
    
    def draw(self, surface: pygame.Surface):
        """Draw all particles."""
        for p in self.particles:
            p.draw(surface)
    
    def burst(self, count: int):
        """Emit a burst of particles at once."""
        for _ in range(min(count, self.max_particles - len(self.particles))):
            self.emit_particle()

class Tilemap(GameObject):
    """Tilemap for 2D games."""
    
    def __init__(self, tile_size: int = 32):
        super().__init__(0, 0)
        self.tile_size = tile_size
        self.tiles: Dict[Tuple[int, int], int] = {}  # (x, y): tile_index
        self.tileset: Dict[int, pygame.Surface] = {}
        self.width = 0
        self.height = 0
        
    def load_from_array(self, data: List[List[int]], tileset: Dict[int, pygame.Surface]):
        """Load tilemap from a 2D array."""
        self.tileset = tileset
        self.height = len(data)
        self.width = len(data[0]) if self.height > 0 else 0
        
        for y in range(self.height):
            for x in range(self.width):
                if data[y][x] >= 0:  # -1 or None can be used for empty tiles
                    self.tiles[(x, y)] = data[y][x]
    
    def draw(self, surface: pygame.Surface):
        """Draw the tilemap."""
        cam = self.game.camera if hasattr(self, 'game') else None
        
        # Calculate visible area
        start_x = 0
        start_y = 0
        end_x = self.width
        end_y = self.height
        
        if cam:
            start_x = max(0, int(cam.rect.x // self.tile_size))
            start_y = max(0, int(cam.rect.y // self.tile_size))
            end_x = min(self.width, int((cam.rect.x + cam.rect.width) // self.tile_size + 1))
            end_y = min(self.height, int((cam.rect.y + cam.rect.height) // self.tile_size + 1))
        
        # Draw visible tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if (x, y) in self.tiles:
                    tile_index = self.tiles[(x, y)]
                    if tile_index in self.tileset:
                        tile_img = self.tileset[tile_index]
                        pos = (x * self.tile_size, y * self.tile_size)
                        if cam:
                            pos = cam.apply_pos(pos)
                        surface.blit(tile_img, pos)

class UIElement(GameObject):
    """Base class for UI elements."""
    def __init__(self, x: float = 0, y: float = 0):
        super().__init__(x, y)
        self.z_index = 1000  # UI typically renders on top
        self.interactive = True
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input event. Return True if event was consumed."""
        return False

class Button(UIElement):
    """Enhanced button class with more styling options."""
    
    def __init__(self, x: float = 0, y: float = 0, width: float = 100, height: float = 50, 
                 text: str = "Button", font: pygame.font.Font = None):
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.text = Text(x + width/2, y + height/2, text, font)
        self.text.x -= self.text.font.size(text)[0] / 2
        self.text.y -= self.text.font.size(text)[1] / 2
        self.rect = pygame.Rect(x, y, width, height)
        self.on_click: Optional[Callable] = None
        
        # Styling
        self.colors = {
            'normal': (100, 100, 100),
            'hover': (150, 150, 150),
            'click': (200, 200, 200),
            'border': (255, 255, 255),
            'text': (255, 255, 255)
        }
        
        self.border_width = 2
        self.corner_radius = 5
        self.current_state = 'normal'
        
    def update(self):
        """Update button state."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        if self.rect.collidepoint(mouse_pos):
            if mouse_clicked:
                self.current_state = 'click'
            else:
                self.current_state = 'hover'
                # Check if click was released on the button
                for event in pygame.event.get(pygame.MOUSEBUTTONUP):
                    if event.button == 1 and self.on_click:
                        self.on_click()
        else:
            self.current_state = 'normal'
            
    def draw(self, surface: pygame.Surface):
        """Draw the button with rounded corners."""
        color = self.colors[self.current_state]
        
        # Draw button body
        pygame.draw.rect(surface, color, self.rect, border_radius=self.corner_radius)
        
        # Draw border
        if self.border_width > 0:
            pygame.draw.rect(surface, self.colors['border'], self.rect, 
                           self.border_width, border_radius=self.corner_radius)
        
        # Draw text
        self.text.draw(surface)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events for button interaction."""
        if not self.interactive:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.current_state = 'click'
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.current_state == 'click':
                if self.on_click:
                    self.on_click()
                self.current_state = 'hover'
                return True
                
        elif event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                if self.current_state != 'click':
                    self.current_state = 'hover'
            else:
                self.current_state = 'normal'
                
        return False

class Text(UIElement):
    """Enhanced text rendering with more options."""
    
    def __init__(self, x: float = 0, y: float = 0, text: str = "", font: pygame.font.Font = None, 
                 color: Tuple[int, int, int] = (255, 255, 255), align: str = 'left'):
        super().__init__(x, y)
        self.text = text
        self.font = font or pygame.font.Font(None, 24)
        self.color = color
        self.antialias = True
        self.align = align  # 'left', 'center', 'right'
        self.background = None
        self.padding = 2
        self.shadow = False
        self.shadow_offset = (1, 1)
        self.shadow_color = (0, 0, 0)
        
    def draw(self, surface: pygame.Surface):
        """Draw the text with alignment and optional background/shadow."""
        if not self.visible or not self.text:
            return
            
        text_surface = self.font.render(self.text, self.antialias, self.color)
        
        # Calculate position based on alignment
        pos = [self.x, self.y]
        if self.align == 'center':
            pos[0] -= text_surface.get_width() // 2
        elif self.align == 'right':
            pos[0] -= text_surface.get_width()
        
        # Draw background if specified
        if self.background:
            bg_rect = pygame.Rect(
                pos[0] - self.padding,
                pos[1] - self.padding,
                text_surface.get_width() + self.padding * 2,
                text_surface.get_height() + self.padding * 2
            )
            pygame.draw.rect(surface, self.background, bg_rect)
            pygame.draw.rect(surface, (255, 255, 255), bg_rect, 1)  # Border
        
        # Draw shadow if specified
        if self.shadow:
            shadow_surface = self.font.render(self.text, self.antialias, self.shadow_color)
            surface.blit(shadow_surface, (pos[0] + self.shadow_offset[0], pos[1] + self.shadow_offset[1]))
        
        surface.blit(text_surface, pos)

class ProgressBar(UIElement):
    """Progress bar UI element."""
    
    def __init__(self, x: float = 0, y: float = 0, width: float = 200, height: float = 20,
                 max_value: float = 100, value: float = 50):
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.max_value = max_value
        self.value = value
        self.colors = {
            'background': (50, 50, 50),
            'fill': (0, 200, 0),
            'border': (255, 255, 255)
        }
        self.border_width = 1
        self.corner_radius = 3
        
    def draw(self, surface: pygame.Surface):
        """Draw the progress bar."""
        # Draw background
        bg_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.colors['background'], bg_rect, 
                        border_radius=self.corner_radius)
        
        # Draw fill
        if self.value > 0:
            fill_width = max(0, min(self.width, (self.value / self.max_value) * self.width))
            fill_rect = pygame.Rect(self.x, self.y, fill_width, self.height)
            pygame.draw.rect(surface, self.colors['fill'], fill_rect, 
                            border_radius=self.corner_radius)
        
        # Draw border
        pygame.draw.rect(surface, self.colors['border'], bg_rect, 
                        self.border_width, border_radius=self.corner_radius)

class Events:
    """Simplified event system."""
    
    def __init__(self):
        self.listeners: Dict[int, List[Callable]] = {}
        
    def add_listener(self, event_type: int, callback: Callable):
        """Add an event listener."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
        
    def remove_listener(self, event_type: int, callback: Callable):
        """Remove an event listener."""
        if event_type in self.listeners and callback in self.listeners[event_type]:
            self.listeners[event_type].remove(callback)
            
    def process_event(self, event: pygame.event.Event):
        """Process a pygame event."""
        if event.type in self.listeners:
            for callback in self.listeners[event.type]:
                callback(event)
                
    def update(self):
        """Update event system (called each frame)."""
        pass

class Input:
    """Simplified input handling."""
    
    def __init__(self):
        self.keys = {}
        self.mouse_buttons = [False] * 5
        self.mouse_pos = (0, 0)
        self.mouse_rel = (0, 0)
        
    def update(self):
        """Update input state."""
        self.keys = pygame.key.get_pressed()
        self.mouse_buttons = pygame.mouse.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_rel = pygame.mouse.get_rel()
        
    def process_event(self, event: pygame.event.Event):
        """Process input-related events."""
        pass
        
    def key_down(self, key: int) -> bool:
        """Check if a key is currently pressed."""
        return self.keys.get(key, False)
        
    def mouse_down(self, button: int = 0) -> bool:
        """Check if a mouse button is currently pressed."""
        if 0 <= button < len(self.mouse_buttons):
            return self.mouse_buttons[button]
        return False
        
    def get_mouse_pos(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return self.mouse_pos

class Audio:
    """Simplified audio system."""
    
    def __init__(self):
        pygame.mixer.init()
        self.music_volume = 0.5
        self.sfx_volume = 0.5
        
    def play_music(self, path: str, loops: int = -1, volume: float = None):
        """
        Play background music.
        
        Args:
            path: Path to music file
            loops: Number of loops (-1 for infinite)
            volume: Volume (0.0 to 1.0)
        """
        if volume is None:
            volume = self.music_volume
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)
        
    def stop_music(self):
        """Stop background music."""
        pygame.mixer.music.stop()
        
    def pause_music(self):
        """Pause background music."""
        pygame.mixer.music.pause()
        
    def resume_music(self):
        """Resume paused background music."""
        pygame.mixer.music.unpause()
        
    def play_sound(self, sound: pygame.mixer.Sound, volume: float = None):
        """
        Play a sound effect.
        
        Args:
            sound: Sound object to play
            volume: Volume (0.0 to 1.0)
        """
        if volume is None:
            volume = self.sfx_volume
        sound.set_volume(volume)
        sound.play()
        
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
        
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))

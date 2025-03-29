import pygame
import sys
import os
import random
import math
from typing import Callable, Any, List, Dict, Tuple, Optional

class SimpleGame:
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
        self._init_colors()
        
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
                self.events.process_event(event)
                self.input.process_event(event)
            
            # Update current scene
            if self.current_scene:
                self.current_scene.update()
                self.current_scene.draw(self.screen)
            
            # Update display
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        # Clean up
        pygame.quit()
        sys.exit()

class Scene:
    """Base class for game scenes."""
    
    def __init__(self):
        self.game: Optional[SimpleGame] = None
        self.objects: List['GameObject'] = []
        
    def enter(self):
        """Called when the scene becomes active."""
        pass
        
    def exit(self):
        """Called when the scene is no longer active."""
        pass
        
    def update(self):
        """Update scene logic."""
        for obj in self.objects:
            obj.update()
        
    def draw(self, surface: pygame.Surface):
        """Draw the scene."""
        surface.fill(self.game.color('black'))  # Clear screen
        for obj in self.objects:
            obj.draw(surface)

class GameObject:
    """Base class for game objects."""
    
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y
        self.visible = True
        
    def update(self):
        """Update object logic."""
        pass
        
    def draw(self, surface: pygame.Surface):
        """Draw the object."""
        pass

class SimpleEvents:
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

class Sprite(GameObject):
    """Simplified sprite class."""
    
    def __init__(self, x: float = 0, y: float = 0, image: pygame.Surface = None):
        super().__init__(x, y)
        self.image = image
        self.rect = pygame.Rect(x, y, image.get_width(), image.get_height()) if image else None
        self.velocity = [0, 0]
        self.rotation = 0
        self.scale = 1.0
        
    def update(self):
        """Update sprite position."""
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        if self.rect:
            self.rect.x = self.x
            self.rect.y = self.y
            
    def draw(self, surface: pygame.Surface):
        """Draw the sprite."""
        if self.image and self.visible:
            if self.rotation != 0 or self.scale != 1.0:
                # Apply rotation and scaling
                img = pygame.transform.rotozoom(self.image, self.rotation, self.scale)
                rect = img.get_rect(center=(self.x, self.y))
                surface.blit(img, rect)
            else:
                surface.blit(self.image, (self.x, self.y))

class Text(GameObject):
    """Simplified text rendering."""
    
    def __init__(self, x: float = 0, y: float = 0, text: str = "", font: pygame.font.Font = None, 
                 color: Tuple[int, int, int] = (255, 255, 255)):
        super().__init__(x, y)
        self.text = text
        self.font = font or pygame.font.Font(None, 24)
        self.color = color
        self.antialias = True
        
    def draw(self, surface: pygame.Surface):
        """Draw the text."""
        if self.visible and self.text:
            text_surface = self.font.render(self.text, self.antialias, self.color)
            surface.blit(text_surface, (self.x, self.y))

class Button(GameObject):
    """Simplified button class."""
    
    def __init__(self, x: float = 0, y: float = 0, width: float = 100, height: float = 50, 
                 text: str = "Button", font: pygame.font.Font = None):
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.text = SimpleText(x + width/2, y + height/2, text, font)
        self.text.x -= self.text.font.size(text)[0] / 2
        self.text.y -= self.text.font.size(text)[1] / 2
        self.normal_color = (100, 100, 100)
        self.hover_color = (150, 150, 150)
        self.click_color = (200, 200, 200)
        self.current_color = self.normal_color
        self.rect = pygame.Rect(x, y, width, height)
        self.on_click = None
        
    def update(self):
        """Update button state."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        if self.rect.collidepoint(mouse_pos):
            if mouse_clicked:
                self.current_color = self.click_color
            else:
                self.current_color = self.hover_color
                # Check if click was released on the button
                for event in pygame.event.get(pygame.MOUSEBUTTONUP):
                    if event.button == 1 and self.on_click:
                        self.on_click()
        else:
            self.current_color = self.normal_color
            
    def draw(self, surface: pygame.Surface):
        """Draw the button."""
        pygame.draw.rect(surface, self.current_color, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)  # Border
        self.text.draw(surface)

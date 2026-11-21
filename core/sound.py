"""
Sound Manager with Asset Discovery & Procedural Synthesizer Fallback.
Handles audio playback safely across all environments.
"""

from pathlib import Path
import numpy as np
import pygame


class SoundManager:
    """Manages audio effects with automatic path discovery in assets/ or project root.
    Includes procedural audio synthesis fallback if audio files are missing or unreadable.
    """

    def __init__(self, volume: float = 0.4):
        self.sounds = {}
        self.muted = False
        self.volume = volume
        self.initialized = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.initialized = True
        except pygame.error as err:
            print(f"[SoundManager] Audio initialization skipped: {err}")
            return

        base_dir = Path(__file__).resolve().parent.parent
        asset_dir = base_dir / "assets"

        sound_files = {
            'sniper': 'sniper.wav',
            'artillery': 'artillery.wav',
            'mortar': 'mortar.wav',
            'explosion': 'explosion.wav',
            'base_hit': 'base_hit.wav'
        }

        for name, filename in sound_files.items():
            target_path = asset_dir / filename
            if not target_path.exists():
                target_path = base_dir / filename

            if target_path.exists():
                try:
                    sound = pygame.mixer.Sound(str(target_path))
                    sound.set_volume(self.volume)
                    self.sounds[name] = sound
                except pygame.error as err:
                    print(f"[SoundManager] Failed to load {filename}: {err}")
                    self.sounds[name] = self._synthesize_fallback(name)
            else:
                self.sounds[name] = self._synthesize_fallback(name)

        # Fallback for base_hit if missing
        if 'base_hit' not in self.sounds and 'explosion' in self.sounds:
            self.sounds['base_hit'] = self.sounds['explosion']

    def _synthesize_fallback(self, sound_type: str):
        """Synthesizes procedural sound waves if audio file is not present on disk."""
        try:
            sample_rate = 44100
            if sound_type in ('sniper', 'artillery'):
                # Laser / gunshot synth: decaying high-frequency chirp
                duration = 0.15
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                freq = np.linspace(880, 110, len(t))
                wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 25)
            elif sound_type in ('mortar', 'explosion', 'base_hit'):
                # Noise burst with exponential decay
                duration = 0.35
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                noise = np.random.uniform(-1.0, 1.0, len(t))
                low_rumble = np.sin(2 * np.pi * 60 * t)
                wave = (noise * 0.7 + low_rumble * 0.3) * np.exp(-t * 10)
            else:
                duration = 0.1
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                wave = np.sin(2 * np.pi * 440 * t) * np.exp(-t * 20)

            # Convert to 16-bit stereo PCM
            wave_int16 = (wave * 32767).astype(np.int16)
            stereo = np.column_stack((wave_int16, wave_int16))
            sound = pygame.sndarray.make_sound(stereo)
            sound.set_volume(self.volume)
            return sound
        except Exception:
            return None

    def play(self, name: str):
        """Plays sound effect if not muted and loaded."""
        if not self.muted and name in self.sounds and self.sounds[name]:
            try:
                self.sounds[name].play()
            except pygame.error:
                pass

    def toggle_mute(self) -> bool:
        """Toggles audio mute state. Returns current muted state."""
        self.muted = not self.muted
        return self.muted

    def set_volume(self, volume: float):
        """Adjusts master volume for all loaded sounds."""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)

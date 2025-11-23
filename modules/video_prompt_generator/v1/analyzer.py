"""
Video Prompt Analyzer - Analyzes song lyrics and audio for video generation
"""
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class VideoScene(BaseModel):
    """Video scene with timing and prompt"""
    start_time: float  # seconds
    end_time: float
    duration: float
    lyrics_segment: str
    visual_prompt: str
    mood: str
    camera_movement: Optional[str] = None
    style_notes: Optional[str] = None


class VideoTimeline(BaseModel):
    """Complete video timeline with scenes"""
    total_duration: float
    scene_count: int
    scenes: List[VideoScene]
    overall_style: str
    platform: str


class VideoPromptAnalyzer:
    """Analyzes songs and generates video prompts"""
    
    def __init__(self):
        self.default_chunk_duration = 5  # seconds
        self.supported_platforms = ["sora", "veo3", "pika", "runway"]
    
    async def analyze_song(
        self,
        song_text: str,
        audio_duration: int,
        platform: str = "sora",
        chunk_duration: int = 5
    ) -> VideoTimeline:
        """
        Analyze song and generate video prompt timeline.
        
        Args:
            song_text: Song lyrics
            audio_duration: Total audio duration in seconds
            platform: Target video generation platform
            chunk_duration: Duration of each scene in seconds
            
        Returns:
            VideoTimeline with scene-by-scene prompts
        """
        logger.info(f"Analyzing song for video prompts: {len(song_text)} chars, {audio_duration}s")
        
        # Validate platform
        if platform not in self.supported_platforms:
            logger.warning(f"Unsupported platform {platform}, using 'sora'")
            platform = "sora"
        
        # Split lyrics into segments
        lyrics_lines = [line.strip() for line in song_text.split('\n') if line.strip()]
        
        # Calculate number of scenes
        scene_count = max(1, audio_duration // chunk_duration)
        
        # Distribute lyrics across scenes
        lines_per_scene = max(1, len(lyrics_lines) // scene_count)
        
        scenes = []
        current_time = 0.0
        
        for i in range(scene_count):
            start_idx = i * lines_per_scene
            end_idx = min((i + 1) * lines_per_scene, len(lyrics_lines))
            
            scene_lyrics = '\n'.join(lyrics_lines[start_idx:end_idx])
            
            # Analyze mood and generate visual prompt
            mood = self._analyze_mood(scene_lyrics)
            visual_prompt = self._generate_visual_prompt(scene_lyrics, mood, platform)
            camera = self._suggest_camera_movement(mood, i, scene_count)
            
            scene = VideoScene(
                start_time=current_time,
                end_time=current_time + chunk_duration,
                duration=chunk_duration,
                lyrics_segment=scene_lyrics,
                visual_prompt=visual_prompt,
                mood=mood,
                camera_movement=camera,
                style_notes=self._get_platform_style_notes(platform)
            )
            
            scenes.append(scene)
            current_time += chunk_duration
        
        overall_style = self._determine_overall_style(song_text)
        
        return VideoTimeline(
            total_duration=float(audio_duration),
            scene_count=len(scenes),
            scenes=scenes,
            overall_style=overall_style,
            platform=platform
        )
    
    def _analyze_mood(self, lyrics_segment: str) -> str:
        """Analyze the mood of a lyrics segment"""
        lyrics_lower = lyrics_segment.lower()
        
        # Keywords for different moods
        moods = {
            "romantic": ["любовь", "сердце", "нежность", "love", "heart", "tender"],
            "joyful": ["счастье", "радость", "веселье", "joy", "happy", "celebration"],
            "nostalgic": ["память", "вспомни", "прошлое", "memory", "remember", "past"],
            "melancholic": ["грусть", "печаль", "слезы", "sad", "tears", "sorrow"],
            "energetic": ["танцуй", "жизнь", "вперед", "dance", "energy", "forward"],
            "dramatic": ["боль", "страсть", "огонь", "pain", "passion", "fire"]
        }
        
        mood_scores = {}
        for mood, keywords in moods.items():
            score = sum(1 for keyword in keywords if keyword in lyrics_lower)
            mood_scores[mood] = score
        
        # Return mood with highest score, or default
        if max(mood_scores.values()) > 0:
            return max(mood_scores, key=mood_scores.get)
        return "neutral"
    
    def _generate_visual_prompt(self, lyrics: str, mood: str, platform: str) -> str:
        """Generate visual prompt based on lyrics and mood"""
        
        # Mood-based visual templates
        mood_visuals = {
            "romantic": "Soft, dreamy atmosphere with warm golden lighting. Intimate close-ups, gentle movements",
            "joyful": "Bright, vibrant colors. Dynamic movements, celebratory atmosphere",
            "nostalgic": "Vintage filter, soft focus. Memories floating like photographs",
            "melancholic": "Cool blue tones, rain or mist. Slow, contemplative camera work",
            "energetic": "Bold colors, fast cuts. Dynamic action, upbeat rhythm",
            "dramatic": "High contrast lighting, intense colors. Powerful compositions",
            "neutral": "Balanced lighting, natural colors. Smooth transitions"
        }
        
        base_visual = mood_visuals.get(mood, mood_visuals["neutral"])
        
        # Try to extract key visual elements from lyrics
        visual_keywords = self._extract_visual_keywords(lyrics)
        
        if visual_keywords:
            prompt = f"{base_visual}. Scene featuring: {', '.join(visual_keywords[:3])}"
        else:
            prompt = base_visual
        
        # Add platform-specific formatting
        if platform == "sora":
            prompt = f"Cinematic shot: {prompt}"
        elif platform == "veo3":
            prompt = f"High-quality video: {prompt}"
        
        return prompt
    
    def _extract_visual_keywords(self, lyrics: str) -> List[str]:
        """Extract visual elements from lyrics"""
        visual_words = []
        
        # Common visual elements in Russian and English
        visual_elements = {
            "небо": "sky", "звезды": "stars", "море": "sea",
            "цветы": "flowers", "глаза": "eyes", "руки": "hands",
            "дом": "home", "дорога": "road", "город": "city",
            "солнце": "sun", "луна": "moon", "свет": "light",
            "тень": "shadow", "огонь": "fire", "вода": "water"
        }
        
        lyrics_lower = lyrics.lower()
        for ru_word, en_word in visual_elements.items():
            if ru_word in lyrics_lower or en_word in lyrics_lower:
                visual_words.append(en_word)
        
        return visual_words
    
    def _suggest_camera_movement(self, mood: str, scene_index: int, total_scenes: int) -> str:
        """Suggest camera movement based on mood and position in timeline"""
        
        # Different movements for different moods
        mood_cameras = {
            "romantic": ["slow dolly in", "gentle pan", "soft focus pull"],
            "joyful": ["dynamic tracking shot", "circular movement", "upward tilt"],
            "nostalgic": ["slow zoom out", "static with subtle drift", "handheld"],
            "melancholic": ["slow dolly out", "downward tilt", "static"],
            "energetic": ["fast tracking", "rapid pan", "dynamic zoom"],
            "dramatic": ["dramatic zoom", "sweeping crane shot", "intense close-up"],
            "neutral": ["steady cam", "smooth pan", "gentle zoom"]
        }
        
        movements = mood_cameras.get(mood, mood_cameras["neutral"])
        
        # Vary movement throughout the video
        return movements[scene_index % len(movements)]
    
    def _get_platform_style_notes(self, platform: str) -> str:
        """Get platform-specific style notes"""
        
        platform_notes = {
            "sora": "Cinematic quality, natural motion, high detail",
            "veo3": "Photorealistic, smooth transitions, high resolution",
            "pika": "Creative effects, stylized look, artistic freedom",
            "runway": "Professional quality, precise control, realistic motion"
        }
        
        return platform_notes.get(platform, "Standard video generation")
    
    def _determine_overall_style(self, song_text: str) -> str:
        """Determine the overall visual style for the video"""
        
        text_lower = song_text.lower()
        
        # Style detection based on content
        if any(word in text_lower for word in ["любовь", "love", "сердце", "heart"]):
            return "Romantic and dreamy"
        elif any(word in text_lower for word in ["танцуй", "dance", "party", "веселье"]):
            return "Energetic and vibrant"
        elif any(word in text_lower for word in ["память", "memory", "прошлое", "past"]):
            return "Nostalgic and reflective"
        else:
            return "Contemporary and emotional"
    
    def generate_scene_breakdown(self, timeline: VideoTimeline) -> str:
        """Generate a formatted text breakdown of the video timeline"""
        
        lines = [
            f"🎬 Video Timeline: {timeline.platform.upper()}",
            f"📊 Total Duration: {timeline.total_duration}s",
            f"🎭 Overall Style: {timeline.overall_style}",
            f"🎞️ Scene Count: {timeline.scene_count}",
            "",
            "=" * 60,
            ""
        ]
        
        for i, scene in enumerate(timeline.scenes, 1):
            lines.extend([
                f"Scene {i}: {scene.start_time:.1f}s - {scene.end_time:.1f}s",
                f"Mood: {scene.mood}",
                f"Lyrics: {scene.lyrics_segment[:100]}...",
                f"Visual: {scene.visual_prompt}",
                f"Camera: {scene.camera_movement}",
                "-" * 60,
                ""
            ])
        
        return "\n".join(lines)


# Global instance
_analyzer = None


def get_analyzer() -> VideoPromptAnalyzer:
    """Get video prompt analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = VideoPromptAnalyzer()
    return _analyzer

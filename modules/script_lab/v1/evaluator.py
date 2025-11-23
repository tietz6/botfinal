"""
Script Evaluator - Analyzes sales scripts and provides feedback
"""
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ScriptAnalysis(BaseModel):
    """Script analysis result"""
    overall_score: float  # 0-100
    structure_score: float
    psychology_score: float
    softness_score: float
    engagement_score: float
    cta_score: float
    
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    improved_version: Optional[str] = None


class ScriptEvaluator:
    """Evaluates sales scripts and provides detailed feedback"""
    
    # Configuration constants
    MIN_WORD_COUNT = 50
    OPTIMAL_MIN_WORDS = 50
    OPTIMAL_MAX_WORDS = 300
    
    def __init__(self):
        self.criteria = {
            "structure": self._evaluate_structure,
            "psychology": self._evaluate_psychology,
            "softness": self._evaluate_softness,
            "engagement": self._evaluate_engagement,
            "cta": self._evaluate_cta
        }
    
    async def evaluate_script(self, script: str, scenario: str = "full_sale") -> ScriptAnalysis:
        """
        Evaluate a sales script and return detailed analysis.
        
        Args:
            script: The sales script text
            scenario: Type of scenario (full_sale, objection_handling, etc.)
            
        Returns:
            ScriptAnalysis with scores and feedback
        """
        logger.info(f"Evaluating script for scenario: {scenario}")
        
        # Evaluate each criterion
        structure_score = self._evaluate_structure(script)
        psychology_score = self._evaluate_psychology(script)
        softness_score = self._evaluate_softness(script)
        engagement_score = self._evaluate_engagement(script)
        cta_score = self._evaluate_cta(script)
        
        # Calculate overall score
        overall_score = (
            structure_score * 0.25 +
            psychology_score * 0.20 +
            softness_score * 0.20 +
            engagement_score * 0.20 +
            cta_score * 0.15
        )
        
        # Generate feedback
        strengths = self._identify_strengths(script, {
            "structure": structure_score,
            "psychology": psychology_score,
            "softness": softness_score,
            "engagement": engagement_score,
            "cta": cta_score
        })
        
        weaknesses = self._identify_weaknesses(script, {
            "structure": structure_score,
            "psychology": psychology_score,
            "softness": softness_score,
            "engagement": engagement_score,
            "cta": cta_score
        })
        
        suggestions = self._generate_suggestions(script, weaknesses)
        
        improved_version = self._generate_improved_version(script, suggestions)
        
        return ScriptAnalysis(
            overall_score=round(overall_score, 2),
            structure_score=round(structure_score, 2),
            psychology_score=round(psychology_score, 2),
            softness_score=round(softness_score, 2),
            engagement_score=round(engagement_score, 2),
            cta_score=round(cta_score, 2),
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            improved_version=improved_version
        )
    
    def _evaluate_structure(self, script: str) -> float:
        """Evaluate script structure (0-100)"""
        score = 50.0  # Base score
        
        # Check for greeting
        greetings = ["привет", "здравствуй", "добрый день", "hello"]
        if any(g in script.lower() for g in greetings):
            score += 10
        
        # Check for introduction
        intros = ["меня зовут", "я из", "компани", "представляю"]
        if any(i in script.lower() for i in intros):
            score += 10
        
        # Check for questions
        if "?" in script:
            score += 10
        
        # Check for closing
        closings = ["спасибо", "жду", "свяжемся", "до свидания"]
        if any(c in script.lower() for c in closings):
            score += 10
        
        # Check length (not too short, not too long)
        word_count = len(script.split())
        if self.OPTIMAL_MIN_WORDS <= word_count <= self.OPTIMAL_MAX_WORDS:
            score += 10
        
        return min(score, 100)
    
    def _evaluate_psychology(self, script: str) -> float:
        """Evaluate psychological approach (0-100)"""
        score = 50.0
        
        # Check for empathy phrases
        empathy = ["понимаю", "чувства", "эмоции", "история", "особенн"]
        empathy_count = sum(1 for e in empathy if e in script.lower())
        score += min(empathy_count * 7, 20)
        
        # Check for benefit-focused language
        benefits = ["для вас", "вы получите", "поможет", "позволит"]
        if any(b in script.lower() for b in benefits):
            score += 10
        
        # Check for social proof
        social = ["другие клиенты", "многие", "отзывы", "примеры"]
        if any(s in script.lower() for s in social):
            score += 10
        
        # Check for personalization
        personal = ["ваш", "вас", "вам", "для вас"]
        personal_count = sum(1 for p in personal if p in script.lower())
        if personal_count >= 3:
            score += 10
        
        return min(score, 100)
    
    def _evaluate_softness(self, script: str) -> float:
        """Evaluate softness and non-aggressiveness (0-100)"""
        score = 70.0  # Start high
        
        # Penalize aggressive language
        aggressive = ["должны", "обязаны", "немедленно", "срочно купите", "только сейчас"]
        for a in aggressive:
            if a in script.lower():
                score -= 15
        
        # Reward soft language
        soft = ["может быть", "возможно", "если хотите", "как вам", "что скажете"]
        for s in soft:
            if s in script.lower():
                score += 6
        
        # Reward question format
        question_count = script.count("?")
        score += min(question_count * 3, 15)
        
        return max(min(score, 100), 0)
    
    def _evaluate_engagement(self, script: str) -> float:
        """Evaluate engagement level (0-100)"""
        score = 50.0
        
        # Check for questions
        question_count = script.count("?")
        score += min(question_count * 8, 25)
        
        # Check for emotional words
        emotions = ["представьте", "увидите", "почувствуете", "удивит", "восхит"]
        emotion_count = sum(1 for e in emotions if e in script.lower())
        score += min(emotion_count * 7, 20)
        
        # Check for storytelling elements
        story = ["история", "однажды", "например", "случай"]
        if any(s in script.lower() for s in story):
            score += 10
        
        return min(score, 100)
    
    def _evaluate_cta(self, script: str) -> float:
        """Evaluate call-to-action clarity (0-100)"""
        score = 50.0
        
        # Check for clear action
        actions = ["давайте", "можем начать", "предлагаю", "что скажете", "начнем"]
        if any(a in script.lower() for a in actions):
            score += 20
        
        # Check for next steps
        steps = ["следующий шаг", "дальше", "затем", "после этого"]
        if any(s in script.lower() for s in steps):
            score += 15
        
        # Check for time-related CTA
        time = ["сегодня", "сейчас", "эту неделю"]
        if any(t in script.lower() for t in time):
            score += 15
        
        return min(score, 100)
    
    def _identify_strengths(self, script: str, scores: Dict[str, float]) -> List[str]:
        """Identify script strengths"""
        strengths = []
        
        if scores["structure"] >= 75:
            strengths.append("Отличная структура скрипта - есть приветствие, основная часть и закрытие")
        
        if scores["psychology"] >= 75:
            strengths.append("Сильный психологический подход - учитывает эмоции клиента")
        
        if scores["softness"] >= 75:
            strengths.append("Мягкий и ненавязчивый стиль общения")
        
        if scores["engagement"] >= 75:
            strengths.append("Высокий уровень вовлечения - хорошо использованы вопросы")
        
        if scores["cta"] >= 75:
            strengths.append("Четкий призыв к действию")
        
        if "?" in script and script.count("?") >= 2:
            strengths.append("Хорошо задает вопросы клиенту")
        
        if any(word in script.lower() for word in ["представьте", "почувствуете"]):
            strengths.append("Использует визуализацию для вовлечения")
        
        return strengths or ["Скрипт имеет базовую структуру"]
    
    def _identify_weaknesses(self, script: str, scores: Dict[str, float]) -> List[str]:
        """Identify script weaknesses"""
        weaknesses = []
        
        if scores["structure"] < 60:
            weaknesses.append("Структура скрипта требует улучшения - не хватает четкого приветствия или закрытия")
        
        if scores["psychology"] < 60:
            weaknesses.append("Недостаточно психологических триггеров - добавьте эмпатию и выгоды для клиента")
        
        if scores["softness"] < 60:
            weaknesses.append("Слишком агрессивный тон - смягчите формулировки")
        
        if scores["engagement"] < 60:
            weaknesses.append("Низкая вовлеченность - добавьте больше вопросов и эмоциональных триггеров")
        
        if scores["cta"] < 60:
            weaknesses.append("Нечеткий призыв к действию - сделайте следующий шаг более понятным")
        
        if script.count("?") < 2:
            weaknesses.append("Мало вопросов - диалог должен быть двусторонним")
        
        if len(script.split()) < self.MIN_WORD_COUNT:
            weaknesses.append("Скрипт слишком короткий - добавьте больше деталей")
        
        return weaknesses or ["Требуется доработка отдельных элементов"]
    
    def _generate_suggestions(self, script: str, weaknesses: List[str]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # General suggestions
        if "приветствие" in str(weaknesses).lower() or not any(g in script.lower() for g in ["привет", "здравствуй"]):
            suggestions.append("Добавьте теплое приветствие: 'Привет! Меня зовут [имя] из компании На Счастье'")
        
        if "вопросов" in str(weaknesses).lower() or script.count("?") < 2:
            suggestions.append("Добавьте открытые вопросы: 'Расскажите, для кого песня?', 'Какая у вас история?'")
        
        if "психолог" in str(weaknesses).lower():
            suggestions.append("Используйте эмпатию: 'Понимаю, как важно сделать особенный подарок'")
        
        if "эмоц" in str(weaknesses).lower() or "вовлеч" in str(weaknesses).lower():
            suggestions.append("Добавьте визуализацию: 'Представьте реакцию, когда она услышит песню о вашей истории'")
        
        if "призыв" in str(weaknesses).lower() or "действи" in str(weaknesses).lower():
            suggestions.append("Сделайте четкий CTA: 'Давайте начнем с того, что вы расскажете историю?'")
        
        if "агрессив" in str(weaknesses).lower():
            suggestions.append("Замените императивы на мягкие формулировки: 'давайте' вместо 'вы должны'")
        
        if not suggestions:
            suggestions.append("Добавьте больше персонализации и обращений к клиенту")
            suggestions.append("Используйте конкретные примеры из практики")
        
        return suggestions
    
    def _generate_improved_version(self, script: str, suggestions: List[str]) -> str:
        """
        Generate an improved version of the script.
        
        Note: This is a placeholder implementation that provides a basic template.
        In production, this should integrate with LLM to generate truly improved
        versions based on the specific suggestions provided.
        """
        
        # Placeholder: Basic template with key improvements suggested
        improved_parts = [
            "Привет! Меня зовут [Ваше имя], я из компании \"На Счастье\".",
            "Мы создаем персонализированные песни - уникальные музыкальные подарки на основе реальных историй.",
            "",
            script.strip(),
            "",
            "Расскажите, для кого планируете подарок? Какая у вас история?",
            "",
            "Представьте реакцию, когда этот человек услышит песню, созданную специально о ваших моментах!",
            "",
            "Давайте начнем? Я задам несколько вопросов, чтобы понять вашу историю."
        ]
        
        # Add note about suggestions
        if suggestions:
            improved_parts.append("")
            improved_parts.append("Рекомендации для улучшения:")
            for suggestion in suggestions[:3]:
                improved_parts.append(f"• {suggestion}")
        
        return "\n".join(improved_parts)


# Global instance
_evaluator = None


def get_evaluator() -> ScriptEvaluator:
    """Get script evaluator instance"""
    global _evaluator
    if _evaluator is None:
        _evaluator = ScriptEvaluator()
    return _evaluator

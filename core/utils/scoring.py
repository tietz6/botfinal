"""Shared scoring utilities for training and exam modules"""


def evaluate_manager_message(manager_text: str, round_num: int = 0) -> int:
    """
    Evaluate a manager's message and return a score from 1-10.
    
    This is used consistently across training and exam modules.
    
    Args:
        manager_text: The manager's message to evaluate
        round_num: The round/turn number (0-based)
        
    Returns:
        Score from 1 to 10
    """
    score = 5  # Base score
    
    text_lower = manager_text.lower()
    
    # Positive indicators
    if "?" in manager_text:
        score += 1
    
    # Warmth and friendliness
    if any(word in text_lower for word in ["привет", "здравств", "рад", "понимаю", "спасибо"]):
        score += 1
    
    # Good length - not too short, not too long
    if 50 < len(manager_text) < 300:
        score += 1
    
    # Mentioning product/value (appropriate after greeting)
    if round_num > 2 and any(word in text_lower for word in ["песн", "подарок", "память", "история"]):
        score += 1
    
    # Negative indicators
    # Pressure tactics
    if any(word in text_lower for word in ["акция", "скидка", "срочно", "успей", "только сегодня"]):
        score -= 2
    
    # Talking about price too early
    if round_num <= 1 and any(word in text_lower for word in ["цена", "стоимость", "рубл", "тысяч"]):
        score -= 1
    
    # Too short messages
    if len(manager_text) < 20:
        score -= 1
    
    # Too long without structure
    if len(manager_text) > 400:
        score -= 1
    
    return max(1, min(10, score))

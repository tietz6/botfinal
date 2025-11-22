"""Encyclopedia service for content management"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import Page, ContentBlock, BlockType
from core.auth.models import Role

logger = logging.getLogger(__name__)


class EncyclopediaService:
    """Service for managing encyclopedia content"""
    
    def __init__(self, content_path: Optional[Path] = None):
        if content_path is None:
            # Default path relative to this file
            content_path = Path(__file__).parent.parent.parent / "modules" / "encyclopedia" / "v1" / "pages"
        
        self.content_path = content_path
        self._pages_cache: Dict[str, Page] = {}
    
    def load_pages(self) -> None:
        """Load all pages from JSON files"""
        if not self.content_path.exists():
            logger.warning(f"Encyclopedia content path does not exist: {self.content_path}")
            return
        
        self._pages_cache.clear()
        
        for json_file in self.content_path.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    page = Page(**data)
                    self._pages_cache[page.id] = page
                    logger.info(f"Loaded encyclopedia page: {page.id}")
            except Exception as e:
                logger.error(f"Failed to load page from {json_file}: {e}")
    
    async def get_pages_list(self, user_role: Optional[Role] = None) -> List[Dict[str, Any]]:
        """
        Get list of available pages for user role.
        
        Args:
            user_role: User's role (filters pages)
            
        Returns:
            List of page summaries
        """
        # Reload pages if cache is empty
        if not self._pages_cache:
            self.load_pages()
        
        result = []
        
        for page_id, page in self._pages_cache.items():
            # Check role access
            if user_role and user_role.value not in page.roles:
                continue
            
            result.append({
                "id": page.id,
                "title": page.title,
                "description": page.description or self._extract_description(page),
                "tags": page.tags or []
            })
        
        return result
    
    async def get_page(self, page_id: str, user_role: Optional[Role] = None) -> Optional[Page]:
        """
        Get full page by ID.
        
        Args:
            page_id: Page identifier
            user_role: User's role (for access check)
            
        Returns:
            Page object or None
        """
        # Reload pages if cache is empty
        if not self._pages_cache:
            self.load_pages()
        
        page = self._pages_cache.get(page_id)
        
        if not page:
            return None
        
        # Check role access
        if user_role and user_role.value not in page.roles:
            logger.warning(f"User role {user_role.value} denied access to page {page_id}")
            return None
        
        return page
    
    def _extract_description(self, page: Page) -> str:
        """Extract description from first text block"""
        for block in page.blocks:
            if block.type == BlockType.TEXT:
                # Take first 150 characters
                text = block.value[:150]
                if len(block.value) > 150:
                    text += "..."
                return text
        return ""
    
    async def get_page_text_for_tts(self, page_id: str) -> Optional[str]:
        """
        Get all text from page for TTS conversion.
        
        Args:
            page_id: Page identifier
            
        Returns:
            Combined text or None
        """
        page = await self.get_page(page_id)
        if not page:
            return None
        
        text_parts = [page.title]
        
        for block in page.blocks:
            if block.type in [BlockType.TEXT, BlockType.HINT, BlockType.EXAMPLE, BlockType.QUOTE]:
                text_parts.append(block.value)
            elif block.type == BlockType.IMAGE and block.caption:
                text_parts.append(f"Изображение: {block.caption}")
        
        return "\n\n".join(text_parts)


# Singleton instance
_encyclopedia_service = None


def get_encyclopedia_service() -> EncyclopediaService:
    """Get or create EncyclopediaService singleton"""
    global _encyclopedia_service
    if _encyclopedia_service is None:
        _encyclopedia_service = EncyclopediaService()
    return _encyclopedia_service

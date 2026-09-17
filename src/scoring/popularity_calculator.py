import math

class PopularityCalculator:
    """Calculates standardized 0-100 popularity score for workflow entries."""

    @staticmethod
    def calculate_youtube_score(views: int, likes: int, comments: int) -> float:
        if views <= 0:
            return 0.0
        like_ratio = likes / views
        comment_ratio = comments / views
        # Multi-factor score: Log volume (40%) + Like density (30%) + Comment density (30%)
        volume_component = math.log10(views + 1) * 15
        like_component = like_ratio * 400
        comment_component = comment_ratio * 800
        score = volume_component + like_component + comment_component
        return min(100.0, round(score, 2))

    @staticmethod
    def calculate_forum_score(views: int, likes: int, replies: int) -> float:
        if views <= 0:
            return 0.0
        like_ratio = likes / views
        reply_ratio = replies / views
        volume_component = math.log10(views + 1) * 20
        like_component = like_ratio * 300
        reply_component = reply_ratio * 600
        score = volume_component + like_component + reply_component
        return min(100.0, round(score, 2))

    @staticmethod
    def calculate_google_trends_score(search_interest: float, growth_pct: float) -> float:
        base_interest = search_interest * 0.75
        growth_bonus = max(0.0, growth_pct) * 0.5
        score = base_interest + growth_bonus
        return min(100.0, round(score, 2))

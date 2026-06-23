import logging

from sqlalchemy import func, select

from app.database.models.user_interest_profile import UserInterestProfile
from app.database.session import get_session

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN_WEIGHTS = {
    "ai_labs_strategy": 1.0,
    "ai_engineering_practice": 0.95,
    "eu_ai_regulation_policy": 0.95,
    "ai_geopolitics": 0.9,
    "swe_fundamentals": 0.8,
    "entrepreneurship": 0.8,
    "local_business": 0.5,
    "career_strategy": 0.7,
    "wisdom_mental_models": 0.65,
    "productivity": 0.65,
}

DEFAULT_CONTEXT_PROSE = """
## PROFILE

AI engineer & entrepreneur, 25, Netherlands. MSc Data Science & Entrepreneurship (JADS). Strong in ML/data, actively developing software engineering depth. Building real projects alongside study. Also deeply interested in CS fundamentals, how systems work at a conceptual level, and living deliberately — focused attention, avoiding distraction, reading broadly.

##LENS — always apply:

- What does this mean for someone in the EU/NL specifically?
- Is this actionable for a junior-to-mid AI engineer in 2025/2026?
- Career signal: what should I learn or prioritize based on this?
- Substance check: is this hype or does it have real depth?
- Life signal: does this help me think more clearly or live more intentionally?

"""

DEFAULT_CHANNEL_NOTES = {
    "boost": [],
    "deprioritize": ["reaction", "drama", "hype", "sponsor"],
}


def seed_interest_profile(session) -> bool:
    existing = session.scalar(select(func.count()).select_from(UserInterestProfile))
    if existing:
        return False

    profile = UserInterestProfile(
        version=1,
        domain_weights=DEFAULT_DOMAIN_WEIGHTS,
        context_prose=DEFAULT_CONTEXT_PROSE,
        channel_notes=DEFAULT_CHANNEL_NOTES,
    )
    session.add(profile)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with get_session() as session:
        created = seed_interest_profile(session)
        if created:
            session.commit()
            print("Created default user interest profile (version 1).")
        else:
            print("Skipped: a user interest profile already exists.")

from sebastian.clients.reddit.client import RedditClient
from sebastian.usecases.SkeletonSoldier.service import SkeletonSoldierService

from .clients import resolve_reddit_client


def resolve_skeleton_soldier_service(
    reddit_client: RedditClient = resolve_reddit_client(),
) -> SkeletonSoldierService:
    return SkeletonSoldierService(
        reddit_client=reddit_client,
    )

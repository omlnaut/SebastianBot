from sebastian.clients import MangaUpdateClient, RedditClient
from sebastian.usecases.MangaUpdate.service import MangaUpdateService
from sebastian.usecases.OnePunchMan.service import OnePunchManService
from sebastian.usecases.SkeletonSoldier import SkeletonSoldierService

from .clients import resolve_mangaupdate_client, resolve_reddit_client


def resolve_skeleton_soldier_service(
    reddit_client: RedditClient = resolve_reddit_client(),
) -> SkeletonSoldierService:
    return SkeletonSoldierService(
        reddit_client=reddit_client,
    )


def resolve_mangaupdate_service(
    mangaupdate_client: MangaUpdateClient = resolve_mangaupdate_client(),
) -> MangaUpdateService:
    return MangaUpdateService(
        client=mangaupdate_client,
    )


def resolve_one_punch_man_service(
    reddit_client: RedditClient = resolve_reddit_client(),
) -> OnePunchManService:
    return OnePunchManService(
        reddit_client=reddit_client,
    )

from fastapi import Security

from app.controllers.parser import parse, strategies, queue, poll
from app.core import config
from app.core.route import CriaRouter
from app.core.schemas import AppMode
from app.core.security.handlers.master import GetApiKeyMaster

router = CriaRouter(
    dependencies=[Security(GetApiKeyMaster())] if config.APP_MODE == AppMode.PRODUCTION else [],
    tags=['Parsing']
)

router.include_views(
    queue.view,
    poll.view,
    parse.view,
    strategies.view,
)

from app.controllers.schemas import APIResponse
from app.core.security.get_api_key import GetApiKey, BadAPIKeyException


class GetApiKeyAny(GetApiKey):

    async def execute(self) -> str:

        response = await self.get_auth()

        if not response.get('authorized'):
            raise BadAPIKeyException(
                status_code=401,
                detail="API key was not found or is not authorized."
            )

        # Master keys go brr
        if not response.get('master') and APIResponse.stack_trace_enabled(self.request):
            raise BadAPIKeyException(
                status_code=401,
                detail="Only master keys can access stacktraces!"
            )

        return self.api_key

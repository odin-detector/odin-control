import asyncio
import logging

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse

class AsyncApiAdapter(ApiAdapter):

    is_async = True

    def __init__(self, **kwargs):

        super(AsyncApiAdapter, self).__init__(**kwargs)

    async def get(self, path, request):

        logging.info("in AsyncApiAdapter GET before sleep")
        await asyncio.sleep(2.0)
        logging.info("in AsyncApiAdapter GET after")

        return ApiAdapterResponse({'response': "GET on path {}".format(path)})


import sys
import os

import echoroboticsapi
import aiohttp
import asyncio
import logging

async def on_request_start(session, trace_config_ctx, params):
    print("Starting %s request for %s. I will send: %s" % (params.method, params.url, params.headers))

async def main():
    user_id = os.environ.get("USER_ID", "your_user_id_here")
    user_token = os.environ.get("USER_TOKEN", "your_user_token_here")
    robot_id = os.environ.get("ROBOT_ID", "your_robot_id_here")

    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(on_request_start)

    async with aiohttp.ClientSession(
        #trace_configs=[trace_config],
        cookies=echoroboticsapi.create_cookies(
            user_id=user_id, user_token=user_token,
        )
    ) as session:
        api = echoroboticsapi.Api(session, robot_ids=robot_id)
        print(await api.last_statuses())

        await asyncio.sleep(0.5)

        result = await api.set_mode("chargeAndWork")
        print(result)

        await asyncio.sleep(0.5)
        print(await api.last_statuses())


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
#!/usr/bin/env python3
import sys
import os
import time

import echoroboticsapi
import aiohttp
import asyncio
import logging


async def on_request_start(session, trace_config_ctx, params):

    # Ask the session's cookie jar what it would attach for this URL
    jar_cookies = session.cookie_jar.filter_cookies(params.url)
    if jar_cookies:
        cookie_str = ";\n".join(f"{k}={v.value}" for k, v in jar_cookies.items())
    else:
        cookie_str = ""

    print(
        "Starting %s request for %s. I will send: %s; cookie_jar: %s"
        % (params.method, params.url, params.headers, cookie_str)
    )


async def main():
    email = os.environ.get("EMAIL", "your_email")
    password = os.environ.get("PASSWORD", "your_password")
    robot_id = os.environ.get("ROBOT_ID", "your_robot_id_here")

    if "your" in email or "your" in password or "your" in robot_id:
        print(
            f"Error: invalid email, password or robot_id: {email=} {password=} {robot_id=}"
        )
        sys.exit(1)

    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(on_request_start)

    async with aiohttp.ClientSession(
        trace_configs=[trace_config],
    ) as session:
        api = echoroboticsapi.Api(
            session, robot_ids=robot_id, email=email, password=password
        )
        smartmode = echoroboticsapi.SmartMode(robot_id)
        api.register_smart_mode(smartmode)
        smartfetch = echoroboticsapi.SmartFetch(api)

        print(f"config: {await api.get_config(reload=True)}")

        print(f"smart_fetch: {await smartfetch.smart_fetch()}")

        print(f"last_statuses: {await api.history_list()}")

        await asyncio.sleep(0.5)
        print(f"robot_mode guess: {smartmode.get_robot_mode()}")

        print(f"current: {await api.current()}")
        # print(f"setmode chargeAndWork: {await api.set_mode('work', use_current_timeout=60)}")
        print(f"robot_mode guess: {smartmode.get_robot_mode()}")

        while True:
            await asyncio.sleep(5)
            await smartfetch.smart_fetch()
            print(f"robot_mode guess: {smartmode.get_robot_mode()}")


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())

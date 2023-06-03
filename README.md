pyechorobotics
=============

![echorobotics_logo](https://brands.home-assistant.io/_/echorobotics/logo@2x.png)

Allows control and reads status of robot lawn mowers by echorobotics.

Example:
```python
import sys

import echoroboticsapi
import aiohttp
import asyncio
import logging


async def main():
    async with aiohttp.ClientSession(cookies=echoroboticsapi.create_cookies(user_id="your-user-id", user_token="user-user-token")) as session:
        api = echoroboticsapi.Api(session, robot_ids=["your-robot-id"])
        print(await api.last_statuses())
        print(await api.set_mode("chargeAndWork"))


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())

```

Unfortunately, the API doesn't tell is which mode the robot is in.
We can make an educated guess though, depending on what we set ourselves, history events and the status.
This is what SmartMode does:

```python
import sys

import echoroboticsapi
import aiohttp
import asyncio
import logging


async def main():
    async with aiohttp.ClientSession(cookies=echoroboticsapi.create_cookies(user_id="your-user-id", user_token="user-user-token")) as session:
        api = echoroboticsapi.Api(session, robot_ids=["your-robot-id"])
        smartmode = echoroboticsapi.SmartMode("your-robot-id")
        api.register_smart_mode(smartmode)
        
        print(await api.history_list())
        print(await api.last_statuses())
        print(await smartmode.get_robot_mode())


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())

```

See also src/main.py

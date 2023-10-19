pyechorobotics
=============

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://brands.home-assistant.io/_/echorobotics/dark_logo@2x.png">
  <img alt="Echorobotics Logo" src="https://brands.home-assistant.io/_/echorobotics/logo@2x.png">
</picture>

Allows control and reads status of robot lawn mowers by echorobotics.

Used by [Home Assistant Echorobotics integration](https://github.com/functionpointer/home-assistant-echorobotics-integration).

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

Unfortunately, the API doesn't tell is which mode ("chargeAndWork", "work" or "chargeAndStay") the robot is in.
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

Dev notes
=========

To make a new release, use GitHub website and draft a release manually.
Make sure the version number in pyproject.toml matches the new tag.
GitHub Actions will publish it to pypi.

Adding a new state
------------------

If a new state is found, it must be added to ``models.py``.
Also check ``notify_laststatuses_received()`` in ```smart_mode.py``` if it should be recognized as a specific Mode.

Finally, in home-assistant-echorobotics-integration, increment the version number in the manifest.json.

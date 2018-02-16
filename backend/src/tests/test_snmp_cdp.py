from snmp import snmp_async
import pprint
import asyncio


async def main():
    data = await snmp_async.get_cdp('192.168.1.1', 'public', 161)
    pprint.pprint(data)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    loop.close()

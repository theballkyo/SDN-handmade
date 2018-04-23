import asyncio

try:
    import uvloop

    can_uvloop = True
except ImportError:
    can_uvloop = False

from snmp.snmp_process import process_system


def force_update_interface(host, community, port):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if can_uvloop:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    loop.run_until_complete(
        process_system(host, community, port)
    )

    loop.close()

import asyncio

import netmiko
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException

from concurrent.futures import ThreadPoolExecutor

import queue

import router_command as router_cmd
import services
import logging

try:
    import uvloop

    can_uvloop = True
except ImportError:
    can_uvloop = False


def process_flow_action(ssh_info, cmd, stage_queue):
    """
    Stage 1 try to SSH connect to device
    Stage 2 sent flow command
    Stage 3 rollback (When some device failed in stage 2)
    :param ssh_info:
    :param cmd:
    :param stage_queue:
    :return:
    """

    print(ssh_info)
    print(type(ssh_info))
    print(ssh_info.get('device_type'))
    print(ssh_info['device_type'])

    try:
        net_connect = netmiko.ConnectHandler(**{
            # 'device_type': 'cisco_ios',
            'device_type': ssh_info['device_type'],
            'ip': ssh_info['ip'],
            'username': ssh_info['username'],
            'password': ssh_info['password'],
            'port': ssh_info['port'],
            'secret': ssh_info['secret'],
            'verbose': False,
            'global_delay_factor': 0.5
        })
        net_connect.enable()
        stage_queue["check_connect_cb"].put(True)
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
        logging.debug("Error 0")
        print(e)
        stage_queue["check_connect_cb"].put(False)
        return False
    except Exception as e:
        logging.debug("error 1")
        print(e)
        stage_queue["send_config_cb"].put(False)
        return False

    print("Waiting send_config")
    send_config_stage = stage_queue["send_config"].get()
    print("AAA Sendconfig")
    if send_config_stage:
        if not net_connect.is_alive():  # Try to reconnect
            try:
                net_connect = netmiko.ConnectHandler(**{
                    'device_type': ssh_info['device_type'],
                    'ip': ssh_info['ip'],
                    'username': ssh_info['username'],
                    'password': ssh_info['password'],
                    'port': ssh_info['port'],
                    'secret': ssh_info['secret'],
                    'verbose': False,
                    'global_delay_factor': 0.5
                })
                net_connect.enable()
                # await stage_queue["send_config_cb"].put(True)
                logging.debug("SSH Connect !")
            except (NetMikoTimeoutException, NetMikoAuthenticationException):
                #  Can't reconnect to server stage 2 failed !!!
                logging.debug("Can't connect SSH")
                stage_queue["send_config_cb"].put(False)
                return False
            except Exception as e:
                logging.debug("error")
                print(e)
                stage_queue["send_config_cb"].put(False)
                return False

        # Send config command
        logging.debug("Send config")
        print("\n".join(cmd))
        output = net_connect.send_config_set("\n".join(cmd))
        # TODO Save log output
        stage_queue["send_config_cb"].put(True)
        # TODO next version checking error

    else:  # send_config_stage Cancelled
        return

    # Todo Stage 3 implement
    # Stage 3 is True == Rollback
    rollback_stage = stage_queue["rollback"].get()
    if rollback_stage:
        pass

    logging.debug("End")

    return True


async def process_flow(executor, flow):
    # Todo Move to another file
    # Run flow

    device_service = services.DeviceService()

    stage_queue = {
        "check_connect": queue.Queue(),
        "check_connect_cb": queue.Queue(),
        "send_config": queue.Queue(),
        "send_config_cb": queue.Queue(),
        "rollback": queue.Queue(),
        "rollback_cb": queue.Queue()
    }

    loop = asyncio.get_event_loop()

    num_device = 0

    tasks = []

    for action in flow.get('action_pending', []):
        device_ip = action["device_ip"]
        ssh_info = device_service.get_ssh_info(device_ip)
        if not ssh_info:
            continue

        flow_cmd = router_cmd.generate_policy_command(ssh_info['device_type'], flow)
        action_cmd = router_cmd.generate_action_command(ssh_info['device_type'], flow, action)
        cmd = flow_cmd + action_cmd
        print(cmd)

        tasks.append(
            asyncio.ensure_future(loop.run_in_executor(executor, process_flow_action, ssh_info, cmd, stage_queue))
        )

        num_device += 1
    print(tasks)
    send_config_cancel = False
    print("check_connect")
    for _ in range(num_device):
        can_connect = stage_queue["check_connect_cb"].get()
        if not can_connect:
            send_config_cancel = True

    print("send_config")
    for _ in range(num_device):
        if send_config_cancel:
            stage_queue["send_config"].put(False)
        else:
            stage_queue["send_config"].put(True)

    print("send_config")
    rollback = False
    for _ in range(num_device):
        stage2_success = stage_queue["send_config_cb"].get()
        if not stage2_success:
            rollback = True

    print("rollback")
    for _ in range(num_device):
        if rollback:
            stage_queue["rollback"].put(True)
        else:
            stage_queue["rollback"].put(False)

    await asyncio.gather(*tasks)


def run_flow_loop(flow):
    import time
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Executor
    executor = ThreadPoolExecutor(max_workers=10)
    if can_uvloop:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print("Loop start")
    start = time.time()
    loop.run_until_complete(process_flow(executor, flow))
    print("Usage time: {:.2f}".format(time.time() - start))
    print("Loop stop")
    loop.stop()

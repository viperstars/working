import socket
import psutil
import commands
import json


def execute_shell(command):

    status, output = commands.getstatusoutput(command)
    if status == 0:
        return output
    else:
        return False


def get_partition():
    status, output = commands.getstatusoutput("fdisk -l | grep 'Disk /dev'")
    if status == 0:
        return output.split("\n")
    else:
        return False

info = dict()

info["hostname"] = socket.gethostname()
mem_info = psutil.virtual_memory()
info["mem_total"] = mem_info.total

net_info = psutil.net_if_addrs()

info["network"] = dict()

for x, y in net_info.iteritems():
    if x not in info["network"]:
        info["network"][x] = dict()
    for z in y:
        if z.family == 2:
            info["network"][x]["ip"] = z.address
        if z.family == 17:
            info["network"][x]["mac"] = z.address

outputs = execute_shell("cat /proc/cpuinfo | grep 'model name'")

info["cpu"] = dict()

info["cpu"]["model"] = outputs.split(":")[1].strip()
info["cpu"]["count"] = psutil.cpu_count()

info["partitions"] = [(x.split()[1].strip(":"), x.split()[4]) for x in get_partition()]

outputs = execute_shell("dmidecode | grep 'System Information' -A 6 | grep Manufacturer")

info["manufacturer"] = outputs.split(":")[1]

outputs = execute_shell("dmidecode | grep 'System Information' -A 6 | grep 'Product Name'")

info["product_name"] = outputs.split(":")[1]

outputs = execute_shell("dmidecode | grep -i release")

info["release_date"] = outputs.split(":")[1]

outputs = execute_shell("cat /etc/issue | head -n 1")

info["sys_version"] = outputs

print json.dumps(info, indent=True)

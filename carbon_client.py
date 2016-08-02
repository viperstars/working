import socket
import time
import errno


class CarbonClient(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._carbon = None
        self._connected = False

    def connect(self):
        if not self._connected:
            self._connect()

    def _connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                sock.connect((self._host, self._port))
            except socket.error as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise e
            break
        self._carbon = sock
        self._connected = True

    def close(self):
        if self._connected:
            self._carbon.close()
            self._connected = False

    def send(self, metrics):
        chunk_start, chunk_end = 0, 20
        while True:
            payload = []
            metric_chunk = metrics[chunk_start: chunk_end]
            if not metric_chunk:
                break
            now = int(time.time())
            for metric in metric_chunk:
                if len(metric) == 2:
                    payload.append("{0} {1} {2}\n".format(metric[0], metric[1], now))
                elif len(metric) == 3:
                    payload.append("{0} {1} {2}\n".format(metric[0], metric[1], metric[2]))
            self._carbon.sendall("".join(payload))
            chunk_start, chunk_end = chunk_end, chunk_end + 20

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exec_type, exec_value, exc_tb):
        self.close()
        return exec_value is None


class SubCarbonClient(CarbonClient):
    CARBON_ADDR = ("192.168.1.1", 2003)

    def __init__(self):
        super(SubCarbonClient, self).__init__(*self.CARBON_ADDR)


if __name__ == "__main__":
    with SubCarbonClient() as client:
        client.send([("system.test", 40)])

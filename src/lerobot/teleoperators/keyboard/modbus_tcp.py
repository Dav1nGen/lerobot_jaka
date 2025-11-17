from pymodbus.client import ModbusTcpClient
from loguru import logger


class ModbusTCP:

    def __init__(self, ip="192.168.1.8", port=502):
        self.__ip: str = ip
        self.__port: int = port
        self.__client: ModbusTcpClient = ModbusTcpClient(host=self.__ip,
                                                         port=self.__port)
        self.__if_connect_: bool = False

    def connect(self) -> None:
        if self.__client.connect():
            logger.info(f"Connect to {self.__ip} successfully")
            self.__if_connect_ = True
        else:
            logger.error(f"Connect to {self.__ip} failed")
            exit(1)

    def disconnect(self) -> None:
        if self.__client.is_socket_open():
            self.__client.close()
            self.__if_connect_ = False
            logger.info("Disconnected from Modbus server.")

    def write(self, coil_address, status_to_send) -> None:
        if not self.__if_connect_:
            logger.error("Modbus TCP not connected")
            exit(1)

        result = self.__client.write_coil(coil_address, status_to_send)

        if result.isError():
            logger.error(f"Modbus TCP write failed: {result}")
            raise IOError(f"Failed to write to coil {coil_address}")
        else:
            logger.info(
                f"Write to coil {coil_address} status {status_to_send} successfully!"
            )

    def read(self, coil_address):
        if not self.__if_connect_:
            logger.error("Modbus TCP not connected")
            exit(1)

        result = self.__client.read_coils(coil_address, 1)

        if result.isError():
            logger.error(f"Modbus TCP read failed: {result}")
            raise IOError(f"Failed to read coil {coil_address}")
        else:
            coil_status = result.bits[0]
            logger.info(f"Read coil {coil_address} status: {coil_status}")
            return coil_status

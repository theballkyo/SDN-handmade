from model.model import Model
import datetime


class FlowStat(Model):
    src_ip: str = str
    src_port: int = str

    dst_ip: str = str
    dst_port: int = int

    first_switched: datetime.datetime
    last_switched: datetime.datetime

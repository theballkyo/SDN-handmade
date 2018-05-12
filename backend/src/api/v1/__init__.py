from sanic import Blueprint

from .link import LinkView
from .device import DeviceView, DeviceNeighborView
from .path import PathView
from .flow import FlowView
from .flow_routing import FlowRoutingView

api_v1 = Blueprint('link', url_prefix='/')

api_v1.add_route(DeviceView.as_view(), '/device')
api_v1.add_route(DeviceView.as_view(), '/device/ifip/<ip>')
api_v1.add_route(DeviceView.as_view(), '/device/<id>')
api_v1.add_route(DeviceNeighborView.as_view(), '/device/<device_id>/neighbor')

api_v1.add_route(LinkView.as_view(), '/link')
api_v1.add_route(LinkView.as_view(), '/link/<id>')

api_v1.add_route(PathView.as_view(), '/path/<src_dst>')

api_v1.add_route(FlowView.as_view(), '/flow')
api_v1.add_route(FlowRoutingView.as_view(), '/flow/routing')
api_v1.add_route(FlowRoutingView.as_view(), '/flow/routing/<id>')

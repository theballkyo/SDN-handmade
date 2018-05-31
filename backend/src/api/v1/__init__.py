from sanic import Blueprint

from .device import DeviceView, DeviceNeighborView
from .flow import FlowView
from .flow_routing import FlowRoutingView
from .link import LinkView
from .neighbor import NeighborView
from .path import PathView
from .routing import RoutingView

api_v1 = Blueprint('link', url_prefix='/')

api_v1.add_route(DeviceView.as_view(), '/device')
api_v1.add_route(DeviceView.as_view(), '/device/ifip/<ip>')
api_v1.add_route(DeviceView.as_view(), '/device/<device_id>')
api_v1.add_route(DeviceNeighborView.as_view(), '/device/<device_id>/neighbor')

api_v1.add_route(LinkView.as_view(), '/link')
api_v1.add_route(LinkView.as_view(), '/link/<_id>')

api_v1.add_route(PathView.as_view(), '/path/<src_dst>')

api_v1.add_route(FlowView.as_view(), '/flow')
api_v1.add_route(FlowRoutingView.as_view(), '/flow/routing')
api_v1.add_route(FlowRoutingView.as_view(), '/flow/routing/<id>')

api_v1.add_route(RoutingView.as_view(), '/routes/<device_id>')

api_v1.add_route(NeighborView.as_view(), '/neighbor/<device_id>')

import struct
import sdn_utils
from netflow.netflow_types import FIELD_TYPES, convert_to_ip
import logging


class DataRecord:
    """This is a 'flow' as we want it from our source. What it contains is
    variable in NetFlow V9, so to work with the data you have to analyze the
    data dict keys (which are integers and can be mapped with the field_types
    dict).

    Should hold a 'data' dict with keys=field_type (integer) and value (in bytes).
    """

    def __init__(self):
        self.data = {}

    def __repr__(self):
        return "<DataRecord with data: {}>".format(self.data)


class DataFlowSet:
    """Holds one or multiple DataRecord which are all defined after the same
    template. This template is referenced in the field 'flowset_id' of this
    DataFlowSet and must not be zero.
    """

    def __init__(self, data, templates, header):
        pack = struct.unpack('!HH', data[:4])

        self.template_id = pack[0]  # flowset_id is reference to a template_id
        self.length = pack[1]
        self.flows = []

        offset = 4
        template = templates[self.template_id]

        # As the field lengths are variable V9 has padding to next 32 Bit
        padding_size = 4 - (self.length % 4)  # 4 Byte

        while offset <= (self.length - padding_size):
            new_record = DataRecord()

            for field in template.fields:
                flen = field.field_length
                fkey = FIELD_TYPES[field.field_type].lower()
                fdata = None

                # The length of the value byte slice is defined in the template
                dataslice = data[offset:offset + flen]

                # Better solution than struct.unpack with variable field length
                fdata = 0
                for idx, byte in enumerate(reversed(bytearray(dataslice))):
                    fdata += byte << (idx * 8)

                if field.field_type in (8, 12, 15):
                    fdata = convert_to_ip(fdata)

                if field.field_type in (21, 22):
                    fdata = int(fdata)
                    # logging.info("%s:%s:%s", header.timestamp, header.uptime, fdata)
                    fdata = (header.timestamp - (header.uptime / 1000)) + (fdata / 1000)
                    # Convert to second
                    # fdata /= 1000
                    fdata = sdn_utils.unix_to_datetime(fdata)

                new_record.data[fkey] = fdata

                offset += flen

            self.flows.append(new_record)

    def __repr__(self):
        return "<DataFlowSet with template {} of length {} holding {} flows>" \
            .format(self.template_id, self.length, len(self.flows))


class TemplateField:
    """A field with type identifier and length.
    """

    def __init__(self, field_type, field_length):
        self.field_type = field_type  # integer
        self.field_length = field_length  # bytes

    def __repr__(self):
        return "<TemplateField type {}:{}, length {}>".format(
            self.field_type, FIELD_TYPES[self.field_type], self.field_length)


class TemplateRecord:
    """A template record contained in a TemplateFlowSet.
    """

    def __init__(self, template_id, field_count, fields):
        self.template_id = template_id
        self.field_count = field_count
        self.fields = fields

    def __repr__(self):
        return "<TemplateRecord {} with {} fields: {}>".format(
            self.template_id, self.field_count,
            ' '.join([FIELD_TYPES[field.field_type] for field in self.fields]))


class TemplateFlowSet:
    """A template flowset, which holds an id that is used by data flowsets to
    reference back to the template. The template then has fields which hold
    identifiers of data types (eg "IP_SRC_ADDR", "PKTS"..). This way the flow
    sender can dynamically put together data flowsets.
    """

    def __init__(self, data):
        pack = struct.unpack('!HH', data[:4])
        self.flowset_id = pack[0]
        self.length = pack[1]  # total length including this header in bytes
        self.templates = {}

        offset = 4  # Skip header

        # Iterate through all template records in this template flowset
        while offset != self.length:
            pack = struct.unpack('!HH', data[offset:offset + 4])
            template_id = pack[0]
            field_count = pack[1]

            fields = []
            for field in range(field_count):
                # Get all fields of this template
                offset += 4
                field_type, field_length = struct.unpack('!HH', data[offset:offset + 4])
                field = TemplateField(field_type, field_length)
                fields.append(field)

            # Create a tempalte object with all collected data
            template = TemplateRecord(template_id, field_count, fields)

            # Append the new template to the global templates list
            self.templates[template.template_id] = template

            # Set offset to next template_id field
            offset += 4

    def __repr__(self):
        return "<TemplateFlowSet with id {} of length {} containing templates: {}>" \
            .format(self.flowset_id, self.length, self.templates.keys())


class Header:
    """The header of the ExportPacket.
    """

    def __init__(self, data):
        pack = struct.unpack('!HHIIII', data[:20])

        self.version = pack[0]
        self.count = pack[1]  # not sure if correct. softflowd: no of flows
        self.uptime = pack[2]
        self.timestamp = pack[3]  # UNIX Seconds
        self.sequence = pack[4]
        self.source_id = pack[5]


class ExportPacket:
    """The flow record holds the header and all template and data flowsets.
    """

    def __init__(self, data, templates):
        self.header = Header(data)
        # print(self.header.uptime, self.header.timestamp)
        self.templates = templates
        self.flows = []

        offset = 20
        while offset != len(data):
            flowset_id = struct.unpack('!H', data[offset:offset + 2])[0]
            if flowset_id == 0:  # TemplateFlowSet always have id 0
                tfs = TemplateFlowSet(data[offset:])
                self.templates.update(tfs.templates)
                offset += tfs.length
            else:
                dfs = DataFlowSet(data[offset:], self.templates, self.header)
                self.flows += dfs.flows
                offset += dfs.length

    def __repr__(self):
        return "<ExportPacket version {} counting {} records>".format(
            self.header.version, self.header.count)

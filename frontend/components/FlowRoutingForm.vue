<template>
  <div class="row">
    <div class="col-sm-12">
      <form class="card" @submit.prevent="onSubmit" method="post">
        <div class="card-header">
          <h3 class="card-title">Add static flow routing</h3>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-sm-12">
              <div class="form-group">
                <label for="name" class="form-label">Name</label>
                <input v-model="form.name" type="text" class="form-control" name="name" placeholder="Name">
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-sm-12">
              <label class="form-label">Flow match</label>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="src_ip" class="form-label">Source IP</label>
                <input v-model="form.src_ip" type="text" class="form-control" name="src_ip" placeholder="Source IP">
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="src_ip" class="form-label">Source netmask (e.g. 24 or 255.255.255.0)</label>
                <input v-model="form.src_subnet" type="text" class="form-control" name="src_subnet" placeholder="Source subnet">
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="src_port" class="form-label">Source port (any for any port)</label>
                <input v-model="form.src_port" type="text" class="form-control" name="src_port" placeholder="Source port">
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-md-4">
              <div class="form-group">
                <label for="dst_ip" class="form-label">Destination IP</label>
                <input v-model="form.dst_ip" type="text" class="form-control" name="dst_ip" placeholder="Destination IP">
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="dst_ip" class="form-label">Destination netmask (e.g. 24 or 255.255.255.0)</label>
                <input v-model="form.dst_subnet" type="text" class="form-control" name="dst_subnet" placeholder="Destination subnet">
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="dst_port" class="form-label">Destination port (any for any port)</label>
                <input v-model="form.dst_port" type="text" class="form-control" name="dst_port" placeholder="Destination port">
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-sm-12">
              <label class="form-label">Actions</label>
            </div>
          </div>

          <div class="row" v-for="(action, i) in form.actions" :key="i">
            <div class="col-md-4">
              <div class="form-group">
                <label class="form-label">Device IP</label>
                <select @change="onActionChange(i)" v-model="action.device_id" class="form-control">
                  <option value="0" disabled>Select device</option>
                  <option v-if="isFetching" disabled>Fetching data...</option>
                  <option v-for="device in devices" :key="device._id.$oid" :value="device._id.$oid">{{ device.name }} ({{device.management_ip}})</option>
                  <!-- <option value="192.168.1.5">R2.lab306 (192.168.1.5)</option>
                  <option value="192.168.1.6">R3.lab306 (192.168.1.6)</option> -->
                </select>
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-group">
                <label for="dst_ip" class="form-label">action</label>
                <select @change="onActionChange(i)" v-model="action.action" class="form-control">
                  <option value="0" disabled>Select action</option>
                  <option value="1">DROP</option>
                  <option :value="2">FORWARD Next-hop IP</option>
                  <option :value="3">FORWARD Next-interface</option>
                  <option disabled>Custom</option>
                  <option :value="4">FORWARD Next-hop IP (Custom)</option>
                  <option :value="5">FORWARD Next-interface (Custom)</option>
                </select>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="dst_port" class="form-label">{{ getActionDataText(action.action) }}</label>
                <select v-if="action.action === 2 || action.action === 3" v-model="action.data" class="form-control">
                  <option disabled>Select data</option>
                  <option v-if="isFetching" disabled>Fetching data...</option>
                  <option v-if="n.ip_addr && action.action === 2" v-for="(n, i) in nextHopID(action.device_id)" :key="i" :value="n.ip_addr">{{n.ip_addr}}</option>
                  <option v-if="action.action === 3" v-for="(d, i) in getDeviceIfByID(action.device_id)" :key="i" :value="d.description">{{d.description}}</option>
                </select>
                <input v-if="action.action === 4 || action.action === 5" v-model="action.data" type="text" class="form-control" placeholder="Enter data" />
              </div>
            </div>

            <div class="col-md-1">
              <div class="form-group">
                <label for="dst_port" class="form-label"></label>
                <button @click="removeAction(i)" type="button" class="btn btn-danger">X</button>
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-md-12">
              <div class="form-group">
                <button @click="addAction" type="button" class="btn btn-primary">Add action</button>
              </div>
            </div>
          </div>

          <!-- <div class="form-label">SNMP information</div> -->

          <div class="row">
            <div class="col-md-6">
              <button type="submit" class="btn btn-primary">Add static flow routing</button>
            </div>
            <div class="col-md-6 text-right">
              <button v-if="showRemove" @click="onRemoveClick" type="button" class="btn btn-danger">Remove</button>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import ipaddrMixin from "@/mixins/ipaddr";
import swal from "sweetalert";

export default {
  data() {
    return {
      form: {
        name: "",
        src_ip: "",
        src_subnet: "",
        src_port: "",
        dst_ip: "",
        dst_subnet: "",
        dst_port: "",
        actions: [
          {
            device_id: "0",
            action: 0,
            data: ""
          }
        ]
      },
      devices: [],
      nextHopIP_: {},
      isFetching: false,
      flowId: null
    };
  },
  props: {
    propForm: {
      default() {
        return {
          name: "",
          src_ip: "",
          src_subnet: "",
          src_port: "",
          dst_ip: "",
          dst_subnet: "",
          dst_port: "",
          actions: [
            {
              device_id: "0",
              action: 0,
              data: ""
            }
          ]
        };
      }
    },
    showRemove: {
      default: false
    }
  },
  mixins: [ipaddrMixin],
  async mounted() {
    try {
      const res = await this.$axios.$get("device");
      if (res) {
        this.devices = res.devices;
      }
    } catch (e) {}
    this.form = {
      ...this.propForm
    };
    console.log(this.form);
  },
  methods: {
    async onSubmit(n) {
      const src_subnet = this.subnetOrCidrToWildcard(this.form.src_subnet);
      const dst_subnet = this.subnetOrCidrToWildcard(this.form.dst_subnet);
      const form = {
        ...this.form,
        src_subnet,
        dst_subnet
      };
      this.$emit("onSubmit", form);
    },
    onRemoveClick() {
      this.$emit("onRemove", this.flowId);
    },
    async onActionChange(i) {
      const action = this.form.actions[i];
      const sel = action.action;
      const device_id = action.device_id;
      if (sel == 2) {
        this.isFetching = true;
        // Cache
        if (this.nextHopIP_[device_id] || device_id == "0") {
          this.isFetching = false;
          return;
        }
        if (!device_id) {
          console.log("Found undefind", action);
          return;
        }
        try {
          const res = await this.$axios.$get(`device/${device_id}/neighbor`);
          const neighbor = res.neighbor;
          this.nextHopIP_ = {
            ...this.nextHopIP_,
            [device_id]: neighbor
          };
        } catch (error) {}
        this.isFetching = false;
      }
    },
    nextHopID(id) {
      return this.nextHopIP_[id];
    },
    getDeviceIfByID(id) {
      const device = this.devices.find(device => device._id.$oid === id);
      if (device && device.interfaces) {
        return device.interfaces;
      }
      return [];
    },
    addAction() {
      this.form.actions.push({
        device_id: "0",
        action: 0,
        data: ""
      });
    },
    removeAction(i) {
      this.form.actions.splice(i, 1);
    },
    getActionDataText(actionId) {
      switch (actionId) {
        case 1:
          return "DROP";
        case 2:
        case 4:
          return "Next-hop IP";
        case 3:
        case 5:
          return "Interface name";
        default:
          return "";
      }
    },
    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }
  },
  watch: {
    async propForm(n, o) {
      this.flowId = n.flow_id;
      this.form = {
        ...n
      };
      await this.sleep(100);
      for (let i = 0; i < n.actions.length; i++) {
        await this.onActionChange(i);
        if (n.actions[i].action === 2) {
          if (
            !this.nextHopIP_[n.actions[i].device_id].find(
              v => v.ip_addr === n.actions[i].data
            )
          ) {
            n.actions[i].action = 4;
          }
        } else if (n.actions[i].action === 3) {
          if (
            !this.getDeviceIfByID(n.actions[i].device_id).find(
              v => v.description === n.actions[i].data
            )
          ) {
            n.actions[i].action = 5;
          }
        }
      }

      this.form = {
        ...n
      };
    }
  }
};
</script>

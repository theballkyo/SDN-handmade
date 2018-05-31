<template>
  <div class="row">
    <div class="col-12">
      <div>
        <button type="button" class="btn btn-info" @click="onClickToggleTab">
          <template v-if="toggleTab">Hide tab</template>
          <template v-else>Show tab</template>
        </button>
        <button type="button" :disabled="isFetching" @click="refresh" class="btn btn-primary btn-padding">Refresh</button>
      </div>
    </div>
    <div class="col-md-4">
      <div v-if="devices.length < 1 && toggleTab" class="list-group">
        <a class="list-group-item list-group-item-action flex-column align-items-start active">
          No devices.
        </a>
      </div>
      <div v-show="toggleTab" class="list-group">
        <a @click="onDeviceClick(i)" v-for="(device, i) in devices" :key="device.management_ip" :class="'list-group-item list-group-item-action flex-column align-items-start ' + (selectDevice === i ? 'active': '')">
          <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1">{{device.name}}</h5>
            <small>{{ formatDuration(device.uptime) }}</small>
          </div>

          <p class="d-flex w-100 justify-content-between">SSH Status:
            <span v-if="device.is_ssh_connect" class="badge badge-success">Connected</span>
            <span v-else class="badge badge-danger">Not connected !</span>
          </p>
          <p class="d-flex w-100 justify-content-between">Last SNMP fetch Status:
            <span v-if="device.is_snmp_connect" class="badge badge-success">Success</span>
            <span v-else class="badge badge-danger">Fail</span>
          </p>
          <p class="d-flex w-100 justify-content-between">IP: {{ device.management_ip }}
            <span class="badge badge-info">{{ device.type }}</span>
          </p>
        </a>
      </div>
    </div>
    <div :class="toggleTab ? 'col-md-8' : 'col-md-12'">
      <div class="card">
        <div class="card-header">
          <!-- <h3 class="title" v-if="selectDevice < 0">My device</h3> -->
          <h3 class="title" v-if="selectDevice >= 0">{{ devices[selectDevice].name }}
            <small>{{ devices[selectDevice].management_ip }}</small>
          </h3>
        </div>
        <div v-if="selectDevice < 0" class="card-body">
          Click a device to view more information.
        </div>
        <div v-if="selectDevice >= 0" class="card-body">
          <DeviceForm title="Device information" :isManagementIpDisabled="true" :removeBtn="true" :device="devices[selectDevice]" @onSubmit="onSubmit" @onRemoveClick="onRemoveClick" />
          <h2>Interfaces</h2>
          <table class="table">
            <thead>
              <tr>
                <th>name</th>
                <th>ip</th>
                <th>IN %</th>
                <th>OUT %</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(interf, i) in devices[selectDevice].interfaces" :key="i">
                <td>{{interf.description}}</td>
                <td>{{interf.ipv4_address}}</td>
                <td>{{parseFloat(interf.bw_in_usage_percent).toFixed(2) || 0.00}}</td>
                <td>{{parseFloat(interf.bw_out_usage_percent).toFixed(2) || 0.00}}</td>
              </tr>
            </tbody>
          </table>
          <h2>Routes</h2>
          <table class="table">
            <thead>
              <tr>
                <th>Protocol</th>
                <th>Destination</th>
                <th>Next-hop</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="route in routes" :key="route._id.$oid">
                <td>{{ getRouteProtoText(route.proto) }}</td>
                <td>{{ route.dst }}/{{ subnetToCidr(route.mask) }}</td>
                <td>{{ route.next_hop }}</td>
              </tr>
            </tbody>
          </table>
          <br/>
          <h2>Neighbor</h2>
          <table class="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Neighbor IP</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(neighbor, i) in neighbors" :key="i">
                <td>{{ neighbor.name }}</td>
                <td>{{ neighbor.ip_addr }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import DeviceForm from "@/components/DeviceForm";
import ipaddrMixin from "@/mixins/ipaddr";

const ROUTE_PROTOCOL = {
  1: "other",
  2: "local",
  3: "netmgmt",
  4: "icmp",
  5: "egp",
  6: "ggp",
  7: "hello",
  8: "rip",
  9: "isIs",
  10: "esIs",
  11: "ciscoIgrp",
  12: "bbnSpfIgp",
  13: "ospf",
  14: "bgp",
  15: "idpr",
  16: "ciscoEigrp"
};

export default {
  data() {
    return {
      toggleTab: true,
      devices: [],
      selectDevice: -1,
      isFetching: false,
      routes: [],
      neighbors: []
    };
  },
  components: {
    DeviceForm
  },
  mixins: [ipaddrMixin],
  async mounted() {
    await this.fetchData();
  },
  methods: {
    async refresh() {
      this.selectDevice = -1;
      await this.fetchData();
    },
    async fetchData() {
      this.isFetching = true;
      try {
        const res = await this.$axios.$get("device");
        this.devices = res.devices;
        this.devices.sort((a, b) => {
          if (a.name < b.name) {
            return -1;
          }
          if (a.name > b.name) {
            return 1;
          }
          return 0;
        });
      } catch (e) {}
      this.isFetching = false;
    },
    formatDuration(time) {
      let sec_num = parseInt(time, 10); // don't forget the second param
      sec_num = Math.floor(sec_num / 100);
      let hours = Math.floor(sec_num / 3600);
      let minutes = Math.floor((sec_num - hours * 3600) / 60);
      let seconds = sec_num - hours * 3600 - minutes * 60;

      if (hours < 10) {
        hours = "0" + hours;
      }
      if (minutes < 10) {
        minutes = "0" + minutes;
      }
      if (seconds < 10) {
        seconds = "0" + seconds;
      }
      return `${hours} hours, ${minutes} minutes`;
    },
    getRouteProtoText(proto) {
      return ROUTE_PROTOCOL[proto];
    },
    async onSubmit(form) {
      console.log(form);
      const willUpdate = await swal({
        title: "Are you sure?",
        text: "You want to update information for this device",
        icon: "warning",
        buttons: true,
        dangerMode: true,
        buttons: ["No", "Yes"]
      });
      if (willUpdate) {
        const res = await this.$axios.$patch("device/" + form._id, form);
        if (res.status) {
          swal("Device has been updated!", {
            icon: "success"
          });
        }
      }
    },
    async onRemoveClick(form) {
      console.log(form);
      const willDelete = await swal({
        title: "Are you sure?",
        text: "You want to remove this device",
        icon: "warning",
        buttons: true,
        dangerMode: true,
        buttons: ["No", "Yes"]
      });
      if (willDelete) {
        const res = await this.$axios.$delete("device", {
          params: { device_id: form._id }
        });
        swal("Device has been deleted!", {
          icon: "success"
        });
      }
    },
    async onDeviceClick(i) {
      this.selectDevice = i;
      const device = this.devices[i];
      // Get routes
      let res = await this.$axios.$get(`routes/${device._id.$oid}`);
      this.routes = res.routes;
      // Get neighbor
      res = await this.$axios.$get(`neighbor/${device._id.$oid}`)
      this.neighbors = res.neighbors.neighbor
    },
    onClickToggleTab() {
      this.toggleTab = !this.toggleTab;
    }
  }
};
</script>

<style scoped>
.btn-padding {
  padding-left: 12px;
}
</style>


<template>
  <div class="row">
    <div class="col-12">
      <p>
        <button :disabled="isFetching" @click="refresh" class="btn btn-primary">Refresh</button>
      </p>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Flow routing</h3>
        </div>
        <div v-if="isFetching" class="text-center card-body">
          Fetching...
        </div>
        <div v-else-if="flows.length > 0" class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Type</th>
                <th scope="col">Status</th>
                <th scope="col">Source</th>
                <th scope="col">Destination</th>
                <th scope="col">actions</th>
                <th scope="col"></th>
                <!-- <th scope="col">IN_BYTES</th>
                <th scope="col">first switched</th>
                <th scope="col">last switched</th> -->
              </tr>
            </thead>
            <tbody>
              <tr v-for="(flow, i) in flows" :key="i">
                <th scope="row">{{i}}</th>
                <td>{{getTypeName(flow.info.submit_from.type || 0)}}</td>
                <td>{{getStatusText(flow.info.status)}}</td>
                <td>{{flow.src_ip}}/{{wildcardToCidr(flow.src_wildcard)}} [{{flow.src_port}}]</td>
                <td>{{flow.dst_ip}}/{{wildcardToCidr(flow.dst_wildcard)}} [{{flow.dst_port}}]</td>
                <td>
                  <table class="table">
                    <thead>
                      <tr>
                        <th>Device</th>
                        <th>Action</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(action, i2) in flow.actions" :key="i2">
                        <td>{{getDeviceNameById(action.device_id.$oid)}}</td>
                        <td>{{getActionName(action.action)}}</td>
                        <td>{{action.data}}</td>
                      </tr>
                    </tbody>
                  </table>
                </td>
                <td>
                  <router-link :to="'/flow/routing/' + flow._id.$oid" v-if="flow.info.submit_from.type === 1" class="btn btn-info">Edit</router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-center card-body">
          No flow routing to show.
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ipaddrMixin from "@/mixins/ipaddr";

const TYPES = {
  1: "static",
  2: "automate"
};

const STATUS = {
  0: "wating apply",
  3: "active"
};

const ACTIONS = {
  1: "DROP",
  2: "Next-hop IP",
  3: "Exit Interface"
};
export default {
  data() {
    return {
      flows: [],
      showCidr: true,
      isFetching: false,
      devices: {}
    };
  },
  mixins: [ipaddrMixin],
  async mounted() {
    await this.fetchDevice();
    await this.fetchData();
  },
  methods: {
    async refresh() {
      if (this.isFetching) {
        return;
      }
      await this.fetchData();
    },
    async fetchData() {
      this.isFetching = true;
      try {
        const fetchData = await this.$axios.$get("flow/routing");
        this.flows = fetchData.flows;
      } catch (e) {}
      this.isFetching = false;
    },
    async fetchDevice() {
      try {
        const res = await this.$axios.$get("device");
        for (let device in res.devices) {
          this.devices[res.devices[device]._id.$oid] = res.devices[device];
        }
      } catch (e) {}
    },
    getDeviceNameById(id) {
      return this.devices[id].name;
    },
    getActionName(id) {
      return ACTIONS[id];
    },
    getTypeName(id) {
      return TYPES[id];
    },
    getStatusText(id) {
      return STATUS[id];
    },
    async onRemoveClick(id) {
      swal({
        title: "Are you sure?",
        text: "You want to remove this device",
        icon: "warning",
        buttons: true,
        dangerMode: true
      }).then(willDelete => {
        if (willDelete) {
          swal("Poof! Your imaginary file has been deleted!", {
            icon: "success"
          });
        } else {
          swal("Your imaginary file is safe!");
        }
      });
    }
  }
};
</script>

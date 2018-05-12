<template>
  <div class="row">
    <div class="col-12">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Flow routing</h3>
        </div>
        <div class="table-responsive">
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
                        <td>{{action.management_ip}}</td>
                        <td>{{getActionName(action.action)}}</td>
                        <td>{{action.data}}</td>
                      </tr>
                    </tbody>
                  </table>
                </td>
                <td>
                  <router-link :to="'/flow/routing/' + flow._id.$oid" v-if="flow.info.submit_from.type === 1" class="btn btn-info">Edit</router-link>
                  <hr/>
                  <button v-if="flow.info.submit_from.type === 1" @click="onRemoveClick(flow.id)" class="btn btn-danger">Remove</button>
                </td>
              </tr>

              <tr>
                <th scope="row">1</th>
                <td>Static</td>
                <td>{{ cidrToWildcard(24) }}</td>
                <td>172.16.31.100:80</td>
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
                      <tr>
                        <td>192.168.1.1</td>
                        <td>Drop</td>
                        <td></td>
                      </tr>
                    </tbody>
                  </table>
                </td>
                <td>
                  <button class="btn btn-danger">Remove</button>
                </td>
              </tr>

              <tr>
                <th scope="row">2</th>
                <td>Automate</td>
                <td>172.16.0.100</td>
                <td>172.16.31.100</td>
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
                      <tr>
                        <td>192.168.1.1</td>
                        <td>Next-hop IP</td>
                        <td>192.168.1.2</td>
                      </tr>
                      <tr>
                        <td>192.168.1.2</td>
                        <td>Next-hop IP</td>
                        <td>192.168.1.6</td>
                      </tr>
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
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
      showCidr: true
    };
  },
  mixins: [ipaddrMixin],
  async mounted() {
    await this.fetchData();
  },
  methods: {
    async fetchData() {
      const fetchData = await this.$axios.$get("flow/routing");
      this.flows = fetchData.flows;
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

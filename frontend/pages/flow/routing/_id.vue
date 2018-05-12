<template>
  <div class="row">
    <div class="col-sm-12">
      <form class="card" @submit.prevent="onSubmit" method="post">
        <div class="card-header">
          <h3 class="card-title">Update static flow routing - Flow ID: {{ form.flow_id }}</h3>
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
                <select v-model="action.management_ip" class="form-control">
                  <option value="0" disabled>Select device</option>
                  <option value="192.168.1.1">R1.lab306 (192.168.1.1)</option>
                  <option value="192.168.1.5">R2.lab306 (192.168.1.5)</option>
                  <option value="192.168.1.6">R3.lab306 (192.168.1.6)</option>
                </select>
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-group">
                <label for="dst_ip" class="form-label">action</label>
                <select v-model="action.action" class="form-control">
                  <option value="0" disabled>Select action</option>
                  <option value="1">DROP</option>
                  <option value="2">FORWARD Next-hop IP</option>
                  <option value="3">FORWARD Next-interface</option>
                  <option disabled>Custom</option>
                  <option value="4">FORWARD Next-hop IP (Custom)</option>
                  <option value="5">FORWARD Next-interface (Custom)</option>
                </select>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="dst_port" class="form-label">{{ getActionDataText(action.action) }}</label>
                <select v-if="action.action == '2' || action.action == '3'" v-model="action.data" class="form-control">
                  <option value="192.168.1.2">192.168.1.2</option>
                  <option value="Serial 0/0/1">Serial 0/0/1</option>
                  <option value="GigabitEthernet 0/0">GigabitEthernet 0/0</option>
                </select>
                <input v-if="action.action == '4' || action.action == '5'" v-model="action.data" type="text" class="form-control" placeholder="Enter data" />
                <input v-if="action.action == '1'" placeholder="DROP" class="form-control" disabled/>
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
            <div class="col-md-12">
              <button type="submit" class="btn btn-success">Update static flow routing</button> or
              <button type="button" @click="onRemoveClick" class="btn btn-danger">Remove static flow routing</button>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import ipaddrMixin from "@/mixins/ipaddr";

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
        flow_id: 0,
        actions: [
          {
            management_ip: 0,
            action: 0,
            data: ""
          }
        ]
      }
    };
  },
  mixins: [ipaddrMixin],
  async mounted() {
    const data = await this.$axios.$get(
      "flow/routing/" + this.$route.params.id
    );
    let flow = data.flow;
    this.form.name = flow.name;
    this.form.src_ip = flow.src_ip;
    this.form.src_port = flow.src_port;
    this.form.src_subnet = this.wildcardToSubnet(flow.src_wildcard);
    this.form.dst_ip = flow.dst_ip;
    this.form.dst_port = flow.dst_port;
    this.form.dst_subnet = this.wildcardToSubnet(flow.dst_wildcard);
    this.form.actions = [];
    for (let obj in flow.actions) {
      this.form.actions.push(flow.actions[obj]);
    }
    this.form.flow_id = flow.flow_id;
  },
  methods: {
    async onSubmit(n) {
      // this.form.src_subnet = this.subnetOrCidrToWildcard(this.form.src_subnet);
      // this.form.dst_subnet = this.subnetOrCidrToWildcard(this.form.dst_subnet);
      await this.$axios.$patch("flow/routing", {
        ...this.form,
        src_subnet: this.subnetOrCidrToWildcard(this.form.src_subnet),
        dst_subnet: this.subnetOrCidrToWildcard(this.form.dst_subnet)
      });
      console.log(this.form);
    },
    addAction() {
      this.form.actions.push({
        device_ip: 0,
        action: 0,
        action_data: ""
      });
    },
    removeAction(i) {
      this.form.actions.splice(i, 1);
    },
    getActionDataText(actionId) {
      actionId = parseInt(actionId);
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
    async onRemoveClick() {
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
  },
  watch: {
    // Todo watch form
  }
};
</script>

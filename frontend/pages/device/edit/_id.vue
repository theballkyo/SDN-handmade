<template>
  <div class="row">
    <div class="col-sm-12">
      <form class="card" @submit.prevent="onSubmit" method="post">
        <div class="card-header">
          <h3 class="card-title">Add device</h3>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <div class="form-group">
                <label class="form-label">Management IP</label>
                <input v-model="form.management_ip" type="text" class="form-control" name="management_ip" placeholder="Device Management IP">
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group">
                <label for="device_type">Device type</label>
                <select v-model="form.type" class="form-control" id="device_type">
                  <option value="cisco_ios">Cisco (IOS)</option>
                </select>
              </div>
            </div>
          </div>
          <!-- <div class="form-label">Remote access (SSH) information</div> -->
          <div class="row">
            <div class="col-md-4">
              <div class="form-group">
                <label class="form-label">SSH Username</label>
                <input v-model="form.ssh_info.username" type="text" class="form-control" name="ssh_username" placeholder="SSH Username">
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label class="form-label">SSH Password</label>
                <input v-model="form.ssh_info.password" type="password" class="form-control" name="ssh_password" placeholder="SSH Password">
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label class="form-label">SSH Port</label>
                <input v-model.number="form.ssh_info.port" type="number" class="form-control" name="ssh_port" placeholder="SSH Port">
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label class="form-label">Enable password (secret)</label>
                <input v-model="form.ssh_info.secret" type="password" class="form-control" name="enable_password" placeholder="Enable password">
              </div>
            </div>
          </div>

          <!-- <div class="form-label">SNMP information</div> -->
          <div class="row">
            <div class="col-md-4">
              <div class="form-group">
                <label for="snmp_version">SNMP version</label>
                <select v-model="form.snmp_info.version" class="form-control" id="snmp_version">
                  <option value="2c">2c</option>
                </select>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label class="form-label">SNMP Community string</label>
                <input v-model="form.snmp_info.community" type="text" class="form-control" name="snmp_community_string" placeholder="SNMP Community string">
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label class="form-label">SNMP Port</label>
                <input v-model.number="form.snmp_info.port" type="number" class="form-control" name="snmp_port" placeholder="SNMP Port">
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-md-12">
              <button type="submit" class="btn btn-success">Update device</button> or
              <button type="button" @click="onRemoveClick" class="btn btn-danger">Remove device</button>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import swal from "sweetalert";

export default {
  data() {
    return {
      form: {
        management_ip: "",
        type: "cisco_ios",
        ssh_info: {
          username: "",
          password: "",
          port: 22,
          secret: ""
        },
        snmp_info: {
          version: "2c",
          community: "public",
          port: 161
        }
      }
    };
  },
  async mounted() {
    const data = await this.$axios.$get("device/" + this.$route.params.id);
    this.form.management_ip = data.device.management_ip;
    this.form.type = data.device.type;
    this.form.ssh_info = data.device.ssh_info;
    this.form.snmp_info = data.device.snmp_info;
  },
  methods: {
    async onSubmit(n) {
      await this.$axios.$put("device", this.form);
      console.log(this.form);
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
  }
};
</script>

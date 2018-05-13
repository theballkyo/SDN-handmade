<template>
  <FlowRoutingForm @onSubmit="onSubmit" />
</template>

<script>
import ipaddrMixin from "@/mixins/ipaddr";
import swal from "sweetalert";
import FlowRoutingForm from "@/components/FlowRoutingForm";

export default {
  data() {
    return {
      devices: [],
      nextHopIP_: {},
      isFetching: false
    };
  },
  mixins: [ipaddrMixin],
  components: {
    FlowRoutingForm
  },
  async mounted() {
    try {
      const res = await this.$axios.$get("device");
      if (res) {
        this.devices = res.devices;
      }
    } catch (e) {}
  },
  methods: {
    async onSubmit(form) {
      form.actions = form.actions.map(action => {
        if (action.action === 4) {
          action.action = 2;
        } else if (action.action === 5) {
          action.action = 3;
        }
        return action;
      });
      console.log(form);
      const res = await this.$axios.$post("flow/routing", form);
      if (res.success) {
        await swal("Successful", "Added static flow routing.", "success");
        this.$router.replace("/flow/routing");
      } else {
        swal("Fail !", res.message, "error");
      }
    },
    nextHopIP(ip) {
      return this.nextHopIP_[ip];
    },
    getDeviceIfByIP(ip) {
      const device = this.devices.find(device => device.management_ip === ip);
      if (device && device.interfaces) {
        return device.interfaces;
      }
      return [];
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
    }
  },
  watch: {
    // Todo watch form
  }
};
</script>

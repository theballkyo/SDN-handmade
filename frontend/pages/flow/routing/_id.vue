<template>
  <FlowRoutingForm :showRemove="true" :propForm="form" @onSubmit="onSubmit" @onRemove="onRemove" />
</template>

<script>
import ipaddrMixin from "@/mixins/ipaddr";
import swal from "sweetalert";
import FlowRoutingForm from "@/components/FlowRoutingForm";

export default {
  data() {
    return {
      form: {}
    };
  },
  mixins: [ipaddrMixin],
  components: {
    FlowRoutingForm
  },
  async mounted() {
    const data = await this.$axios.$get(
      "flow/routing/" + this.$route.params.id
    );
    let flow = data.flow;
    let form = {};
    form.name = flow.name;
    form.src_ip = flow.src_ip;
    form.src_port = flow.src_port;
    form.src_subnet = this.wildcardToSubnet(flow.src_wildcard);
    form.dst_ip = flow.dst_ip;
    form.dst_port = flow.dst_port;
    form.dst_subnet = this.wildcardToSubnet(flow.dst_wildcard);
    form.actions = [];
    for (let obj in flow.actions) {
      flow.actions[obj].device_id = flow.actions[obj].device_id.$oid;
      form.actions.push(flow.actions[obj]);
    }
    form.flow_id = flow.flow_id;
    this.form = {
      ...form
    };
    console.log(this.form);
  },
  methods: {
    async onSubmit(n) {
      try {
        const res = await this.$axios.$patch("flow/routing", {
          ...this.form,
          src_subnet: this.subnetOrCidrToWildcard(this.form.src_subnet),
          dst_subnet: this.subnetOrCidrToWildcard(this.form.dst_subnet)
        });
        if (res.success) {
          swal("Successful", "Updated flow routing !", "success");
          this.$router.replace("/flow/routing");
        }
      } catch (e) {}
    },
    async onRemove(id) {
      const willDelete = await swal({
        title: "Are you sure?",
        text: "You want to remove this flow routing",
        icon: "warning",
        buttons: true,
        dangerMode: true,
        buttons: ["No", "Yes"]
      });
      if (willDelete) {
        const res = await this.$axios.$delete("flow/routing", {
          params: { flow_id: this.form.flow_id }
        });
        swal("Successful", "Removed flow routing !", "success");
        this.$router.replace("/flow/routing");
      }
    }
  },
  watch: {
    // Todo watch form
  }
};
</script>

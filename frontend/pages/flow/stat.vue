<template>
  <div class="row">
    <div class="col-12">
      <p>
        <button :disabled="isFetching" @click="refresh" class="btn btn-primary">Refresh</button>
      </p>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Flow stat</h3>
        </div>
        <div v-if="isFetching" class="text-center card-body">
          Fetching...
        </div>
        <div v-else-if="flows.length > 0" class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">From</th>
                <th scope="col">Source</th>
                <th scope="col">Destination</th>
                <th scope="col">IN_PKTS</th>
                <th scope="col">IN_BYTES</th>
                <th scope="col">first switched</th>
                <th scope="col">last switched</th>
              </tr>
            </thead>
            <tbody>
              <!-- <tr>
                <th scope="row">1</th>
                <td>192.168.1.1</td>
                <td>172.16.0.100:7842</td>
                <td>172.16.31.100:5201</td>
                <td>2450</td>
                <td>1479800</td>
                <td>30/04/2018 08:43:26</td>
                <td>30/04/2018 08:44:26</td>
              </tr>
              <tr>
                <th scope="row">2</th>
                <td>192.168.1.2</td>
                <td>172.16.0.100:7842</td>
                <td>172.16.31.100:5201</td>
                <td>2421</td>
                <td>1462284</td>
                <td>30/04/2018 08:43:26</td>
                <td>30/04/2018 08:44:26</td>
              </tr> -->
              <tr v-for="(flow, i) in flows" :key="i">
                <th scope="row">{{ i + 1 }}</th>
                <td>{{ flow.from_ip }}</td>
                <td>{{ flow.ipv4_src_addr}}:{{ flow.l4_src_port }}</td>
                <td>{{ flow.ipv4_dst_addr}}:{{ flow.l4_dst_port }}</td>
                <td>{{ flow.in_pkts }}</td>
                <td>{{ flow.in_bytes }}</td>
                <td>{{ flow.first_switched.$date / 1000 |moment('timezone', 'Asia/Bangkok', 'DD/MM/YYYY hh:mm:ss') }}</td>
                <td>{{ flow.last_switched.$date / 1000 | moment('timezone', 'Asia/Bangkok', 'DD/MM/YYYY hh:mm:ss') }}</td>
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
export default {
  data() {
    return {
      flows: [],
      isFetching: false
    };
  },
  async mounted() {
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
        const fetchData = await this.$axios.$get("flow");
        this.flows = fetchData.flows;
      } catch (e) {}
      this.isFetching = false;
    }
  }
};
</script>

<template>
  <div class="row">
    <div class="col-12">
      <h3 class="btn btn-info" @click="onClickToggleTab">
        <template v-if="toggleTab">Hide tab</template>
        <template v-else>Show tab</template>
      </h3>
    </div>
    <div class="col-md-4">
      <div v-show="toggleTab" class="list-group">
        <a @click="onDeviceClick(i)" v-for="(device, i) in devices" :key="device.management_ip" :class="'list-group-item list-group-item-action flex-column align-items-start ' + (selectDevice === i ? 'active': '')">
          <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1">{{device.name}}</h5>
            <small>{{ formatDuration(device.uptime) }}</small>
          </div>
          <p class="mb-1">{{ device.type }}</p>
          <p class="mb-1">{{ device.management_ip }}</p>
        </a>
      </div>
    </div>
    <div :class="toggleTab ? 'col-md-8' : 'col-md-12'">
      <div class="card">
        <div class="card-header">
          <h3 v-if="selectDevice < 0">Card header</h3>
          <h3 class="title" v-else>{{ devices[selectDevice].name }}
            <small>{{ devices[selectDevice].management_ip }}</small>
          </h3>
        </div>
        <div v-if="selectDevice < 0" class="card-body">
          Click a device to view more information.
        </div>
        <div v-if="selectDevice >= 0" class="card-body">
          <DeviceForm title="Device information" :isManagementIpDisabled="true" :removeBtn="true" :device="devices[selectDevice]" @onSubmit="onSubmit" @onRemoveClick="onRemoveClick" />
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
                <td>{{interf.bw_in_usage_percent}}</td>
                <td>{{interf.bw_out_usage_percent}}</td>
              </tr>
            </tbody>
          </table>
          Route...<br/> CDP... <br/>
        </div>
      </div>
    </div>
    <!-- <div class="col-md-6 col-xl-4" v-for="device in devices" :key="device.management_ip">
      <div class="card">
        <div class="card-status bg-blue"></div>
        <div class="card-header">
          <h3 class="card-title">{{ device.name || 'Unknown' }}</h3>
        </div>
        <div class="card-body">
          <p>Management IP: {{ device.management_ip }}</p>
          <p>Type: {{ device.type }}</p>
          <p>Uptime: {{ formatDuration(device.uptime) }}</p>
        </div>
        <div class="card-footer">
          <router-link class="btn btn-info" :to="'/device/edit/' + device._id.$oid">Edit</router-link> or 
          <span class="btn btn-danger">Remove</span>
        </div>
      </div>
    </div> -->
  </div>
</template>

<script>
import DeviceForm from "@/components/DeviceForm";

export default {
  data() {
    return {
      toggleTab: true,
      devices: [],
      selectDevice: -1
    };
  },
  components: {
    DeviceForm
  },
  async mounted() {
    const rawData = await this.$axios.$get("device");
    this.devices = rawData.devices;
    this.devices.sort((a, b) => {
      if (a.name < b.name) {
        return -1;
      }
      if (a.name > b.name) {
        return 1;
      }
      return 0;
    });
  },
  methods: {
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
    onSubmit(form) {
      // console.log(form);
    },
    async onRemoveClick(form) {
      const willDelete = await swal({
        title: "Are you sure?",
        text: "You want to remove this device",
        icon: "warning",
        buttons: true,
        dangerMode: true,
        buttons: ["No", "Yes"]
      });
      if (willDelete) {
        swal("Poof! Your imaginary file has been deleted!", {
          icon: "success"
        });
      }
    },
    onDeviceClick(i) {
      this.selectDevice = i;
      // console.log(this.devices[i]);
    },
    onClickToggleTab() {
      this.toggleTab = !this.toggleTab;
    }
  }
};
</script>

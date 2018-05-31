<template>
  <div ref="visualization" :style="{
    height:height + 'px',
    border: '1px solid lightgray'}"></div>
</template>

<script>
import vis from "vis";
const events = [
  "click",
  "contextmenu",
  "doubleClick",
  "changed",
  "rangechange",
  "rangechanged",
  "timechange",
  "timechanged"
];
export default {
  data() {
    return {
      // width: 400,
      height: 600,
      graphData: null
    };
  },
  props: {
    nodes: {
      require: true
    },
    edges: {
      require: true
    },
    physics: {
      default: true
    }
  },
  watch: {
    nodes(n, o) {
      // Todo Remove nodes is not exist !
      this.graphData.nodes.update(n);
      // this.graph2d.stabilize();
      // this.graphData.nodes.clear();
      // this.graphData.nodes.add(n);
    },
    edges(n, o) {
      this.graphData.edges.update(n);
      // this.graphData.edges.clear();
      // this.graphData.edges.add(n);
      // this.graph2d.stabilize();
    }
  },
  mounted() {
    const container = this.$refs.visualization;

    this.graphData = {
      nodes: new vis.DataSet(this.nodes),
      edges: new vis.DataSet(this.edges)
    };
    const options = {
      edges: {
        smooth: {
          forceDirection: "none"
        }
      },
      physics: {
        enabled: true,
        minVelocity: 0.75
      },
      nodes: {
        shape: "dot"
        // scaling: {
        //   customScalingFunction: function(min, max, total, value) {
        //     return value / total;
        //   },
        //   min: 5,
        //   max: 150
        // }
        // scaling: {
        //   label: {
        //     min: 8,
        //     max: 20
        //   }
        // }
      }
    };
    this.graph2d = new vis.Network(container, this.graphData, options);
    events.forEach(eventName => {
      this.graph2d.on(eventName, props => this.$emit(eventName, props));
    });
  }
};
</script>

<style>
@import "~/node_modules/vis/dist/vis.min.css";
</style>

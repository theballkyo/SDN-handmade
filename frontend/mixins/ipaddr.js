let mixin = {
  methods: {
    wildcardToCidr(wildcard) {
      if (!wildcard) return ""
      const spliter = wildcard.split(".");
      let cidr = 0;
      const subnet_bit = spliter.forEach(n => {
        return parseInt(n)
          .toString(2)
          .padStart(8, "0")
          .split("")
          .forEach(b => {
            if (1 - b === 1) {
              cidr++;
            }
          });
      });
      return cidr;
    },
    wildcardToSubnet(wildcard) {
      if (!wildcard) return ""
      const spliter = wildcard.split(".");
      // let cidr = 0;
      const subnet_bit = spliter.map(n => {
        const bits = parseInt(n)
          .toString(2)
          .padStart(8, "0")
          .split("")
          .map(b => (1 - b).toString())
          .join("");
        return parseInt(bits, 2);
      });
      return subnet_bit.join(".");
    },
    subnetToWildcard(subnet) {
      return subnet.split(".")
        .map(s => parseInt(parseInt(s)
          .toString(2)
          .padStart(8, "0")
          .split("")
          .map(b => (1 - b).toString())
          .join(""), 2)).join(".")
    },
    subnetToCidr(subnet) {
      return this.wildcardToCidr(this.subnetToWildcard(subnet))
    },
    cidrToWildcard(cidr) {
      let subnet = ""
      let _subnet = ""
      for (let i = 1; i <= 32; i++) {
        if (i <= cidr) {
          _subnet += "1"
        } else {
          _subnet += "0"
        }
        if (i % 8 === 0) {
          subnet += parseInt(_subnet.split("").map(b => (1 - b).toString()).join(""), 2).toString()
          if (i !== 32) {
            subnet += "."
          }
          _subnet = ""
        }
      }
      return subnet
    },
    subnetOrCidrToWildcard(val) {
      // Auto detection val is subnet or cidr
      if (val.length === 1 || val.length === 2) {
        return this.cidrToWildcard(val)
      }
      return this.subnetToWildcard(val)
    }
  }
}

export default mixin
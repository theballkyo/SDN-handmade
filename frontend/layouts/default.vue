<template>
  <div>
    <div class="header collapse d-lg-flex p-0" id="headerMenuCollapse">
      <div class="container">
        <div class="row row align-items-center">
          <div class="col col-lg order-lg-first">
            <ul class="nav nav-tabs border-0 flex-column flex-lg-row">
              <!-- <li class="nav-item">
                <router-link active-class="active" class="nav-link" aria-current="true" data-toggle="false" to="/" exact>
                  <i class="fe fe-home"></i> Home</router-link>
              </li> -->
              <li class="nav-item">
                <router-link active-class="active" class="nav-link" aria-current="true" data-toggle="false" to="/graph">
                  <i class="fe fe-box"></i> Graph</router-link>
              </li>
              <li class="nav-item">
                <a href="javascript:void(0)" class="nav-link" data-toggle="dropdown">
                  <i class="fe fe-box"></i> Device</a>
                <div class="dropdown-menu dropdown-menu-arrow">
                  <router-link data-toggle="false" active-class="active" class="dropdown-item " to="/device/add">Add new</router-link>
                  <router-link data-toggle="false" active-class="active" class="dropdown-item " to="/device/view">View</router-link>
                </div>
              </li>
              <li class="nav-item">
                <a href="javascript:void(0)" class="nav-link" data-toggle="dropdown">
                  <i class="fe fe-box"></i> Flow</a>
                <div class="dropdown-menu dropdown-menu-arrow">
                  <router-link active-class="active" class="dropdown-item" to="/flow/stat" exact>Flow stat</router-link>
                  <router-link data-toggle="false" active-class="active" class="dropdown-item" to="/flow/routing" exact>Flow routing</router-link>
                  <router-link data-toggle="false" active-class="active" class="dropdown-item" to="/flow/routing/add" exact>Add static flow routing</router-link>
                </div>
              </li>
              <li class="nav-item">
                <a href="javascript:void(0)" class="nav-link" data-toggle="dropdown">
                  <i class="fe fe-box"></i> System</a>
                <div class="dropdown-menu dropdown-menu-arrow">
                  <!-- <router-link data-toggle="false" active-class="active" class="dropdown-item " to="/system/info" exact>View</router-link> -->
                  <router-link data-toggle="false" active-class="active" class="dropdown-item " to="/system/setting" exact>Setting</router-link>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <div class="page">
      <div class="page-main">
        <div class="my-3 my-md-5">
          <div class="container">
            <div class="page-header">
              <h1 class="page-title">

                <!-- SDN handmade management -->
              </h1>
            </div>

            <nuxt/>

          </div>
        </div>
      </div>
    </div>
    <footer class="footer">
      <div class="container">
        <div class="row align-items-center flex-row-reverse">
          <div class="col-auto ml-lg-auto">
            <div class="row align-items-center">

            </div>
          </div>
          <div class="col-12 col-lg-auto mt-3 mt-lg-0 text-center">
            Copyright © 2018 Developed by
            <a href="https://github.com/theballkyo">Theballkyo</a>. Theme by
            <a href="https://codecalm.net" target="_blank">codecalm.net</a> All rights reserved. Version {{ version }}
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  data() {
    return {
      version: "1.0.0 Release"
    };
  }
};
</script>

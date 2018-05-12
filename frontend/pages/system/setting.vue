<template>
  <div class="row">
    <div class="col-12">
      <form @submit.prevent="onSubmit" method="post">
        <div class="card">
          <div class="card-header">Setting</div>
          <div class="card-body">
            <div class="row">
              <div class="col-4">
                <div class="form-group">
                  <label for="name" class="form-label">Threshold (%)</label>
                  <input type="text" class="form-control" name="name" placeholder="Threshold">
                </div>
              </div>
            </div>
          </div>
          <div class="card-footer">
            <div class="row">
              <div class="col-md-12">
                <button type="submit" class="btn btn-primary">Update setting</button>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

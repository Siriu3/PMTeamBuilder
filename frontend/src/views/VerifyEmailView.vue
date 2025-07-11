<template>
  <div class="verify-email-view">
    <EmailVerificationView />
  </div>
</template>

<script setup>
import EmailVerificationView from '../components/Auth/EmailVerificationView.vue';
</script>

<style scoped>
.verify-email-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 100px);
}
</style>
<template>
  <el-card class="verification-card">
    <template #header>
      <div class="card-header">
        <span>邮箱验证</span>
      </div>
    </template>
    <div v-if="loading" class="text-center">
      <el-icon class="is-loading"><Loading /></el-icon>
      <p>正在验证您的邮箱...</p>
    </div>
    <div v-else>
      <el-alert v-if="verificationSuccess" title="邮箱验证成功！" type="success" show-icon center closable />
      <el-alert v-else :title="verificationError" type="error" show-icon center closable />

      <div class="mt-4 text-center">
        <el-button type="primary" @click="goToLogin">前往登录</el-button>
        <el-button v-if="!verificationSuccess" @click="resendEmail" :loading="resending">重新发送验证邮件</el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElCard, ElAlert, ElButton, ElIcon, ElMessage } from 'element-plus';
import { Loading } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const loading = ref(true);
const verificationSuccess = ref(false);
const verificationError = ref('邮箱验证失败，请检查链接是否有效或已过期。');
const resending = ref(false);

const email = ref<string | null>(null); // To store email for resend functionality

onMounted(async () => {
  const token = route.query.token as string;
  if (!token) {
    verificationError.value = '缺少验证令牌。';
    loading.value = false;
    return;
  }

  try {
    const response = await authStore.verifyEmail(token);
    if (response.success) {
      verificationSuccess.value = true;
      ElMessage.success('邮箱验证成功！您现在可以登录。');
      // Optionally extract email from response if needed for future resend, or rely on user input
      email.value = response.email; // Assuming backend sends email in success response
    } else {
      verificationError.value = response.message || '邮箱验证失败。';
      ElMessage.error(verificationError.value);
    }
  } catch (error: any) {
    verificationError.value = error.response?.data?.message || '邮箱验证过程中发生错误。';
    ElMessage.error(verificationError.value);
    console.error('Email verification error:', error);
  } finally {
    loading.value = false;
  }
});

const goToLogin = () => {
  router.push('/login');
};

const resendEmail = async () => {
  if (resending.value) return;

  // If email is not available from previous verification, prompt user or assume it's from the original registration attempt
  let targetEmail = email.value;
  if (!targetEmail) {
    // A more robust solution would prompt the user for their email here
    ElMessage.warning('无法自动获取您的邮箱，请前往登录页手动输入邮箱。');
    return;
  }

  resending.value = true;
  try {
    const response = await authStore.resendVerificationEmail(targetEmail);
    ElMessage.success(response.message || '新的验证邮件已发送，请检查您的邮箱。');
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '重新发送邮件失败，请稍后再试。');
    console.error('Resend email error:', error);
  } finally {
    resending.value = false;
  }
};
</script>

<style scoped>
.verification-card {
  max-width: 500px;
  margin: 50px auto;
  padding: 20px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  text-align: center;
}

.card-header {
  font-size: 1.2em;
  font-weight: bold;
}

.text-center {
  text-align: center;
}

.mt-4 {
  margin-top: 20px;
}

.is-loading {
  font-size: 3em;
  color: var(--el-color-primary);
}
</style>
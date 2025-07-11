<template>
  <el-card class="login-card">
    <template #header>
      <div class="card-header">
        <span>用户登录</span>
      </div>
    </template>
    <el-form :model="form" :rules="rules" ref="loginFormRef" label-width="auto">
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="请输入邮箱"></el-input>
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input type="password" v-model="form.password" show-password placeholder="请输入密码"></el-input>
      </el-form-item>
      <el-form-item>
        <el-checkbox v-model="form.rememberMe">记住我</el-checkbox>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit" :loading="loading" class="full-width-button">登录</el-button>
      </el-form-item>
    </el-form>
    <div class="login-footer">
      还没有账号？<router-link to="/register">立即注册</router-link>
      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon class="mt-3" closable />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElForm, ElFormItem, ElInput, ElButton, ElCard, ElCheckbox, ElAlert, ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed

const authStore = useAuthStore();
const router = useRouter();

const loginFormRef = ref<FormInstance>();
const loading = ref(false);
const errorMessage = ref('');

const form = reactive({
  email: '',
  password: '',
  rememberMe: false, // For "Remember Me" functionality
});

const rules = reactive<FormRules>({
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
  ],
});

const onSubmit = async () => {
  if (!loginFormRef.value) return;

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      errorMessage.value = '';
      try {
        const response = await authStore.login({
          email: form.email,
          password: form.password,
        });
        ElMessage.success('登录成功！');
        // Redirect to homepage or dashboard
        router.push('/');
      } catch (error: any) {
        errorMessage.value = error.response?.data?.message || '登录失败，请检查邮箱和密码。';
        ElMessage.error(errorMessage.value);
        console.error('Login error:', error);
      } finally {
        loading.value = false;
      }
    } else {
      ElMessage.error('请检查表单输入。');
      return false;
    }
  });
};
</script>

<style scoped>
.login-card {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.card-header {
  font-size: 1.2em;
  font-weight: bold;
  text-align: center;
}

.full-width-button {
  width: 100%;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
}

.mt-3 {
  margin-top: 15px;
}
</style>
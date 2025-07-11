<template>
  <el-card class="register-card">
    <template #header>
      <div class="card-header">
        <span>用户注册</span>
      </div>
    </template>
    <el-form :model="form" :rules="rules" ref="registerFormRef" label-width="auto">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入用户名"></el-input>
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="请输入邮箱"></el-input>
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input type="password" v-model="form.password" show-password placeholder="请输入密码"></el-input>
      </el-form-item>
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input type="password" v-model="form.confirmPassword" show-password placeholder="请再次输入密码"></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit" :loading="loading" class="full-width-button">注册</el-button>
      </el-form-item>
    </el-form>
    <div class="register-footer">
      已有账号？<router-link to="/login">立即登录</router-link>
      <el-alert v-if="successMessage" :title="successMessage" type="success" show-icon class="mt-3" closable />
      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon class="mt-3" closable />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElForm, ElFormItem, ElInput, ElButton, ElCard, ElAlert, ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed

const authStore = useAuthStore();
const router = useRouter();

const registerFormRef = ref<FormInstance>();
const loading = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
});

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'));
  } else if (value !== form.password) {
    callback(new Error('两次输入的密码不一致!'));
  } else {
    callback();
  }
};

const rules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度在 6 到 30 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' },
  ],
});

const onSubmit = async () => {
  if (!registerFormRef.value) return;

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      errorMessage.value = '';
      successMessage.value = '';
      try {
        const response = await authStore.register({
          username: form.username,
          email: form.email,
          password: form.password,
        });
        successMessage.value = response.message || '注册成功！请检查您的邮箱以完成验证。';
        ElMessage.success(successMessage.value);
        // Optionally redirect to login or show verification message
        router.push('/login'); // Redirect to login after successful registration
      } catch (error: any) {
        errorMessage.value = error.response?.data?.message || '注册失败，请稍后再试。';
        ElMessage.error(errorMessage.value);
        console.error('Registration error:', error);
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
.register-card {
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

.register-footer {
  text-align: center;
  margin-top: 20px;
}

.mt-3 {
  margin-top: 15px;
}
</style>
<template>
  <!-- locale 从这里下发：按需引入后不再有全局 app.use(ElementPlus, { locale })，
       el-config-provider 由 ElementPlusResolver 自动解析引入 -->
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

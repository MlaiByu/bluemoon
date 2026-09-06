<template>
  <div class="bm-container nf">
    <div class="moon">🌙</div>
    <div class="code bm-gradient-text">404</div>
    <p class="tip">页面走丢了，或者它从未存在过。</p>
    <p class="sub">也许它正在月球背面度假 ☕</p>
    <div class="ops">
      <button class="bm-btn" @click="$router.push('/')">回到首页</button>
      <el-button @click="$router.back()">返回上一页</el-button>
    </div>
  </div>
</template>

<style scoped>
.nf {
  padding: 90px 20px 110px;
  text-align: center;
}

.moon {
  font-size: 64px;
  filter: drop-shadow(0 10px 20px rgba(102, 126, 234, 0.3));
  animation: float 3.5s ease-in-out infinite;
}

.code {
  font-size: 110px;
  font-weight: 900;
  line-height: 1;
  letter-spacing: 8px;
  margin: 10px 0 0;
}

.tip {
  margin: 18px 0 4px;
  font-size: 17px;
  font-weight: 600;
  color: var(--bm-text);
}

.sub {
  margin: 0 0 28px;
  font-size: 13.5px;
  color: var(--bm-text-sub);
}

.ops {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
</style>

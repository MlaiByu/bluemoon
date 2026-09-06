# 拉灯模式（纸灯笼）组件文档

## 概述

「拉灯」是固定在页面右侧、可拖拽的**纸灯笼**日夜模式切换控件。往下拉流苏穗子即触发「点灯 / 熄灯」（切换 `html.dark` 主题），松手有橡皮筋回弹；也支持点击、键盘 `Space` / `Enter` 切换。核心交互（切主题）与旧版一致，手感与视觉全面重做为「温暖、柔软、治愈」的纸灯笼意象。

## 文件结构

```
src/
  components/ThemeSwitch.vue      # 视图层：纸灯笼 UI + 拖拽物理 + 粒子
  composables/useTheme.js         # 主题状态：html.dark 读写 + 跨标签同步 + 音效
  composables/useLampMachine.js   # 状态机：idle/dragging/switching/locked
  styles/index.css                # 设计 token（朱砂红/暖橘/竹编/spring 曲线）
```

## 交互方式

| 方式 | 行为 |
|------|------|
| 拖拽流苏 | 下拉超过**灯身 1/3** 行程触发切换；不足则 spring 回弹（橡皮筋阻力：越深阻力越大） |
| 单击 | 等效一次完整拉灯 |
| 键盘 | `Space` / `Enter` |
| 跨标签页 | `storage` 事件即时同步 |

## 状态机

| 状态 | 说明 | 可交互 |
|------|------|--------|
| `idle` | 静止 | 是 |
| `dragging` | 拖拽中 | 本实例 |
| `switching` | 切换动画中（锁） | 否 |
| `locked` | 异步加载中（预留） | 否 |

- 阈值：`DRAG_THRESHOLD = 1/3`（灯身高度 1/3）。
- 快速连拉由状态机锁定，动画播完才响应下一次，不会乱跳。

## 视觉与文案

- **灯身**：朱砂红/暖橘渐变 + 宣纸高光 + CSS 竹编纹理 + 内部透光；顶部深色木纹横档带翘角，底部彩色流苏（金混樱花粉）末端坠琉璃珠。
- **文案**：`点灯 / 熄灯`（按钮 title）、`灯明 / 灯灭`（状态标签），配颜文字 `(｡･ω･｡)` / `(´-ω-｀)`。
- **发光**：灯亮时内部暖黄透光 + 地面一圈模糊圆形光斑（径向渐变 + box-shadow）；灯灭时灯身素净、似小月亮。
- **粒子**：日间飘落小花/蒲公英光点，夜间萤火虫光点；数量 ≤16，**全部 Canvas 绘制**（满足「>20 必须 Canvas」红线）。
- **动效**：灯亮瞬间 scale 1→1.08→1 呼吸膨胀；空闲 2s 一轮微弱脉动（活物感）；流苏松手弹簧回弹带惯性延迟。

## 无障碍

- `role="switch"` + `aria-checked` + `aria-label`。
- 键盘 `Space` / `Enter`；焦点态琉璃珠金色发光环。
- `prefers-reduced-motion: reduce`：弹簧降级为 0.2s 线性淡入淡出，隐藏粒子。

## 性能

- 拖拽 `pointermove` 约 16ms 节流；动画只改 `transform` / `opacity` / CSS 变量（合成层）。
- 粒子用 Canvas，且常驻数量 ≤16，不堆 DOM。
- 未引入 GSAP；回弹用 `ease-out-back`（`cubic-bezier` 近似弹簧）+ rAF 实现。

## 使用

```vue
<script setup>
import ThemeSwitch from '@/components/ThemeSwitch.vue'
</script>
<template><ThemeSwitch /></template>
```

已挂载于 `src/layouts/FrontLayout.vue`。

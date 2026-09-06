/**
 * 拉灯状态机（组合式函数）
 *
 * 四态：idle（静止）→ dragging（拖拽中）→ switching（切换动画中）→ 回到 idle
 *       switching 期间若需异步加载可进入 locked（锁定，忽略一切输入）。
 *
 * 职责：只管理「状态 + 拖拽距离 → 是否触发切换」的决策，不触碰 DOM 与动画，
 *       便于单元测试与视图层解耦。
 */
import { computed, reactive, readonly } from 'vue'

/** 拖拽行程阈值：拉下超过灯笼高度 1/3 即判定为一次完整拉灯（0~1） */
const DRAG_THRESHOLD = 1 / 3

/**
 * @param {{ onCommit: () => void }} hooks  触发切换时的回调（由视图层注入）
 */
export function useLampMachine({ onCommit } = {}) {
  const state = reactive({
    name: 'idle', // idle | dragging | switching | locked
    /** 拉绳被拖拽的距离（px，向下为正），由视图层在 move 时更新 */
    drag: 0,
    /** 拉绳最大行程（px），用于换算比例 */
    maxDrag: 120,
  })

  const isIdle = computed(() => state.name === 'idle')
  const isDragging = computed(() => state.name === 'dragging')
  const isBusy = computed(() => state.name === 'switching' || state.name === 'locked')

  /** 当前拖拽比例 0~1 */
  const ratio = computed(() =>
    state.maxDrag > 0 ? Math.min(1, Math.max(0, state.drag / state.maxDrag)) : 0
  )

  /** 是否已越过触发阈值 */
  const passedThreshold = computed(() => ratio.value >= DRAG_THRESHOLD)

  /**
   * 尝试进入拖拽态。
   * switching / locked 期间忽略（防连击导致状态错乱）。
   * @returns {boolean} 是否成功进入
   */
  function start() {
    if (isBusy.value) return false
    state.name = 'dragging'
    state.drag = 0
    return true
  }

  /** 更新拖拽距离（move 事件，调用方已做节流） */
  function move(delta) {
    if (state.name !== 'dragging') return
    state.drag = delta
  }

  /**
   * 松手：决定是否触发切换。
   * @returns {'commit' | 'cancel'} 触发切换 or 回弹取消
   */
  function end() {
    if (state.name !== 'dragging') return 'cancel'
    if (passedThreshold.value) {
      state.name = 'switching'
      state.drag = state.maxDrag // 吸附到满行程
      onCommit?.()
      return 'commit'
    }
    state.name = 'idle'
    state.drag = 0 // 回弹复位
    return 'cancel'
  }

  /** 切换完成（动画/异步结束后由视图层调用），回到 idle */
  function done() {
    if (state.name === 'switching' || state.name === 'locked') {
      state.name = 'idle'
      state.drag = 0
    }
  }

  /** 进入/退出锁定（异步加载期间阻塞交互） */
  function lock() {
    state.name = 'locked'
  }
  function unlock() {
    state.name = 'idle'
    state.drag = 0
  }

  /** 外部强制复位（如拖拽被中断） */
  function reset() {
    state.name = 'idle'
    state.drag = 0
  }

  return {
    state: readonly(state),
    isIdle,
    isDragging,
    isBusy,
    ratio,
    passedThreshold,
    start,
    move,
    end,
    done,
    lock,
    unlock,
    reset,
    DRAG_THRESHOLD,
  }
}

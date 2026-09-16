/**
 * 全局图标注册表（按需）。
 *
 * 为什么不写 `import * as Icons from '@element-plus/icons-vue'`：
 * 命名空间导入会让打包器无法做静态分析，整个图标包（2000+ 个）会被整体拉进产物。
 * 必须逐个具名导入，tree-shaking 才能只保留下面这 26 个。
 *
 * 新增图标时：在本文件补一行，模板里即可直接写 <el-icon><Xxx /></el-icon>。
 * 若组件内已显式 import 该图标（如 AdminLayout / PostEdit / ImagesAdmin），
 * 则无需在此重复登记 —— 两处都有也不会重复打包，同一模块会被复用。
 */
import {
  ArrowDown,
  Calendar,
  Camera,
  ChatDotRound,
  CopyDocument,
  DataLine,
  Delete,
  Document,
  Edit,
  EditPen,
  Folder,
  HomeFilled,
  Link,
  Loading,
  Location,
  Message,
  Picture,
  Plus,
  Refresh,
  Search,
  Star,
  TrendCharts,
  UploadFilled,
  User,
  View,
  Warning,
} from '@element-plus/icons-vue'

const ICONS = {
  ArrowDown,
  Calendar,
  Camera,
  ChatDotRound,
  CopyDocument,
  DataLine,
  Delete,
  Document,
  Edit,
  EditPen,
  Folder,
  HomeFilled,
  Link,
  Loading,
  Location,
  Message,
  Picture,
  Plus,
  Refresh,
  Search,
  Star,
  TrendCharts,
  UploadFilled,
  User,
  View,
  Warning,
}

export function registerGlobalIcons(app) {
  for (const [name, component] of Object.entries(ICONS)) {
    app.component(name, component)
  }
}

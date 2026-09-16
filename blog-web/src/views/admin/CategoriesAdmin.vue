<template>
  <div class="categories-admin bm-fade-up">
    <div class="bm-card panel">
      <div class="head">
        <h3 class="block-title"><i class="dot"></i>分类管理</h3>
        <div class="head-actions">
          <span class="count-chip">共 {{ categories.length }} 个分类</span>
          <el-button type="primary" :icon="Plus" @click="openDialog()">新建分类</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="categories" stripe class="cat-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="slug" label="别名" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '—' }}</template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="post_count" label="文章数" width="90" align="right" />
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialog" :title="editing ? '编辑分类' : '新建分类'" width="440px">
      <el-form :model="form" label-width="70px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="分类名称" maxlength="50" />
        </el-form-item>
        <el-form-item label="别名">
          <el-input v-model="form.slug" placeholder="英文别名，留空自动生成" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
          <span class="hint">数值越大越靠前</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index'
import { ElMessageBox } from 'element-plus/es/components/message-box/index'
import { Plus } from '@element-plus/icons-vue'
import { createCategory, deleteCategory, getCategories, updateCategory } from '@/api'

const categories = ref([])
const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const editing = ref(null)

const form = reactive({ name: '', slug: '', description: '', sort_order: 0 })

async function fetchList() {
  loading.value = true
  try {
    categories.value = (await getCategories()) || []
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  editing.value = row || null
  Object.assign(form, {
    name: row?.name || '',
    slug: row?.slug || '',
    description: row?.description || '',
    sort_order: row?.sort_order ?? 0,
  })
  dialog.value = true
}

async function submit() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写分类名称')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateCategory(editing.value.id, { ...form })
      ElMessage.success('已更新')
    } else {
      await createCategory({ ...form })
      ElMessage.success('已创建')
    }
    dialog.value = false
    fetchList()
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除分类「${row.name}」？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  try {
    await deleteCategory(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(fetchList)
</script>

<style scoped>
.categories-admin {
  position: relative;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.block-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.block-title .dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  background: var(--bm-gradient);
  transform: rotate(45deg);
  box-shadow: 0 3px 8px var(--bm-shadow-color);
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.count-chip {
  padding: 5px 14px;
  background: var(--bm-primary-soft);
  color: var(--bm-primary-2);
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
}

.cat-table {
  border-radius: var(--bm-radius-sm);
  overflow: hidden;
}

.hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--bm-text-mute);
}
</style>

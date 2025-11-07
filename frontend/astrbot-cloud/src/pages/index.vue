<script setup>
import axios from 'axios';
import { pinyin } from 'pinyin-pro';
import { ref, computed, onMounted, watch } from 'vue';
import { useTheme } from 'vuetify';

// 主题
const theme = useTheme();
const isDark = computed(() => theme.global.current.value.dark);

// 插件市场数据
const pluginMarketData = ref([]);
const marketSearch = ref("");
const debouncedMarketSearch = ref("");
const refreshingMarket = ref(false);
const sortBy = ref('default'); // default, stars, author, updated
const sortOrder = ref('desc'); // desc (降序) or asc (升序)
const showPluginFullName = ref(false);
const loading = ref(false);

// 分页相关
const currentPage = ref(1);
const displayItemsPerPage = 9; // 每页显示9个卡片

// Toast 提示
const snack_message = ref("");
const snack_show = ref(false);
const snack_success = ref("success");

// 发布插件对话框
const publishDialog = ref(false);
const pluginForm = ref({
  name: '',
  display_name: '',
  desc: '',
  author: '',
  repo: '',
  tags: [],
  social_link: ''
});
const tagInput = ref('');
const formValid = ref(false);

// 表单验证规则
const rules = {
  required: (v) => !!v || '此项为必填项',
  nameFormat: (v) => {
    if (!v) return '此项为必填项';
    if (!v.startsWith('astrbot_plugin_')) {
      return '插件名必须以 astrbot_plugin_ 开头';
    }
    return true;
  },
  urlFormat: (v) => {
    if (!v) return '此项为必填项';
    try {
      new URL(v);
      return true;
    } catch {
      return '请输入有效的 URL';
    }
  }
};

// Toast 提示函数
const toast = (message, success) => {
  snack_message.value = message;
  snack_show.value = true;
  snack_success.value = success;
};

// 拼音搜索相关函数
const normalizeStr = (s) => (s ?? '').toString().toLowerCase().trim();
const toPinyinText = (s) => pinyin(s ?? '', { toneType: 'none' }).toLowerCase().replace(/\s+/g, '');
const toInitials = (s) => pinyin(s ?? '', { pattern: 'first', toneType: 'none' }).toLowerCase().replace(/\s+/g, '');

const marketCustomFilter = (value, query, item) => {
  const q = normalizeStr(query);
  if (!q) return true;

  const candidates = new Set();
  if (value != null) candidates.add(String(value));
  if (item?.name) candidates.add(String(item.name));
  if (item?.trimmedName) candidates.add(String(item.trimmedName));
  if (item?.desc) candidates.add(String(item.desc));
  if (item?.author) candidates.add(String(item.author));

  for (const v of candidates) {
    const nv = normalizeStr(v);
    if (nv.includes(q)) return true;
    const pv = toPinyinText(v);
    if (pv.includes(q)) return true;
    const iv = toInitials(v);
    if (iv.includes(q)) return true;
  }
  return false;
};

// 过滤后的插件市场数据（带搜索）
const filteredMarketPlugins = computed(() => {
  if (!Array.isArray(pluginMarketData.value)) {
    return [];
  }
  
  if (!debouncedMarketSearch.value) {
    return pluginMarketData.value;
  }

  const search = debouncedMarketSearch.value.toLowerCase();
  return pluginMarketData.value.filter(plugin => {
    return marketCustomFilter(plugin.name, search, plugin) ||
      marketCustomFilter(plugin.desc, search, plugin) ||
      marketCustomFilter(plugin.author, search, plugin);
  });
});

// 排序后的插件列表
const sortedPlugins = computed(() => {
  const filtered = filteredMarketPlugins.value || [];
  if (!Array.isArray(filtered)) return [];
  
  let plugins = [...filtered];

  if (sortBy.value === 'stars') {
    plugins.sort((a, b) => {
      const starsA = a.stars ?? 0;
      const starsB = b.stars ?? 0;
      return sortOrder.value === 'desc' ? starsB - starsA : starsA - starsB;
    });
  } else if (sortBy.value === 'author') {
    plugins.sort((a, b) => {
      const authorA = (a.author ?? '').toLowerCase();
      const authorB = (b.author ?? '').toLowerCase();
      const result = authorA.localeCompare(authorB);
      return sortOrder.value === 'desc' ? -result : result;
    });
  } else if (sortBy.value === 'updated') {
    plugins.sort((a, b) => {
      const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
      const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
      return sortOrder.value === 'desc' ? dateB - dateA : dateA - dateB;
    });
  } else {
    // default: 推荐插件排在前面
    const pinned = plugins.filter(plugin => plugin?.pinned);
    const notPinned = plugins.filter(plugin => !plugin?.pinned);
    return [...pinned, ...notPinned];
  }

  return plugins;
});

// 分页计算
const totalPages = computed(() => {
  return Math.ceil(sortedPlugins.value.length / displayItemsPerPage);
});

const paginatedPlugins = computed(() => {
  const start = (currentPage.value - 1) * displayItemsPerPage;
  const end = start + displayItemsPerPage;
  return sortedPlugins.value.slice(start, end);
});

// 处理插件名称
const trimExtensionName = () => {
  pluginMarketData.value.forEach(plugin => {
    if (plugin.name) {
      let name = plugin.name.trim().toLowerCase();
      if (name.startsWith("astrbot_plugin_")) {
        plugin.trimmedName = name.substring(15);
      } else if (name.startsWith("astrbot_") || name.startsWith("astrbot-")) {
        plugin.trimmedName = name.substring(8);
      } else {
        plugin.trimmedName = plugin.name;
      }
    }
  });
};

// 获取插件市场数据
const getPluginMarketData = async (forceRefresh = false) => {
  loading.value = true;
  try {
    const response = await axios.get('https://api.soulter.top/astrbot/plugins');
    const data = response.data || {};
    
    // 将对象转换为数组，每个插件添加 name 属性
    const pluginsArray = Object.keys(data).map(key => ({
      name: key,
      ...data[key]
    }));
    
    pluginMarketData.value = pluginsArray;
    trimExtensionName();
    currentPage.value = 1;
    
    if (forceRefresh) {
      toast('刷新成功', 'success');
    }
  } catch (error) {
    console.error('获取插件市场数据失败:', error);
    toast('获取插件市场数据失败: ' + error.message, 'error');
    // 错误时也确保是空数组
    pluginMarketData.value = [];
  } finally {
    loading.value = false;
  }
};

// 刷新插件市场
const refreshPluginMarket = async () => {
  refreshingMarket.value = true;
  try {
    await getPluginMarketData(true);
  } finally {
    refreshingMarket.value = false;
  }
};

// 添加标签
const addTag = () => {
  if (tagInput.value && !pluginForm.value.tags.includes(tagInput.value.trim())) {
    pluginForm.value.tags.push(tagInput.value.trim());
    tagInput.value = '';
  }
};

// 删除标签
const removeTag = (tag) => {
  const index = pluginForm.value.tags.indexOf(tag);
  if (index > -1) {
    pluginForm.value.tags.splice(index, 1);
  }
};

// 重置表单
const resetForm = () => {
  pluginForm.value = {
    name: '',
    display_name: '',
    desc: '',
    author: '',
    repo: '',
    tags: [],
    social_link: ''
  };
  tagInput.value = '';
};

// 提交到 GitHub Issue
const submitToGitHub = () => {
  // 构建 JSON
  const pluginJson = {
    name: pluginForm.value.name,
    display_name: pluginForm.value.display_name,
    desc: pluginForm.value.desc,
    author: pluginForm.value.author,
    repo: pluginForm.value.repo,
  };
  
  // 只添加非空的可选字段
  if (pluginForm.value.tags.length > 0) {
    pluginJson.tags = pluginForm.value.tags;
  }
  if (pluginForm.value.social_link) {
    pluginJson.social_link = pluginForm.value.social_link;
  }

  // 格式化 JSON（带缩进）
  const jsonString = JSON.stringify(pluginJson, null, 2);
  
  // 构建 Issue body
  const issueBody = `\`\`\`json\n${jsonString}\n\`\`\``;
  
  // 构建 GitHub Issue URL
  const baseUrl = 'https://github.com/AstrBotDevs/AstrBot/issues/new';
  const params = new URLSearchParams({
    template: 'PLUGIN_PUBLISH.yml',
    title: `[Plugin] ${pluginForm.value.name}`,
    'plugin-info': issueBody
  });
  
  const issueUrl = `${baseUrl}?${params.toString()}`;
  
  // 打开新窗口
  window.open(issueUrl, '_blank');
  
  // 关闭对话框并重置表单
  publishDialog.value = false;
  resetForm();
  
  toast('正在跳转到 GitHub Issue 页面...', 'success');
};

// 搜索防抖处理
let searchDebounceTimer = null;
watch(marketSearch, (newVal) => {
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer);
  }

  searchDebounceTimer = setTimeout(() => {
    debouncedMarketSearch.value = newVal;
    currentPage.value = 1;
  }, 300);
});

// 切换主题
const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'light' : 'dark';
};

// 页面加载时获取数据
onMounted(() => {
  getPluginMarketData();
});
</script>

<template>
  <v-container fluid :class="['page-container', { 'dark-mode': isDark }]">
    <!-- 导航栏 -->
    <nav class="top-nav">
      <div class="nav-container">
        <!-- Logo -->
        <a href="https://astrbot.app" target="_blank" class="nav-logo">
          <img 
            src="@/assets/logo-combine.svg" 
            alt="AstrBot Logo" 
            class="page-logo"
          />
        </a>
        
        <!-- 导航项 -->
        <div class="nav-items">
          <v-btn
            icon
            variant="text"
            @click="toggleTheme"
            size="small"
          >
            <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
            <v-tooltip activator="parent" location="bottom">
              {{ isDark ? '切换到浅色模式' : '切换到深色模式' }}
            </v-tooltip>
          </v-btn>
          <a href="https://astrbot.app" target="_blank" class="nav-item">
            <v-icon size="small" class="mr-1">mdi-home</v-icon>
            <span class="d-none d-sm-inline">主页</span>
          </a>
          <a href="https://github.com/AstrBotDevs/AstrBot" target="_blank" class="nav-item">
            <v-icon size="small" class="mr-1">mdi-github</v-icon>
            <span class="d-none d-sm-inline">GitHub</span>
          </a>
          <a href="https://docs.astrbot.app" target="_blank" class="nav-item">
            <v-icon size="small" class="mr-1">mdi-book-open-variant</v-icon>
            <span class="d-none d-sm-inline">文档</span>
          </a>
          <a href="https://blog.astrbot.app" target="_blank" class="nav-item">
            <v-icon size="small" class="mr-1">mdi-post</v-icon>
            <span class="d-none d-sm-inline">博客</span>
          </a>
        </div>
      </div>
    </nav>

    <v-row>
      <v-col cols="12">
        <v-card variant="flat" color="transparent">
          <v-card-text style="padding: 0px 12px;">
            <!-- 标题和搜索栏 -->
            <div class="mb-4 d-flex flex-column align-center">
              <h1 class="page-title text-h4 mb-4 text-center">AstrBot 插件市场</h1>
              <div style="width: 100%; max-width: 500px; padding: 0 12px;">
                <v-text-field
                  v-model="marketSearch"
                  density="compact"
                  label="搜索插件..."
                  prepend-inner-icon="mdi-magnify"
                  variant="solo-filled"
                  flat
                  hide-details
                  single-line
                ></v-text-field>
              </div>
            </div>

            <!-- 插件市场内容 -->
            <div class="mt-4">
              <div class="section-header d-flex align-center mb-2" style="justify-content: space-between; flex-wrap: wrap; gap: 8px; padding: 0 4px;">
                <div class="d-flex align-center" style="gap: 6px;">
                  <h2 class="section-title">所有插件({{ filteredMarketPlugins.length }})</h2>
                  <v-btn icon variant="text" @click="refreshPluginMarket" :loading="refreshingMarket" size="small">
                    <v-icon size="small">mdi-refresh</v-icon>
                  </v-btn>
                </div>

                <div class="d-flex align-center flex-wrap" style="gap: 8px;">
                  <!-- 移动端隐藏分页，使用底部分页 -->
                  <v-pagination
                    v-model="currentPage"
                    :length="totalPages"
                    :total-visible="5"
                    size="small"
                    density="comfortable"
                    class="d-none d-sm-flex"
                  ></v-pagination>

                  <!-- 排序选择器 -->
                  <v-select
                    v-model="sortBy"
                    :items="[
                      { title: '默认排序', value: 'default' },
                      { title: '按 Star 数', value: 'stars' },
                      { title: '按作者', value: 'author' },
                      { title: '按更新时间', value: 'updated' }
                    ]"
                    density="compact"
                    variant="outlined"
                    hide-details
                    style="max-width: 150px;"
                  >
                    <template v-slot:prepend-inner>
                      <v-icon size="small">mdi-sort</v-icon>
                    </template>
                  </v-select>

                  <!-- 排序方向切换按钮 -->
                  <v-btn
                    icon
                    v-if="sortBy !== 'default'"
                    @click="sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'"
                    variant="text"
                    density="compact"
                  >
                    <v-icon>{{ sortOrder === 'desc' ? 'mdi-sort-descending' : 'mdi-sort-ascending' }}</v-icon>
                    <v-tooltip activator="parent" location="top">
                      {{ sortOrder === 'desc' ? '降序' : '升序' }}
                    </v-tooltip>
                  </v-btn>
                </div>
              </div>

              <!-- 插件卡片列表 -->
              <v-row style="min-height: 26rem;">
                <v-col v-if="loading" cols="12" class="d-flex justify-center align-center">
                  <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
                </v-col>

                <v-col v-else-if="paginatedPlugins.length === 0" cols="12" class="text-center pa-8">
                  <v-icon size="64" color="info" class="mb-4">mdi-puzzle-outline</v-icon>
                  <div class="text-h5 mb-2">暂无插件</div>
                  <div class="text-body-1 mb-4">没有找到符合条件的插件</div>
                </v-col>

                <v-col v-else v-for="plugin in paginatedPlugins" :key="plugin.name" cols="12" md="6" lg="4">
                  <v-card 
                    class="plugin-card rounded-lg d-flex flex-column" 
                    elevation="0" 
                    style="height: 12rem; position: relative;"
                  >
                    <!-- 推荐标记 -->
                    <v-chip
                      v-if="plugin?.pinned"
                      color="warning"
                      size="x-small"
                      label
                      class="pinned-chip"
                      style="position: absolute; right: 8px; top: 8px; z-index: 10; height: 20px; font-weight: bold;"
                    >
                      🥳 推荐
                    </v-chip>

                    <v-card-text style="padding: 12px; padding-bottom: 8px; display: flex; gap: 12px; width: 100%; flex: 1; overflow: hidden;">
                      <div v-if="plugin?.logo" style="flex-shrink: 0; height: 75px; width: 75px;">
                        <img
                          :src="plugin.logo"
                          :alt="plugin.name"
                          class="plugin-logo"
                          style="height: 75px; width: 75px; border-radius: 8px; object-fit: cover; opacity: 0; transition: opacity 0.5s ease-in-out;"
                          @load="(e) => e.target.style.opacity = 1"
                        />
                      </div>

                      <div style="flex: 1; overflow: hidden; display: flex; flex-direction: column;">
                        <!-- Display Name -->
                        <div
                          class="font-weight-bold"
                          style="margin-bottom: 4px; line-height: 1.3; font-size: 1.2rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
                        >
                          <span style="overflow: hidden; text-overflow: ellipsis;">
                            {{ plugin.display_name?.length ? plugin.display_name : (showPluginFullName ? plugin.name : plugin.trimmedName) }}
                          </span>
                        </div>

                        <!-- Author with link -->
                        <div class="d-flex align-center" style="gap: 4px; margin-bottom: 6px;">
                          <v-icon icon="mdi-account" size="x-small" style="color: rgba(var(--v-theme-on-surface), 0.5);"></v-icon>
                          <a
                            v-if="plugin?.social_link"
                            :href="plugin.social_link"
                            target="_blank"
                            class="text-subtitle-2 font-weight-medium"
                            style="text-decoration: none; color: rgb(var(--v-theme-primary)); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
                          >
                            {{ plugin.author }}
                          </a>
                          <span
                            v-else
                            class="text-subtitle-2 font-weight-medium"
                            style="color: rgb(var(--v-theme-primary)); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
                          >
                            {{ plugin.author }}
                          </span>
                          <div class="d-flex align-center text-subtitle-2 ml-2" style="color: rgba(var(--v-theme-on-surface), 0.7);">
                            <v-icon icon="mdi-source-branch" size="x-small" style="margin-right: 2px;"></v-icon>
                            <span>{{ plugin.version }}</span>
                          </div>
                        </div>

                        <!-- Description -->
                        <div
                          class="text-caption"
                          style="overflow: scroll; color: rgba(var(--v-theme-on-surface), 0.6); line-height: 1.3; margin-bottom: 6px; flex: 1;"
                        >
                          {{ plugin.desc }}
                        </div>

                        <!-- Stats: Stars & Updated -->
                        <div class="d-flex align-center" style="gap: 8px; margin-top: auto;">
                          <div v-if="plugin.stars !== undefined" class="d-flex align-center text-subtitle-2" style="color: rgba(var(--v-theme-on-surface), 0.7);">
                            <v-icon icon="mdi-star" size="x-small" style="margin-right: 2px;"></v-icon>
                            <span>{{ plugin.stars }}</span>
                          </div>
                          <div v-if="plugin.updated_at" class="d-flex align-center text-subtitle-2" style="color: rgba(var(--v-theme-on-surface), 0.7);">
                            <v-icon icon="mdi-clock-outline" size="x-small" style="margin-right: 2px;"></v-icon>
                            <span>{{ new Date(plugin.updated_at).toLocaleString() }}</span>
                          </div>
                        </div>
                      </div>
                    </v-card-text>

                    <!-- Actions -->
                    <v-card-actions style="gap: 6px; padding: 8px 12px; padding-top: 0;">
                      <v-chip
                        v-for="tag in plugin.tags?.slice(0, 2)"
                        :key="tag"
                        :color="tag === 'danger' ? 'error' : 'primary'"
                        label
                        size="x-small"
                        style="height: 20px;"
                      >
                        {{ tag === 'danger' ? '危险' : tag }}
                      </v-chip>
                      <v-menu v-if="plugin.tags && plugin.tags.length > 2" open-on-hover offset-y>
                        <template v-slot:activator="{ props: menuProps }">
                          <v-chip v-bind="menuProps" color="grey" label size="x-small" style="height: 20px; cursor: pointer;">
                            +{{ plugin.tags.length - 2 }}
                          </v-chip>
                        </template>
                        <v-list density="compact">
                          <v-list-item v-for="tag in plugin.tags.slice(2)" :key="tag">
                            <v-chip :color="tag === 'danger' ? 'error' : 'primary'" label size="small">
                              {{ tag === 'danger' ? '危险' : tag }}
                            </v-chip>
                          </v-list-item>
                        </v-list>
                      </v-menu>
                      <v-spacer></v-spacer>
                      <v-btn
                        v-if="plugin?.repo"
                        color="secondary"
                        size="x-small"
                        variant="tonal"
                        :href="plugin.repo"
                        target="_blank"
                        style="height: 24px;"
                      >
                        <v-icon icon="mdi-github" start size="x-small"></v-icon>
                        仓库
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </v-col>
              </v-row>

              <!-- 底部分页控件 -->
              <div class="d-flex justify-center mt-4" v-if="totalPages > 1">
                <v-pagination v-model="currentPage" :length="totalPages" :total-visible="7" size="small"></v-pagination>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 浮动操作按钮 -->
    <v-btn
      icon
      size="large"
      color="primary"
      elevation="8"
      class="floating-action-button"
      @click="publishDialog = true"
    >
      <v-icon size="large">mdi-plus</v-icon>
      <v-tooltip activator="parent" location="left">
        发布插件到市场
      </v-tooltip>
    </v-btn>

    <!-- 发布插件对话框 -->
    <v-dialog 
      v-model="publishDialog" 
      :max-width="$vuetify.display.smAndDown ? '100%' : '500'" 
      :fullscreen="$vuetify.display.xs"
      persistent 
      scrollable
    >
      <v-card class="publish-dialog-card">
        <v-card-title class="dialog-title text-h5 d-flex align-center pa-4 pa-sm-6">
          <div>
            <div class="text-h6 text-sm-h5 font-weight-bold">发布插件到 AstrBot 插件市场</div>
            <div class="text-caption mt-1" style="opacity: 0.9;">填写插件信息,自动提交到 GitHub</div>
          </div>
        </v-card-title>
        
        <v-card-text class="pt-6 pb-4" style="max-height: 600px; overflow-y: auto;">
          <v-form v-model="formValid">
            <!-- 基本信息卡片 -->
            <v-card class="form-section mb-4" elevation="0">
              <v-card-title class="form-section-title text-subtitle-1 py-3">
                <v-icon size="small" class="mr-2">mdi-information</v-icon>
                基本信息
              </v-card-title>
              <v-card-text class="pa-4">
                <v-text-field
                  v-model="pluginForm.name"
                  label="插件名"
                  hint="必须以 astrbot_plugin_ 开头"
                  persistent-hint
                  :rules="[rules.nameFormat]"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-package-variant"
                  class="mb-4"
                ></v-text-field>

                <v-text-field
                  v-model="pluginForm.display_name"
                  label="展示名称"
                  hint="用于展示的插件名，方便人类阅读"
                  persistent-hint
                  :rules="[rules.required]"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-tag"
                  class="mb-4"
                ></v-text-field>

                <v-textarea
                  v-model="pluginForm.desc"
                  label="插件描述"
                  hint="简短介绍你的插件功能"
                  persistent-hint
                  :rules="[rules.required]"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-text"
                  rows="3"
                  auto-grow
                ></v-textarea>
              </v-card-text>
            </v-card>

            <!-- 作者信息卡片 -->
            <v-card class="form-section mb-4" elevation="0">
              <v-card-title class="form-section-title text-subtitle-1 py-3">
                <v-icon size="small" class="mr-2">mdi-account</v-icon>
                作者信息
              </v-card-title>
              <v-card-text class="pa-4">
                <v-text-field
                  v-model="pluginForm.author"
                  label="作者名"
                  :rules="[rules.required]"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-account-circle"
                  class="mb-4"
                ></v-text-field>

                <v-text-field
                  v-model="pluginForm.social_link"
                  label="社交链接（可选）"
                  hint="你的个人网站、GitHub 主页等"
                  persistent-hint
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-link-variant"
                ></v-text-field>
              </v-card-text>
            </v-card>

            <!-- 仓库信息卡片 -->
            <v-card class="form-section mb-4" elevation="0">
              <v-card-title class="form-section-title text-subtitle-1 py-3">
                <v-icon size="small" class="mr-2">mdi-github</v-icon>
                仓库信息
              </v-card-title>
              <v-card-text class="pa-4">
                <v-text-field
                  v-model="pluginForm.repo"
                  label="插件仓库链接"
                  hint="GitHub 仓库地址"
                  persistent-hint
                  :rules="[rules.urlFormat]"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-source-repository"
                  placeholder="https://github.com/username/repo"
                ></v-text-field>
              </v-card-text>
            </v-card>

            <!-- 标签卡片 -->
            <v-card class="form-section mb-4" elevation="0">
              <v-card-title class="form-section-title text-subtitle-1 py-3">
                <v-icon size="small" class="mr-2">mdi-tag-multiple</v-icon>
                插件标签（可选）
              </v-card-title>
              <v-card-text class="pa-4">
                <div class="d-flex align-center mb-3">
                  <v-text-field
                    v-model="tagInput"
                    label="添加标签"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    @keyup.enter="addTag"
                    class="mr-2"
                    prepend-inner-icon="mdi-label"
                  ></v-text-field>
                  <v-btn 
                    color="primary" 
                    @click="addTag" 
                    icon 
                    size="large"
                    elevation="0"
                  >
                    <v-icon>mdi-plus</v-icon>
                  </v-btn>
                </div>
                <div v-if="pluginForm.tags.length > 0" class="d-flex flex-wrap gap-2">
                  <v-chip
                    v-for="tag in pluginForm.tags"
                    :key="tag"
                    closable
                    @click:close="removeTag(tag)"
                    color="primary"
                    variant="flat"
                    size="default"
                  >
                    <v-icon start size="small">mdi-tag</v-icon>
                    {{ tag }}
                  </v-chip>
                </div>
                <div v-else class="text-caption text-grey text-center py-4">
                  暂无标签，点击上方添加
                </div>
              </v-card-text>
            </v-card>

            <!-- 提示信息 -->
            <v-alert 
              type="info" 
              variant="tonal" 
              class="mb-0"
              border="start"
              border-color="info"
            >
              <template v-slot:prepend>
                <v-icon size="large">mdi-information</v-icon>
              </template>
              <div class="text-body-2">
                <div class="font-weight-bold mb-2">提交前请注意：</div>
                <ul style="padding-left: 20px;">
                  <li>插件名必须以 <code style="background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 4px;">astrbot_plugin_</code> 开头</li>
                  <li>提交后将自动跳转到 GitHub Issue 页面完成发布</li>
                  <li>请确保所有必填信息填写完整且准确</li>
                  <li>仓库链接需要是有效的 GitHub URL</li>
                </ul>
              </div>
            </v-alert>
          </v-form>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions class="dialog-actions pa-4">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey" 
            variant="text" 
            @click="publishDialog = false; resetForm();"
          >
            <v-icon start>mdi-close</v-icon>
            取消
          </v-btn>
          <v-btn 
            variant="tonal" 
            @click="submitToGitHub"
            :disabled="!formValid"
            elevation="0"
          >
            <v-icon start>mdi-github</v-icon>
            提交到 GitHub
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Toast 提示 -->
    <v-snackbar :timeout="2000" elevation="24" :color="snack_success" v-model="snack_show">
      {{ snack_message }}
    </v-snackbar>
  </v-container>
</template>

<style scoped>
/* 页面容器 */
.page-container {
  background-color: #f9fafc;
  transition: background-color 0.3s ease;
}

.page-container.dark-mode {
  background-color: #121212;
}

/* 导航栏样式 */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  animation: fadeInUp 0.3s ease-in-out;
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.dark-mode .top-nav {
  background: rgba(18, 18, 18, 0.95);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.nav-container {
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
}

.nav-logo {
  display: flex;
  align-items: center;
  text-decoration: none;
  transition: transform 0.2s ease-in-out;
}

.nav-logo:hover {
  transform: scale(1.05);
}

.page-logo {
  height: 30px;
  width: auto;
}

.nav-items {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: rgba(0, 0, 0, 0.7);
  font-weight: 500;
  transition: all 0.2s ease-in-out;
  white-space: nowrap;
}

.dark-mode .nav-item {
  color: rgba(255, 255, 255, 0.7);
}

.nav-item:hover {
  background: rgba(0, 0, 0, 0.05);
  color: rgb(var(--v-theme-primary));
}

.dark-mode .nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* 页面标题 */
.page-title {
  font-weight: 1000;
  padding-top: 80px;
  transition: color 0.3s ease;
}

/* 区块标题 */
.section-header {
  transition: color 0.3s ease;
}

.section-title {
  transition: color 0.3s ease;
}

/* 移动端导航适配 */
@media (max-width: 600px) {
  .nav-container {
    padding: 10px 12px;
  }
  
  .page-logo {
    height: 24px;
  }
  
  .nav-items {
    gap: 4px;
  }
  
  .nav-item {
    padding: 6px 10px;
    font-size: 0.875rem;
  }
}

@media (max-width: 480px) {
  .nav-items {
    gap: 2px;
  }
  
  .nav-item {
    padding: 6px 8px;
  }
}

/* 发布插件对话框样式 */
.publish-dialog-card {
  overflow: hidden;
}

.dialog-title {
  transition: background-color 0.3s ease, color 0.3s ease;
}

.dialog-actions {
  background-color: rgba(0, 0, 0, 0.02);
  transition: background-color 0.3s ease;
}

.dark-mode .dialog-actions {
  background-color: rgba(255, 255, 255, 0.05);
}

.form-section {
  border: 1px solid rgba(0, 0, 0, 0.1);
  transition: border-color 0.3s ease, background-color 0.3s ease;
}

.dark-mode .form-section {
  border-color: rgba(255, 255, 255, 0.12);
}

.form-section-title {
  background-color: rgba(0, 0, 0, 0.03);
  transition: background-color 0.3s ease;
}

.dark-mode .form-section-title {
  background-color: rgba(255, 255, 255, 0.05);
}

.publish-dialog-card :deep(.v-card-text) {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

.publish-dialog-card :deep(.v-card-text::-webkit-scrollbar) {
  width: 8px;
}

.publish-dialog-card :deep(.v-card-text::-webkit-scrollbar-track) {
  background: transparent;
}

.publish-dialog-card :deep(.v-card-text::-webkit-scrollbar-thumb) {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.publish-dialog-card :deep(.v-card-text::-webkit-scrollbar-thumb:hover) {
  background-color: rgba(0, 0, 0, 0.3);
}

/* 浮动操作按钮 */
.floating-action-button {
  position: fixed;
  bottom: 32px;
  right: 32px;
  z-index: 1000;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.floating-action-button:hover {
  transform: scale(1.1) rotate(90deg);
}

/* 移动端浮动按钮适配 */
@media (max-width: 600px) {
  .floating-action-button {
    bottom: 20px;
    right: 20px;
  }
}

/* 插件卡片悬停效果 */
.plugin-card {
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background-color: #ffffff;
}

.dark-mode .plugin-card {
  background-color: #1e1e1e;
}

.plugin-card:hover {
  border-color: rgb(var(--v-theme-secondary));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dark-mode .plugin-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* 推荐标签动画 */
.pinned-chip {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.01);
  }
}

/* Logo 加载占位符 */
.plugin-logo {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -100% 0;
  }
  100% {
    background-position: 100% 0;
  }
}

/* 按钮悬停效果 */
.v-btn {
  transition: all 0.2s ease-in-out;
}

.v-btn:hover {
  transform: scale(1.01);
}

/* 搜索框聚焦动画 */
.v-text-field {
  transition: all 0.3s ease-in-out;
}

/* 页面进入动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(0);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.v-card {
  animation: fadeInUp 0.4s ease-out;
}

/* 移动端适配 */
@media (max-width: 960px) {
  /* 标题适配 */
  .page-title.text-h4 {
    font-size: 1.75rem !important;
    padding-top: 80px !important;
  }
  
  .section-title {
    font-size: 1.25rem !important;
  }
}

@media (max-width: 600px) {
  /* 标题适配 */
  .page-title.text-h4 {
    font-size: 1.5rem !important;
    padding-top: 70px !important;
  }
  
  .section-title {
    font-size: 1.1rem !important;
  }
  
  /* 插件卡片适配 */
  .plugin-card {
    height: auto !important;
    min-height: 10rem;
  }
  
  /* 隐藏移动端不必要的元素 */
  .plugin-card .text-caption {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  /* 对话框适配 */
  .publish-dialog-card {
    margin: 0;
    max-height: 100vh !important;
    border-radius: 0 !important;
  }
  
  .publish-dialog-card .v-card-text {
    max-height: calc(100vh - 200px) !important;
  }
}

/* 平板适配 */
@media (min-width: 601px) and (max-width: 960px) {
  .plugin-card {
    height: 11rem !important;
  }
}
</style>

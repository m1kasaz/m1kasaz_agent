const modeConfigs = {
  chat: {
    label: 'Chat',
    description: '通用对话模式，适合直接提问。',
    subtitle: 'm1kasaz agent 已就绪，开始你的第一个问题。',
    emptyTitle: '今天想聊点什么？',
    emptyHint: '你可以直接提问，也可以使用下方推荐卡片快速开始。',
    placeholder: '给 m1kasaz agent 发消息',
    suggestions: [
      { title: '总结一段技术方案', prompt: '帮我总结一下这个 Agent 项目的 MVP 范围', hint: '快速进入普通问答' },
      { title: '解释一段代码', prompt: '请解释一下 LangGraph 主图的作用', hint: '适合代码理解与说明' },
      { title: '生成待办清单', prompt: '请帮我拆解下一阶段开发任务', hint: '适合规划与拆解' },
    ],
  },
  document: {
    label: 'Document',
    description: '文档模式，当前支持基于文件名或路径的摘要与抽取请求。',
    subtitle: '输入文件名或路径，快速构造文档处理请求。',
    emptyTitle: '想处理哪份文档？',
    emptyHint: '当前不支持上传文件，可直接输入 report.pdf 或 note.docx 这类路径。',
    placeholder: '输入文档文件名或路径，例如 report.pdf',
    suggestions: [
      { title: '摘要 PDF', prompt: 'report.pdf', hint: 'summarize this document report.pdf' },
      { title: '抽取 DOCX', prompt: 'meeting-notes.docx', hint: 'extract this document meeting-notes.docx' },
      { title: '检查说明书', prompt: 'requirements.docx', hint: '适合做快速抽取或摘要' },
    ],
  },
  paper: {
    label: 'Paper',
    description: '推荐模式，支持论文与 AI 应用推荐，并返回可点击链接。',
    subtitle: '输入主题关键词，快速获取高引用论文或高 stars 应用推荐。',
    emptyTitle: '今天想看哪类推荐？',
    emptyHint: '可以输入 agents、rag、multimodal，也可以直接描述 application / tool / product 需求。',
    placeholder: '输入推荐主题，例如 agents 或 writing tool',
    suggestions: [
      { title: 'Agents', prompt: 'agents', hint: '推荐一篇关于 AI agents 的论文' },
      { title: 'RAG', prompt: 'rag', hint: '推荐一篇关于 retrieval 的论文' },
      { title: 'Multimodal', prompt: 'multimodal', hint: '推荐一篇关于多模态的论文' },
    ],
  },
};

const chatModelPresets = {
  quick: {
    label: '快速',
    description: '适用于大部分情况',
    payload: {
      provider: 'openai',
      name: 'gpt-4o-mini',
      temperature: 0.2,
    },
  },
  think: {
    label: '思考',
    description: '擅长解决更难的问题',
    payload: {
      provider: 'anthropic',
      name: 'claude-opus-4-7',
      temperature: 0.6,
    },
  },
};

const state = {
  mode: 'chat',
  loading: false,
  messages: [],
  recentPrompts: [],
  chatPreset: 'quick',
  settingsOpen: false,
  settingsLoading: false,
  providerSettings: {
    openai: null,
    anthropic: null,
  },
};

const elements = {
  healthBadge: document.getElementById('healthBadge'),
  healthBtn: document.getElementById('healthBtn'),
  headerStatusText: document.getElementById('headerStatusText'),
  headerModePill: document.getElementById('headerModePill'),
  pageTitle: document.getElementById('pageTitle'),
  pageSubtitle: document.getElementById('pageSubtitle'),
  modeDescription: document.getElementById('modeDescription'),
  emptyState: document.getElementById('emptyState'),
  emptyTitle: document.getElementById('emptyTitle'),
  emptyHint: document.getElementById('emptyHint'),
  suggestionList: document.getElementById('suggestionList'),
  conversationList: document.getElementById('conversationList'),
  recentList: document.getElementById('recentList'),
  promptInput: document.getElementById('promptInput'),
  loadingText: document.getElementById('loadingText'),
  errorBox: document.getElementById('errorBox'),
  settingsPanel: document.getElementById('settingsPanel'),
  settingsBtn: document.getElementById('settingsBtn'),
  settingsCloseBtn: document.getElementById('settingsCloseBtn'),
  openaiStatusBadge: document.getElementById('openaiStatusBadge'),
  anthropicStatusBadge: document.getElementById('anthropicStatusBadge'),
  openaiStatusText: document.getElementById('openaiStatusText'),
  anthropicStatusText: document.getElementById('anthropicStatusText'),
  openaiApiKeyInput: document.getElementById('openaiApiKeyInput'),
  anthropicApiKeyInput: document.getElementById('anthropicApiKeyInput'),
  saveOpenaiBtn: document.getElementById('saveOpenaiBtn'),
  saveAnthropicBtn: document.getElementById('saveAnthropicBtn'),
  clearOpenaiBtn: document.getElementById('clearOpenaiBtn'),
  clearAnthropicBtn: document.getElementById('clearAnthropicBtn'),
  sendBtn: document.getElementById('sendBtn'),
  newConversationBtn: document.getElementById('newConversationBtn'),
  tabs: Array.from(document.querySelectorAll('.mode-btn')),
  documentAction: document.getElementById('documentAction'),
  chatControls: document.getElementById('chatControls'),
  documentControls: document.getElementById('documentControls'),
  paperControls: document.getElementById('paperControls'),
  chipButtons: Array.from(document.querySelectorAll('.chip-btn')),
  chatPresetDescription: document.getElementById('chatPresetDescription'),
  chatPresetOptions: Array.from(document.querySelectorAll('.chat-preset-pill')),
};

function getActiveChatPreset() {
  return chatModelPresets[state.chatPreset] || chatModelPresets.quick;
}

function syncChatPresetUI() {
  const preset = getActiveChatPreset();
  const providerSettings = state.providerSettings[preset.payload.provider];
  const statusHint = providerSettings?.configured ? '已配置 Key' : '未配置 Key';
  elements.chatPresetDescription.textContent = `${preset.description} · ${statusHint}`;

  elements.chatPresetOptions.forEach((button) => {
    const active = button.dataset.chatPreset === state.chatPreset;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

function setMode(mode) {
  state.mode = mode;
  state.settingsOpen = false;
  const config = modeConfigs[mode];

  document.body.dataset.mode = mode;
  elements.tabs.forEach((button) => {
    button.classList.toggle('active', button.dataset.mode === mode);
  });

  elements.headerModePill.textContent = config.label;
  elements.pageTitle.textContent = '新对话';
  elements.pageSubtitle.textContent = config.subtitle;
  elements.modeDescription.textContent = config.description;
  elements.emptyTitle.textContent = config.emptyTitle;
  elements.emptyHint.textContent = config.emptyHint;
  elements.promptInput.placeholder = config.placeholder;

  elements.chatControls.classList.toggle('hidden', mode !== 'chat');
  elements.documentControls.classList.toggle('hidden', mode !== 'document');
  elements.paperControls.classList.toggle('hidden', mode !== 'paper');
  syncSettingsPanel();
  syncChatPresetUI();
  renderSuggestions();
  clearError();
  autoResizePrompt();
}

function renderSuggestions() {
  const config = modeConfigs[state.mode];
  elements.suggestionList.replaceChildren();

  config.suggestions.forEach((item) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'suggestion-btn';

    const title = document.createElement('strong');
    title.textContent = item.title;
    const hint = document.createElement('span');
    hint.textContent = item.hint;

    button.append(title, hint);
    button.addEventListener('click', async () => {
      elements.promptInput.value = item.prompt;
      autoResizePrompt();
      elements.promptInput.focus();
      await quickSubmitWithCurrentInput();
    });
    elements.suggestionList.append(button);
  });
}

function renderRecentPrompts() {
  elements.recentList.replaceChildren();

  if (!state.recentPrompts.length) {
    const empty = document.createElement('p');
    empty.className = 'recent-empty';
    empty.textContent = '暂无最近输入';
    elements.recentList.append(empty);
    return;
  }

  state.recentPrompts.forEach((item) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'recent-btn';

    const mode = document.createElement('strong');
    mode.textContent = item.modeLabel;
    const text = document.createElement('span');
    text.textContent = item.prompt;

    button.append(mode, text);
    button.addEventListener('click', () => {
      setMode(item.mode);
      elements.promptInput.value = item.prompt;
      autoResizePrompt();
      elements.promptInput.focus();
    });

    elements.recentList.append(button);
  });
}

function renderConversation() {
  const hasMessages = state.messages.length > 0;
  syncSettingsPanel();

  if (!hasMessages) {
    elements.conversationList.replaceChildren();
    return;
  }

  const fragment = document.createDocumentFragment();

  state.messages.forEach((message) => {
    const row = document.createElement('article');
    row.className = `message-row ${message.role}`;

    const card = document.createElement('div');
    card.className = 'message-card';
    if (message.loading) {
      card.classList.add('loading');
    }

    const metaRow = document.createElement('div');
    metaRow.className = 'message-meta-row';

    const role = document.createElement('span');
    role.className = 'message-role';
    role.textContent = message.role === 'user' ? '你' : message.role === 'assistant' ? 'm1kasaz agent' : '提示';
    metaRow.append(role);

    if (message.modeLabel) {
      const mode = document.createElement('span');
      mode.textContent = message.modeLabel;
      metaRow.append(mode);
    }

    if (message.presetLabel) {
      const preset = document.createElement('span');
      preset.className = 'message-preset-pill';
      preset.textContent = message.presetLabel;
      metaRow.append(preset);
    }

    const content = document.createElement('p');
    content.className = 'message-content';
    content.textContent = message.content;

    card.append(metaRow, content);

    if (message.artifacts) {
      const artifactSection = renderArtifacts(message.artifacts);
      if (artifactSection) {
        card.append(artifactSection);
      }
    }

    row.append(card);
    fragment.append(row);
  });

  elements.conversationList.replaceChildren(fragment);
  elements.conversationList.lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function renderArtifacts(artifacts) {
  if (!artifacts || typeof artifacts !== 'object') {
    return null;
  }

  const section = document.createElement('section');
  section.className = 'artifact-section';

  if (artifacts.mode === 'document' && artifacts.document) {
    section.append(renderDocumentArtifact(artifacts.document, artifacts.links || []));
  }

  if (artifacts.recommendation) {
    section.append(renderRecommendationArtifact(artifacts.recommendation, artifacts.links || []));
  }

  if (!section.childElementCount) {
    return null;
  }
  return section;
}

function renderDocumentArtifact(documentArtifact, links) {
  const card = document.createElement('div');
  card.className = 'artifact-card';

  const title = document.createElement('h4');
  title.className = 'artifact-title';
  title.textContent = `文档${documentArtifact.action || '处理'}结果`;
  card.append(title);

  if (documentArtifact.output) {
    const meta = document.createElement('div');
    meta.className = 'artifact-meta';
    meta.append(
      createMetaChip(documentArtifact.output.mime_type || 'unknown'),
      createMetaChip(`${documentArtifact.output.size_bytes || 0} bytes`),
    );
    card.append(meta);
  }

  const linkRow = renderLinkRow(links);
  if (linkRow) {
    card.append(linkRow);
  }

  return card;
}

function renderRecommendationArtifact(recommendation, links) {
  const card = document.createElement('div');
  card.className = 'artifact-card recommendation-card';

  const title = document.createElement('h4');
  title.className = 'artifact-title';
  title.textContent = recommendation.item?.title || '推荐结果';
  card.append(title);

  const summary = document.createElement('p');
  summary.className = 'artifact-summary';
  summary.textContent = recommendation.item?.summary || recommendation.reason || '';
  card.append(summary);

  const meta = document.createElement('div');
  meta.className = 'artifact-meta';
  if (recommendation.item?.source_provider) meta.append(createMetaChip(recommendation.item.source_provider));
  if (recommendation.item?.stars) meta.append(createMetaChip(`★ ${recommendation.item.stars}`));
  if (recommendation.item?.citation_count) meta.append(createMetaChip(`Citations ${recommendation.item.citation_count}`));
  if (recommendation.item?.published_at) meta.append(createMetaChip(recommendation.item.published_at));
  if (meta.childElementCount) {
    card.append(meta);
  }

  const linkRow = renderLinkRow(links);
  if (linkRow) {
    card.append(linkRow);
  }

  return card;
}

function renderLinkRow(links) {
  const validLinks = (links || []).filter((link) => isRenderableLink(link?.url));
  if (!validLinks.length) {
    return null;
  }

  const row = document.createElement('div');
  row.className = 'artifact-links';
  validLinks.forEach((link) => {
    const anchor = document.createElement('a');
    anchor.className = `artifact-link artifact-link-${link.role || 'landing'}`;
    anchor.href = link.url;
    anchor.textContent = link.label || link.url;
    if (link.url.startsWith('http://') || link.url.startsWith('https://')) {
      anchor.target = '_blank';
      anchor.rel = 'noopener noreferrer';
    }
    if (link.role === 'download') {
      anchor.setAttribute('download', '');
    }
    row.append(anchor);
  });
  return row;
}

function createMetaChip(value) {
  const chip = document.createElement('span');
  chip.className = 'artifact-chip';
  chip.textContent = String(value);
  return chip;
}

function isRenderableLink(url) {
  return typeof url === 'string' && (url.startsWith('/artifacts/') || url.startsWith('http://') || url.startsWith('https://'));
}

function setLoading(loading) {
  state.loading = loading;
  elements.loadingText.textContent = loading ? '思考中...' : '';

  [
    elements.sendBtn,
    elements.healthBtn,
    elements.newConversationBtn,
    ...elements.chatPresetOptions,
    ...elements.tabs,
    ...elements.chipButtons,
  ].forEach((element) => {
    if (element) {
      element.disabled = loading;
    }
  });
}

function showError(message) {
  elements.errorBox.textContent = message;
  elements.errorBox.classList.remove('hidden');
}

function clearError() {
  elements.errorBox.textContent = '';
  elements.errorBox.classList.add('hidden');
}

function autoResizePrompt() {
  elements.promptInput.style.height = 'auto';
  elements.promptInput.style.height = `${Math.min(elements.promptInput.scrollHeight, 220)}px`;
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `请求失败 (${response.status})`;
    try {
      const data = await response.json();
      detail = data.detail ? JSON.stringify(data.detail) : detail;
    } catch {
      // ignore parse failure
    }
    throw new Error(detail);
  }
  return response.json();
}

async function checkHealth() {
  try {
    const data = await requestJson('/health');
    const ok = data.status === 'ok';
    elements.healthBadge.textContent = ok ? '服务正常' : '状态未知';
    elements.healthBadge.className = `status-badge ${ok ? 'ok' : 'pending'}`;
    elements.headerStatusText.textContent = ok ? '服务正常，可直接开始对话' : '服务状态未知';
  } catch (error) {
    elements.healthBadge.textContent = '服务异常';
    elements.healthBadge.className = 'status-badge error';
    elements.headerStatusText.textContent = '服务异常，请检查后端';
    showError(error.message);
  }
}

function syncSettingsPanel() {
  elements.settingsPanel.classList.toggle('hidden', !state.settingsOpen);
  elements.emptyState.classList.toggle('hidden', state.settingsOpen || state.messages.length > 0);
  elements.conversationList.classList.toggle('hidden', state.settingsOpen || !state.messages.length);
}

function renderProviderStatus(provider) {
  const config = state.providerSettings[provider];
  const badge = provider === 'openai' ? elements.openaiStatusBadge : elements.anthropicStatusBadge;
  const text = provider === 'openai' ? elements.openaiStatusText : elements.anthropicStatusText;
  const defaultLabel = state.settingsLoading ? '读取中' : '未配置';

  if (!config) {
    badge.textContent = defaultLabel;
    badge.className = `status-badge ${state.settingsLoading ? 'pending' : 'error'}`;
    text.textContent = state.settingsLoading ? '正在读取配置状态。' : '当前未配置 API Key。';
    return;
  }

  badge.textContent = config.configured ? '已配置' : '未配置';
  badge.className = `status-badge ${config.configured ? 'ok' : 'error'}`;

  if (!config.configured) {
    text.textContent = '当前未配置 API Key。';
    return;
  }

  const sourceLabel = config.source === 'stored' ? '本地设置' : config.source === 'env' ? '环境变量' : '未配置';
  text.textContent = `来源：${sourceLabel}${config.masked_api_key ? ` · ${config.masked_api_key}` : ''}`;
}

function renderSettingsStatus() {
  renderProviderStatus('openai');
  renderProviderStatus('anthropic');
  syncChatPresetUI();
}

function setSettingsLoading(loading) {
  state.settingsLoading = loading;
  [
    elements.settingsBtn,
    elements.settingsCloseBtn,
    elements.saveOpenaiBtn,
    elements.saveAnthropicBtn,
    elements.clearOpenaiBtn,
    elements.clearAnthropicBtn,
  ].forEach((element) => {
    if (element) {
      element.disabled = loading;
    }
  });
}

async function loadSettings() {
  setSettingsLoading(true);
  renderSettingsStatus();
  try {
    const data = await requestJson('/settings/model');
    state.providerSettings = {
      openai: data.providers.find((item) => item.provider === 'openai') || null,
      anthropic: data.providers.find((item) => item.provider === 'anthropic') || null,
    };
    renderSettingsStatus();
  } finally {
    setSettingsLoading(false);
    renderSettingsStatus();
  }
}

function openSettingsPanel() {
  state.settingsOpen = true;
  syncSettingsPanel();
  clearError();
  elements.pageTitle.textContent = '模型配置';
  elements.pageSubtitle.textContent = '在当前机器上保存 OpenAI / Anthropic API Key。';
  elements.headerModePill.textContent = 'Settings';
  requestAnimationFrame(() => {
    elements.settingsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

function closeSettingsPanel() {
  state.settingsOpen = false;
  syncSettingsPanel();
  const config = modeConfigs[state.mode];
  elements.headerModePill.textContent = config.label;
  elements.pageTitle.textContent = '新对话';
  elements.pageSubtitle.textContent = config.subtitle;
}

async function saveProviderKey(provider, inputElement) {
  const apiKey = inputElement.value.trim();
  if (!apiKey) {
    throw new Error('请先输入 API Key。');
  }
  setSettingsLoading(true);
  try {
    await requestJson(`/settings/model/${provider}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, clear_api_key: false }),
    });
    inputElement.value = '';
    await loadSettings();
  } finally {
    setSettingsLoading(false);
  }
}

async function clearProviderKey(provider, inputElement) {
  setSettingsLoading(true);
  try {
    await requestJson(`/settings/model/${provider}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clear_api_key: true }),
    });
    inputElement.value = '';
    await loadSettings();
  } finally {
    setSettingsLoading(false);
  }
}

function pushRecentPrompt(mode, prompt) {
  const trimmed = prompt.trim();
  if (!trimmed) {
    return;
  }

  state.recentPrompts = [
    { mode, modeLabel: modeConfigs[mode].label, prompt: trimmed },
    ...state.recentPrompts.filter((item) => !(item.mode === mode && item.prompt === trimmed)),
  ].slice(0, 8);

  renderRecentPrompts();
}

function buildChatSubmission() {
  const preset = getActiveChatPreset();
  const payload = {
    intent: 'chat',
    user_input: elements.promptInput.value.trim(),
    model: { ...preset.payload },
  };

  return {
    payload,
    userText: payload.user_input,
    presetLabel: preset.label,
  };
}

function buildDocumentSubmission() {
  const raw = elements.promptInput.value.trim();
  return {
    payload: {
      intent: 'document',
      user_input: `${elements.documentAction.value} this document ${raw}`,
    },
    userText: `[${elements.documentAction.value}] ${raw}`,
    presetLabel: null,
  };
}

function buildPaperSubmission() {
  const topic = elements.promptInput.value.trim() || 'agents';
  return {
    payload: {
      intent: 'paper',
      user_input: `recommend one AI paper about ${topic}`,
    },
    userText: `推荐一篇关于 ${topic} 的 AI 论文`,
    presetLabel: null,
  };
}

function validateSubmission(payload) {
  if (state.mode === 'chat') {
    if (!payload.user_input) {
      throw new Error('请先输入聊天内容。');
    }
    return;
  }

  if (!elements.promptInput.value.trim()) {
    throw new Error(state.mode === 'document' ? '请先填写文档文件名或路径。' : '请先输入论文主题。');
  }
}

function buildSubmission() {
  if (state.mode === 'document') {
    return buildDocumentSubmission();
  }
  if (state.mode === 'paper') {
    return buildPaperSubmission();
  }
  return buildChatSubmission();
}

async function quickSubmitWithCurrentInput() {
  if (state.loading) {
    return;
  }
  await submitCurrentPrompt();
}

async function submitCurrentPrompt() {
  clearError();

  try {
    const { payload, userText, presetLabel } = buildSubmission();
    validateSubmission(payload);
    pushRecentPrompt(state.mode, elements.promptInput.value.trim() || userText);

    state.messages.push({
      role: 'user',
      modeLabel: modeConfigs[state.mode].label,
      content: userText,
      presetLabel,
    });

    const loadingIndex = state.messages.push({
      role: 'assistant',
      modeLabel: modeConfigs[state.mode].label,
      content: '正在思考，请稍候...',
      loading: true,
      presetLabel,
    }) - 1;

    renderConversation();
    setLoading(true);
    syncChatPresetUI();

    const data = await requestJson('/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    state.messages[loadingIndex] = {
      role: 'assistant',
      modeLabel: modeConfigs[state.mode].label,
      content: data.response || '',
      presetLabel,
      artifacts: data.artifacts || null,
    };

    elements.promptInput.value = '';
    autoResizePrompt();
    renderConversation();
  } catch (error) {
    showError(error.message);

    if (state.messages.length && state.messages[state.messages.length - 1].loading) {
      state.messages[state.messages.length - 1] = {
        role: 'system',
        modeLabel: modeConfigs[state.mode].label,
        content: error.message,
      };
      renderConversation();
    }
  } finally {
    setLoading(false);
  }
}

function resetConversation() {
  state.messages = [];
  elements.promptInput.value = '';
  clearError();
  autoResizePrompt();
  renderConversation();
  elements.promptInput.focus();
}

function handleChatPresetSelection(presetKey) {
  if (!chatModelPresets[presetKey]) {
    return;
  }

  state.chatPreset = presetKey;
  syncChatPresetUI();
}

function bindEvents() {
  elements.tabs.forEach((button) => {
    button.addEventListener('click', () => setMode(button.dataset.mode));
  });

  elements.healthBtn.addEventListener('click', async () => {
    clearError();
    await checkHealth();
  });

  elements.settingsBtn.addEventListener('click', () => {
    openSettingsPanel();
  });

  elements.settingsCloseBtn.addEventListener('click', () => {
    closeSettingsPanel();
  });

  elements.saveOpenaiBtn.addEventListener('click', async () => {
    clearError();
    try {
      await saveProviderKey('openai', elements.openaiApiKeyInput);
    } catch (error) {
      showError(error.message);
    }
  });

  elements.saveAnthropicBtn.addEventListener('click', async () => {
    clearError();
    try {
      await saveProviderKey('anthropic', elements.anthropicApiKeyInput);
    } catch (error) {
      showError(error.message);
    }
  });

  elements.clearOpenaiBtn.addEventListener('click', async () => {
    clearError();
    try {
      await clearProviderKey('openai', elements.openaiApiKeyInput);
    } catch (error) {
      showError(error.message);
    }
  });

  elements.clearAnthropicBtn.addEventListener('click', async () => {
    clearError();
    try {
      await clearProviderKey('anthropic', elements.anthropicApiKeyInput);
    } catch (error) {
      showError(error.message);
    }
  });

  elements.newConversationBtn.addEventListener('click', resetConversation);

  elements.promptInput.addEventListener('input', autoResizePrompt);
  elements.promptInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (!state.loading) {
        submitCurrentPrompt();
      }
    }
  });

  elements.sendBtn.addEventListener('click', submitCurrentPrompt);

  elements.chatPresetOptions.forEach((button) => {
    button.addEventListener('click', () => {
      handleChatPresetSelection(button.dataset.chatPreset);
    });
  });

  elements.chipButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      elements.promptInput.value = button.dataset.topic || '';
      autoResizePrompt();
      elements.promptInput.focus();
      await quickSubmitWithCurrentInput();
    });
  });
}

async function init() {
  setMode('chat');
  syncChatPresetUI();
  renderRecentPrompts();
  renderConversation();
  bindEvents();
  autoResizePrompt();
  await Promise.all([checkHealth(), loadSettings()]);
}

init().catch((error) => {
  showError(error.message);
});

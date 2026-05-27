const assistantConfig = {
  subtitle: '直接描述你的需求，系统会自动完成问答、检索或文档处理。',
  emptyTitle: '今天想完成什么？',
  emptyHint: '支持普通问答、论文/应用检索，以及上传 PDF / DOCX 后做抽取、总结、问答或转换。',
  placeholder: '请输入问题',
  suggestions: [
    { title: '推荐论文', prompt: '推荐一篇关于 agents 的经典论文', hint: '自动触发论文检索' },
    { title: '推荐应用', prompt: '推荐一个 AI 写作工具', hint: '自动触发应用检索' },
    { title: '文档处理', prompt: '总结这个文档', hint: '可先上传 PDF / DOCX，再让系统自动识别动作' },
  ],
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
  loading: false,
  messages: [],
  recentPrompts: [],
  chatPreset: 'quick',
  settingsOpen: false,
  settingsLoading: false,
  selectedFile: null,
  providerSettings: {
    openai: null,
    anthropic: null,
    openai_compatible: null,
  },
};

const elements = {
  healthBadge: document.getElementById('healthBadge'),
  healthBtn: document.getElementById('healthBtn'),
  headerStatusText: document.getElementById('headerStatusText'),
  emptyState: document.getElementById('emptyState'),
  emptyTitle: document.getElementById('emptyTitle'),
  emptyHint: document.getElementById('emptyHint'),
  suggestionList: document.getElementById('suggestionList'),
  conversationList: document.getElementById('conversationList'),
  recentList: document.getElementById('recentList'),
  promptInput: document.getElementById('promptInput'),
  documentFileInput: document.getElementById('documentFileInput'),
  documentFileTrigger: document.getElementById('documentFileTrigger'),
  selectedFileBadge: document.getElementById('selectedFileBadge'),
  selectedFileName: document.getElementById('selectedFileName'),
  clearSelectedFileBtn: document.getElementById('clearSelectedFileBtn'),
  loadingText: document.getElementById('loadingText'),
  errorBox: document.getElementById('errorBox'),
  settingsPanel: document.getElementById('settingsPanel'),
  settingsBtn: document.getElementById('settingsBtn'),
  settingsCloseBtn: document.getElementById('settingsCloseBtn'),
  openaiStatusBadge: document.getElementById('openaiStatusBadge'),
  anthropicStatusBadge: document.getElementById('anthropicStatusBadge'),
  compatibleStatusBadge: document.getElementById('compatibleStatusBadge'),
  openaiStatusText: document.getElementById('openaiStatusText'),
  anthropicStatusText: document.getElementById('anthropicStatusText'),
  compatibleStatusText: document.getElementById('compatibleStatusText'),
  openaiApiKeyInput: document.getElementById('openaiApiKeyInput'),
  anthropicApiKeyInput: document.getElementById('anthropicApiKeyInput'),
  compatibleBaseUrlInput: document.getElementById('compatibleBaseUrlInput'),
  compatibleApiKeyInput: document.getElementById('compatibleApiKeyInput'),
  saveOpenaiBtn: document.getElementById('saveOpenaiBtn'),
  saveAnthropicBtn: document.getElementById('saveAnthropicBtn'),
  saveCompatibleBtn: document.getElementById('saveCompatibleBtn'),
  clearOpenaiBtn: document.getElementById('clearOpenaiBtn'),
  clearAnthropicBtn: document.getElementById('clearAnthropicBtn'),
  clearCompatibleBtn: document.getElementById('clearCompatibleBtn'),
  sendBtn: document.getElementById('sendBtn'),
  newConversationBtn: document.getElementById('newConversationBtn'),
  chatControls: document.getElementById('chatControls'),
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

function syncAssistantShell() {
  elements.emptyTitle.textContent = assistantConfig.emptyTitle;
  elements.emptyHint.textContent = assistantConfig.emptyHint;
  elements.promptInput.placeholder = assistantConfig.placeholder;
  syncSettingsPanel();
  syncChatPresetUI();
  renderSuggestions();
  clearError();
  autoResizePrompt();
}

function renderSuggestions() {
  elements.suggestionList.replaceChildren();

  assistantConfig.suggestions.forEach((item) => {
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

    const title = document.createElement('strong');
    title.textContent = '最近输入';
    const text = document.createElement('span');
    text.textContent = item.prompt;

    button.append(title, text);
    button.addEventListener('click', () => {
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

    if (message.presetLabel) {
      const preset = document.createElement('span');
      preset.className = 'message-preset-pill';
      preset.textContent = message.presetLabel;
      metaRow.append(preset);
    }

    const content = renderMessageContent(message);

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

function renderMessageContent(message) {
  const text = String(message.content || '');
  if (message.role === 'user' || message.loading) {
    const content = document.createElement('p');
    content.className = 'message-content';
    content.textContent = text;
    return content;
  }

  const blocks = splitMessageBlocks(text);
  if (blocks.length <= 1) {
    const content = document.createElement('p');
    content.className = 'message-content';
    content.textContent = text;
    return content;
  }

  const wrapper = document.createElement('div');
  wrapper.className = 'message-content-stack';
  blocks.forEach((block) => {
    const paragraph = document.createElement('p');
    paragraph.className = 'message-content message-paragraph';
    paragraph.textContent = block;
    wrapper.append(paragraph);
  });
  return wrapper;
}

function splitMessageBlocks(text) {
  const normalized = text.replace(/\r\n/g, '\n').trim();
  if (!normalized) {
    return [''];
  }

  const paragraphs = normalized
    .split(/\n{2,}/)
    .flatMap((paragraph) => splitLongParagraph(paragraph))
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

  return paragraphs.length ? paragraphs : [normalized];
}

function splitLongParagraph(paragraph) {
  const cleaned = paragraph.trim();
  if (!cleaned) {
    return [];
  }
  if (cleaned.length <= 120) {
    return [cleaned];
  }

  const sentences = cleaned.match(/[^。！？!?；;]+[。！？!?；;]?/g) || [cleaned];
  const chunks = [];
  let current = '';

  sentences.forEach((sentence) => {
    const next = `${current}${sentence}`.trim();
    if (current && next.length > 120) {
      chunks.push(current.trim());
      current = sentence;
      return;
    }
    current = `${current}${sentence}`;
  });

  if (current.trim()) {
    chunks.push(current.trim());
  }

  return chunks.length ? chunks : [cleaned];
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

  const meta = document.createElement('div');
  meta.className = 'artifact-meta';
  if (documentArtifact.source?.type) meta.append(createMetaChip(documentArtifact.source.type));
  if (documentArtifact.source?.origin === 'uploaded') meta.append(createMetaChip('uploaded'));
  if (documentArtifact.source?.name) meta.append(createMetaChip(documentArtifact.source.name));
  if (documentArtifact.output?.mime_type) meta.append(createMetaChip(documentArtifact.output.mime_type));
  if (documentArtifact.output?.size_bytes) meta.append(createMetaChip(`${documentArtifact.output.size_bytes} bytes`));
  if (meta.childElementCount) {
    card.append(meta);
  }

  if (documentArtifact.summary) {
    const summary = document.createElement('p');
    summary.className = 'artifact-summary';
    summary.textContent = documentArtifact.summary;
    card.append(summary);
  }

  if (documentArtifact.answer) {
    const answer = document.createElement('p');
    answer.className = 'artifact-summary';
    answer.textContent = documentArtifact.answer;
    card.append(answer);
  }

  if (documentArtifact.text_preview) {
    const preview = document.createElement('p');
    preview.className = 'artifact-preview';
    preview.textContent = documentArtifact.text_preview;
    card.append(preview);
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

function getProviderElements(provider) {
  if (provider === 'openai') {
    return { badge: elements.openaiStatusBadge, text: elements.openaiStatusText };
  }
  if (provider === 'anthropic') {
    return { badge: elements.anthropicStatusBadge, text: elements.anthropicStatusText };
  }
  return { badge: elements.compatibleStatusBadge, text: elements.compatibleStatusText };
}

function renderProviderStatus(provider) {
  const config = state.providerSettings[provider];
  const { badge, text } = getProviderElements(provider);
  const defaultLabel = state.settingsLoading ? '读取中' : '未配置';

  if (!config) {
    badge.textContent = defaultLabel;
    badge.className = `status-badge ${state.settingsLoading ? 'pending' : 'error'}`;
    text.textContent = state.settingsLoading ? '正在读取配置状态。' : '当前未配置 API Key。';
    return;
  }

  badge.textContent = config.configured ? '已配置' : '未配置';
  badge.className = `status-badge ${config.configured ? 'ok' : 'error'}`;

  const sourceLabel = config.source === 'stored' ? '本地设置' : config.source === 'env' ? '环境变量' : '未配置';
  const baseUrlSourceLabel = config.base_url_source === 'stored' ? '本地设置' : config.base_url_source === 'env' ? '环境变量' : '未配置';

  if (provider === 'openai_compatible') {
    if (!config.configured && !config.base_url) {
      text.textContent = '当前未配置 Base URL 和 API Key。';
      return;
    }

    const parts = [];
    parts.push(config.base_url ? `Base URL：${config.base_url}（${baseUrlSourceLabel}）` : 'Base URL：未配置');
    parts.push(config.configured ? `API Key 来源：${sourceLabel}${config.masked_api_key ? ` · ${config.masked_api_key}` : ''}` : 'API Key：未配置');
    text.textContent = parts.join('；');
    return;
  }

  if (!config.configured) {
    text.textContent = '当前未配置 API Key。';
    return;
  }

  text.textContent = `来源：${sourceLabel}${config.masked_api_key ? ` · ${config.masked_api_key}` : ''}`;
}

function renderSettingsStatus() {
  renderProviderStatus('openai');
  renderProviderStatus('anthropic');
  renderProviderStatus('openai_compatible');
  syncChatPresetUI();
}

function setSettingsLoading(loading) {
  state.settingsLoading = loading;
  [
    elements.settingsBtn,
    elements.settingsCloseBtn,
    elements.saveOpenaiBtn,
    elements.saveAnthropicBtn,
    elements.saveCompatibleBtn,
    elements.clearOpenaiBtn,
    elements.clearAnthropicBtn,
    elements.clearCompatibleBtn,
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
      openai_compatible: data.providers.find((item) => item.provider === 'openai_compatible') || null,
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
  requestAnimationFrame(() => {
    elements.settingsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

function closeSettingsPanel() {
  state.settingsOpen = false;
  syncSettingsPanel();
  syncAssistantShell();
}

async function saveProviderKey(provider, inputElement, extraPayload = {}) {
  const apiKey = inputElement.value.trim();
  if (!apiKey) {
    throw new Error('请先输入 API Key。');
  }
  setSettingsLoading(true);
  try {
    await requestJson(`/settings/model/${provider}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, clear_api_key: false, ...extraPayload }),
    });
    inputElement.value = '';
    await loadSettings();
  } finally {
    setSettingsLoading(false);
  }
}

async function clearProviderKey(provider, inputElement, extraPayload = {}) {
  setSettingsLoading(true);
  try {
    await requestJson(`/settings/model/${provider}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clear_api_key: true, ...extraPayload }),
    });
    inputElement.value = '';
    await loadSettings();
  } finally {
    setSettingsLoading(false);
  }
}

function pushRecentPrompt(prompt) {
  const trimmed = prompt.trim();
  if (!trimmed) {
    return;
  }

  state.recentPrompts = [
    { prompt: trimmed },
    ...state.recentPrompts.filter((item) => item.prompt !== trimmed),
  ].slice(0, 8);

  renderRecentPrompts();
}

function buildSubmission() {
  const userInput = elements.promptInput.value.trim();
  if (!userInput && !state.selectedFile) {
    throw new Error('请先输入内容或选择文档。');
  }

  const preset = getActiveChatPreset();
  if (state.selectedFile) {
    const formData = new FormData();
    formData.set('user_input', userInput);
    formData.set('model', JSON.stringify({ ...preset.payload }));
    formData.set('file', state.selectedFile);
    return {
      url: '/invoke/upload',
      options: { method: 'POST', body: formData },
      userText: userInput || `处理文档：${state.selectedFile.name}`,
      presetLabel: preset.label,
    };
  }

  return {
    url: '/invoke',
    options: {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_input: userInput,
        model: { ...preset.payload },
      }),
    },
    userText: userInput,
    presetLabel: preset.label,
  };
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
    const { url, options, userText, presetLabel } = buildSubmission();
    pushRecentPrompt(userText);

    state.messages.push({
      role: 'user',
      content: userText,
      presetLabel,
    });

    const loadingIndex = state.messages.push({
      role: 'assistant',
      content: '正在思考，请稍候...',
      loading: true,
      presetLabel,
    }) - 1;

    renderConversation();
    setLoading(true);
    syncChatPresetUI();

    const data = await requestJson(url, options);

    state.messages[loadingIndex] = {
      role: 'assistant',
      content: data.response || '',
      presetLabel,
      artifacts: data.artifacts || null,
    };

    elements.promptInput.value = '';
    elements.documentFileInput.value = '';
    state.selectedFile = null;
    syncSelectedFileUI();
    autoResizePrompt();
    renderConversation();
  } catch (error) {
    showError(error.message);

    if (state.messages.length && state.messages[state.messages.length - 1].loading) {
      state.messages[state.messages.length - 1] = {
        role: 'system',
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
  state.selectedFile = null;
  elements.promptInput.value = '';
  elements.documentFileInput.value = '';
  syncSelectedFileUI();
  clearError();
  autoResizePrompt();
  renderConversation();
  elements.promptInput.focus();
}

function syncSelectedFileUI() {
  const file = state.selectedFile;
  const hasFile = Boolean(file);
  elements.selectedFileBadge.classList.toggle('hidden', !hasFile);
  elements.selectedFileName.textContent = hasFile ? file.name : '';
  elements.documentFileTrigger.classList.toggle('active', hasFile);
}

function handleSelectedFile(file) {
  if (!file) {
    state.selectedFile = null;
    syncSelectedFileUI();
    return;
  }
  const lowerName = file.name.toLowerCase();
  if (!lowerName.endsWith('.pdf') && !lowerName.endsWith('.docx')) {
    throw new Error('仅支持上传 .pdf 或 .docx 文件。');
  }
  state.selectedFile = file;
  syncSelectedFileUI();
}

function handleChatPresetSelection(presetKey) {
  if (!chatModelPresets[presetKey]) {
    return;
  }

  state.chatPreset = presetKey;
  syncChatPresetUI();
}

function bindEvents() {
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

  elements.saveCompatibleBtn.addEventListener('click', async () => {
    clearError();
    try {
      const baseUrl = elements.compatibleBaseUrlInput.value.trim();
      if (!baseUrl) {
        throw new Error('请先输入兼容服务 Base URL。');
      }
      await saveProviderKey('openai_compatible', elements.compatibleApiKeyInput, {
        base_url: baseUrl,
        clear_base_url: false,
      });
      elements.compatibleBaseUrlInput.value = '';
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

  elements.clearCompatibleBtn.addEventListener('click', async () => {
    clearError();
    try {
      await clearProviderKey('openai_compatible', elements.compatibleApiKeyInput, { clear_base_url: true });
      elements.compatibleBaseUrlInput.value = '';
    } catch (error) {
      showError(error.message);
    }
  });

  elements.newConversationBtn.addEventListener('click', resetConversation);

  elements.documentFileTrigger.addEventListener('click', () => {
    elements.documentFileInput.click();
  });

  elements.documentFileInput.addEventListener('change', () => {
    clearError();
    try {
      handleSelectedFile(elements.documentFileInput.files?.[0] || null);
    } catch (error) {
      elements.documentFileInput.value = '';
      showError(error.message);
    }
  });

  elements.clearSelectedFileBtn.addEventListener('click', () => {
    state.selectedFile = null;
    elements.documentFileInput.value = '';
    syncSelectedFileUI();
  });

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
}

async function init() {
  syncAssistantShell();
  renderRecentPrompts();
  renderConversation();
  bindEvents();
  syncSelectedFileUI();
  autoResizePrompt();
  await Promise.all([checkHealth(), loadSettings()]);
}

init().catch((error) => {
  showError(error.message);
});

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function setup() {
  const calls = [];
  const store = new Map();
  const context = vm.createContext({
    document: { addEventListener() {} },
    sessionStorage: { setItem: (k, v) => store.set(k, v) },
    console,
    fetch: async (url, options) => {
      calls.push({ url, ...options });
      return { ok: true, status: 200, json: async () => ({ response: 'Resposta', conversation_id: 42 }) };
    }
  });
  vm.runInContext(readFileSync(path.join(__dirname, '../web/script.js'), 'utf8') + '\nglobalThis.Interface = JarvisInterface;', context);
  const ui = Object.create(context.Interface.prototype);
  Object.assign(ui, {
    token: 'test-token', sessionReady: Promise.resolve(), apiUrl: 'http://test',
    conversationId: null, messageInput: { value: '' },
    chatMessages: { appendChild() {} },
    createMessageElement: () => ({}), updateUIState() {}, scrollToBottom() {},
    showTypingIndicator() {}, hideTypingIndicator() {},
    showErrorMessage(message) { throw new Error(message); }
  });
  return { ui, calls, store };
}

test('envia a credencial e reutiliza a conversa retornada pela API', async () => {
  const { ui, calls, store } = setup();
  ui.messageInput.value = 'Meu nome é Samuel';
  await ui.sendMessage();
  ui.messageInput.value = 'Qual é meu nome?';
  await ui.sendMessage();
  assert.equal(calls.length, 2);
  assert.equal(calls[0].headers.Authorization, 'Bearer test-token');
  assert.equal(JSON.parse(calls[0].body).conversation_id, null);
  assert.equal(JSON.parse(calls[1].body).conversation_id, 42);
  assert.equal(store.get('jarvis_conversation'), '42');
  assert.equal(ui.currentSessionId, '42');
});

test('associa a pergunta real ao feedback da resposta', async () => {
  const { ui } = setup();
  const rendered = [];
  ui.createMessageElement = (...args) => { rendered.push(args); return {}; };
  ui.messageInput.value = 'Minha pergunta';
  await ui.sendMessage();
  assert.deepEqual(rendered[1], ['Resposta', 'bot', 'Minha pergunta']);
});

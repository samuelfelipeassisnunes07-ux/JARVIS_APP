class JarvisInterface {
  constructor() {
    this.apiUrl = window.JARVIS_API_URL || (location.port === '8000' ? location.origin : 'http://127.0.0.1:8000');
    this.isProcessing = false;
    this.isRecording = false;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.token = localStorage.getItem('jarvis_token');
    this.conversationId = this.token ? Number(sessionStorage.getItem('jarvis_conversation')) || null : null;
    this.currentSessionId = this.conversationId ? String(this.conversationId) : null;
    this.sessionReady = this.ensureSession();

    this.init();
  }

  init() {
    this.bindElements();
    this.bindEvents();
    this.addWelcomeMessage();
    this.updateStats();
  }

  bindElements() {
    // Chat elements
    this.chatMessages = document.getElementById('chat-messages');
    this.messageInput = document.getElementById('message-input');
    this.sendBtn = document.getElementById('send-btn');
    this.voiceBtn = document.getElementById('voice-btn');
    this.typingIndicator = document.getElementById('typing-indicator');

    // Modal elements
    this.modals = {
      settings: document.getElementById('settings-modal'),
      stats: document.getElementById('stats-modal'),
      feedback: null // Created dynamically
    };

    // Buttons
    this.settingsBtn = document.getElementById('settings-btn');
    this.statsBtn = document.getElementById('stats-btn');
  }

  bindEvents() {
    // Chat events
    this.messageInput?.addEventListener('keydown', (e) => this.handleKeyDown(e));
    this.sendBtn?.addEventListener('click', () => this.sendMessage());
    this.voiceBtn?.addEventListener('click', () => this.toggleVoiceRecording());

    // Modal events
    this.settingsBtn?.addEventListener('click', () => this.showModal('settings'));
    this.statsBtn?.addEventListener('click', () => this.showModal('stats'));

    // Close modals
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal')) {
        this.hideAllModals();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.hideAllModals();
      }
    });
  }

  generateSessionId() {
    return 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  async ensureSession() {
    if (this.token) return;
    const response = await fetch(`${this.apiUrl}/session`, { method: 'POST' });
    if (!response.ok) throw new Error('Não foi possível iniciar a sessão');
    const data = await response.json();
    this.token = data.token;
    localStorage.setItem('jarvis_token', this.token);
  }

  async authorizedFetch(path, options = {}) {
    try {
      if (!this.sessionReady) this.sessionReady = this.ensureSession();
      await this.sessionReady;
    } catch (error) {
      this.sessionReady = null;
      throw error;
    }
    const response = await fetch(`${this.apiUrl}${path}`, {
      ...options,
      headers: { ...options.headers, Authorization: `Bearer ${this.token}` }
    });
    if (response.status === 401) {
      throw new Error('Credencial inválida. A sessão precisa ser recuperada ou reiniciada.');
    }
    return response;
  }

  addWelcomeMessage() {
    const welcomeMessage = this.createMessageElement(
      'Olá! Eu sou o Jarvis, seu assistente de IA inteligente. Como posso ajudar você hoje? 🤖',
      'bot'
    );
    this.chatMessages?.appendChild(welcomeMessage);
  }

  handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  async sendMessage() {
    const text = this.messageInput?.value.trim();
    if (!text || this.isProcessing) return;

    this.isProcessing = true;
    this.updateUIState(true);

    try {
      // Add user message
      const userMessage = this.createMessageElement(text, 'user');
      this.chatMessages?.appendChild(userMessage);
      this.scrollToBottom();
      this.messageInput.value = '';

      // Show typing indicator
      this.showTypingIndicator();

      // Send to API
      const response = await this.fetchResponse(text);
      this.hideTypingIndicator();

      if (response.ok) {
        const data = await response.json();
        this.conversationId = data.conversation_id;
        this.currentSessionId = String(data.conversation_id);
        sessionStorage.setItem('jarvis_conversation', String(data.conversation_id));
        const botMessage = this.createMessageElement(
          data.response || data.error || 'Desculpe, não entendi.',
          'bot', text
        );
        this.chatMessages?.appendChild(botMessage);
        this.scrollToBottom();
      } else {
        const data = await response.json().catch(() => ({}));
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Erro na resposta do servidor');
      }

    } catch (error) {
      console.error('Erro:', error);
      this.hideTypingIndicator();
      this.showErrorMessage(error.message || 'Erro de conexão. Verifique se o servidor está rodando.');
    } finally {
      this.isProcessing = false;
      this.updateUIState(false);
      this.scrollToBottom();
    }
  }

  async fetchResponse(text) {
    return this.authorizedFetch('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        text,
        conversation_id: this.conversationId
      })
    });
  }

  createMessageElement(content, type, userQuestion = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textP = document.createElement('p');
    textP.textContent = content;
    contentDiv.appendChild(textP);

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = new Date().toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    });
    contentDiv.appendChild(timeSpan);

    if (type === 'user') {
      messageDiv.appendChild(contentDiv);
      messageDiv.appendChild(avatar);
    } else {
      messageDiv.appendChild(avatar);
      messageDiv.appendChild(contentDiv);

      // Apenas respostas reais podem receber feedback.
      if (userQuestion !== null) {
      const feedbackBtn = document.createElement('button');
      feedbackBtn.className = 'btn btn-icon';
      feedbackBtn.innerHTML = '👍';
      feedbackBtn.setAttribute('aria-label', 'Avaliar resposta');
      feedbackBtn.addEventListener('click', () => this.showFeedbackModal(userQuestion, content));
      messageDiv.appendChild(feedbackBtn);
      }
    }

    return messageDiv;
  }

  showTypingIndicator() {
    if (this.typingIndicator) {
      this.typingIndicator.classList.add('show');
      this.scrollToBottom();
    }
  }

  hideTypingIndicator() {
    if (this.typingIndicator) {
      this.typingIndicator.classList.remove('show');
    }
  }

  showErrorMessage(message) {
    const errorMessage = this.createMessageElement(`⚠️ ${message}`, 'bot');
    errorMessage.style.borderColor = 'var(--error)';
    this.chatMessages?.appendChild(errorMessage);
  }

  updateUIState(processing) {
    if (this.sendBtn) {
      this.sendBtn.disabled = processing;
      this.sendBtn.textContent = processing ? 'Enviando...' : 'Enviar';
    }

    if (this.messageInput) {
      this.messageInput.disabled = processing;
      this.messageInput.placeholder = processing ?
        'Aguardando resposta...' : 'Digite sua mensagem...';
    }
  }

  scrollToBottom() {
    if (this.chatMessages) {
      this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
  }

  // Voice functionality
  async toggleVoiceRecording() {
    if (this.isRecording) {
      this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  async startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);
      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        this.audioChunks.push(event.data);
      };

      this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        await this.processAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      this.mediaRecorder.start();
      this.isRecording = true;
      this.voiceBtn?.classList.add('active');
      this.voiceBtn?.setAttribute('aria-label', 'Parar gravação');

    } catch (error) {
      console.error('Erro ao iniciar gravação:', error);
      this.showErrorMessage('Erro ao acessar microfone.');
    }
  }

  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      this.voiceBtn?.classList.remove('active');
      this.voiceBtn?.setAttribute('aria-label', 'Iniciar gravação de voz');
    }
  }

  async processAudio(audioBlob) {
    // This would integrate with speech-to-text API
    // For now, just show a message
    this.showErrorMessage('Funcionalidade de voz em desenvolvimento.');
  }

  // Modal functionality
  showModal(modalType) {
    const modal = this.modals[modalType];
    if (modal) {
      modal.classList.add('show');
      modal.setAttribute('aria-hidden', 'false');
    }
  }

  hideAllModals() {
    Object.values(this.modals).forEach(modal => {
      if (modal) {
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
      }
    });
  }

  showFeedbackModal(userQuestion, assistantResponse) {
    // Remove existing feedback modal
    const existingModal = document.getElementById('feedback-modal');
    if (existingModal) existingModal.remove();

    // Create feedback modal
    const modal = document.createElement('div');
    modal.id = 'feedback-modal';
    modal.className = 'modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-labelledby', 'feedback-title');
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2 id="feedback-title" class="modal-title">Avalie a resposta</h2>
          <button class="modal-close" aria-label="Fechar modal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Sua avaliação:</label>
            <div class="rating-stars" role="radiogroup" aria-label="Avaliação de estrelas">
              <button class="star" data-rating="1" aria-label="1 estrela">⭐</button>
              <button class="star" data-rating="2" aria-label="2 estrelas">⭐</button>
              <button class="star" data-rating="3" aria-label="3 estrelas">⭐</button>
              <button class="star" data-rating="4" aria-label="4 estrelas">⭐</button>
              <button class="star" data-rating="5" aria-label="5 estrelas">⭐</button>
            </div>
          </div>
          <div class="form-group">
            <label for="feedback-text" class="form-label">Comentário (opcional):</label>
            <textarea id="feedback-text" class="form-input form-textarea" placeholder="Conte-nos o que achou da resposta..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" onclick="jarvisInterface.hideAllModals()">Cancelar</button>
          <button id="submit-feedback" class="btn btn-primary" disabled>Enviar Feedback</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.modals.feedback = modal;

    // Bind feedback events
    this.bindFeedbackEvents(userQuestion, assistantResponse);

    // Show modal
    setTimeout(() => this.showModal('feedback'), 10);
  }

  bindFeedbackEvents(userQuestion, assistantResponse) {
    const modal = this.modals.feedback;
    if (!modal) return;

    let selectedRating = 0;
    const stars = modal.querySelectorAll('.star');
    const submitBtn = modal.querySelector('#submit-feedback');
    const closeBtn = modal.querySelector('.modal-close');

    // Star rating
    stars.forEach(star => {
      star.addEventListener('click', () => {
        selectedRating = parseInt(star.dataset.rating);
        stars.forEach(s => s.classList.remove('active'));
        for (let i = 0; i < selectedRating; i++) {
          stars[i].classList.add('active');
        }
        submitBtn.disabled = false;
      });
    });

    // Close modal
    closeBtn.addEventListener('click', () => this.hideAllModals());

    // Submit feedback
    submitBtn.addEventListener('click', async () => {
      if (selectedRating === 0) return;

      const feedbackText = modal.querySelector('#feedback-text').value;

      try {
        submitBtn.innerHTML = '<div class="loading-spinner"></div> Enviando...';
        submitBtn.disabled = true;

        const response = await this.authorizedFetch('/feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_id: this.currentSessionId,
            user_question: userQuestion,
            assistant_response: assistantResponse,
            rating: selectedRating,
            feedback_text: feedbackText,
            intent: '',
            model_used: '',
            response_time: 0
          })
        });

        if (response.ok) {
          this.showSuccessMessage('Obrigado pelo feedback! 👍');
          this.hideAllModals();
          this.updateStats();
        } else {
          throw new Error('Erro ao enviar feedback');
        }
      } catch (error) {
        console.error('Erro no feedback:', error);
        this.showErrorMessage('Erro ao enviar feedback. Tente novamente.');
      } finally {
        submitBtn.innerHTML = 'Enviar Feedback';
        submitBtn.disabled = false;
      }
    });
  }

  showSuccessMessage(message) {
    const successMessage = this.createMessageElement(`✅ ${message}`, 'bot');
    successMessage.style.borderColor = 'var(--success)';
    this.chatMessages?.appendChild(successMessage);
  }

  async updateStats() {
    try {
      const response = await this.authorizedFetch('/stats');
      if (response.ok) {
        const stats = await response.json();
        this.updateStatsModal(stats);
      }
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  }

  updateStatsModal(stats) {
    const statsContainer = document.getElementById('stats-container');
    if (!statsContainer) return;

    statsContainer.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">${stats.total_conversations || 0}</div>
          <div class="stat-label">Conversas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.total_feedbacks || 0}</div>
          <div class="stat-label">Feedbacks</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.average_rating ? stats.average_rating.toFixed(1) : '0.0'}</div>
          <div class="stat-label">Avaliação Média</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.total_memories || 0}</div>
          <div class="stat-label">Memórias salvas</div>
        </div>
      </div>
    `;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.jarvisInterface = new JarvisInterface();
});

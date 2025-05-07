document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.querySelector('.send-button');
    let chatHistory = [];
    let isSending = false;

    // 마크다운 설정
    marked.setOptions({
        renderer: new marked.Renderer(),
        highlight: function (code, language) {
            const validLanguage = hljs.getLanguage(language) ? language : 'plaintext';
            return hljs.highlight(validLanguage, code).value;
        },
        pedantic: false,
        gfm: true,
        breaks: true,
        sanitize: false,
        smartLists: true,
        smartypants: false,
        xhtml: false
    });

    // 메시지 추가 함수
    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        if (type === 'ai') {
            // AI 응답은 마크다운으로 렌더링
            const markdownContent = document.createElement('div');
            markdownContent.className = 'markdown-content';
            markdownContent.innerHTML = marked.parse(content);
            messageDiv.appendChild(markdownContent);

            // 코드 블록에 하이라이팅 적용
            messageDiv.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightBlock(block);
            });
        } else {
            // 사용자 메시지는 일반 텍스트로 표시
            messageDiv.textContent = content;
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 타이핑 인디케이터 추가
    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return indicator;
    }

    // 타이핑 인디케이터 제거
    function removeTypingIndicator(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }

    // 입력창/버튼 비활성화
    function setInputDisabled(disabled) {
        messageInput.disabled = disabled;
        sendButton.disabled = disabled;
    }

    // API 요청 함수
    async function sendMessage(message) {
        isSending = true;
        setInputDisabled(true);
        const typingIndicator = addTypingIndicator();

        try {
            const response = await fetch('/chat/conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    history: chatHistory
                })
            });

            const data = await response.json();

            if (data.success) {
                // AI 응답 추가 (마크다운으로 렌더링)
                addMessage(data.data.answer, 'ai');
                // 대화 내역 업데이트
                chatHistory.push({
                    human: message,
                    ai: data.data.answer
                });
            } else {
                // 에러 메시지 표시
                addMessage('죄송합니다. 오류가 발생했습니다.', 'system');
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('서버와의 통신 중 오류가 발생했습니다.', 'system');
        } finally {
            removeTypingIndicator(typingIndicator);
            setInputDisabled(false);
            isSending = false;
            messageInput.focus();
        }
    }

    // 폼 제출 이벤트 처리
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (isSending) return;
        const message = messageInput.value.trim();
        if (!message) return;
        // 사용자 메시지 추가
        addMessage(message, 'user');
        // 입력 필드 초기화
        messageInput.value = '';
        // API 요청
        await sendMessage(message);
    });

    // Enter 키로 메시지 전송 (Shift + Enter는 줄바꿈)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            // form의 submit 이벤트만 사용 (중복 트리거 방지)
            // e.preventDefault();
            // chatForm.requestSubmit();
        }
    });
}); 
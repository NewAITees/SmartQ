// アプリケーションの状態管理
const appState = {
    isLoading: false,
    isError: false,
    errorMessage: '',
    currentQuestion: null,
    selectedAnswer: null,
    feedback: null
};

// DOM要素の参照
const elements = {
    topicSelect: document.getElementById('topicSelect'),
    generateButton: document.getElementById('generateButton'),
    submitButton: document.getElementById('submitButton'),
    questionText: document.getElementById('questionText'),
    optionsContainer: document.getElementById('optionsContainer'),
    additionalAnswer: document.getElementById('additionalAnswer'),
    feedbackContainer: document.getElementById('feedbackContainer'),
    errorMessage: document.getElementById('errorMessage'),
    systemPrompt: document.getElementById('systemPrompt'),
    knowledgeInput: document.getElementById('knowledgeInput')
};

// 状態更新関数
const updateState = (newState) => {
    Object.assign(appState, newState);
    render();
};

// UI更新関数
const render = () => {
    // ローディング状態の更新
    elements.generateButton.disabled = appState.isLoading;
    elements.submitButton.disabled = appState.isLoading || !appState.currentQuestion;
    
    if (appState.isLoading) {
        elements.generateButton.classList.add('loading');
        elements.submitButton.classList.add('loading');
    } else {
        elements.generateButton.classList.remove('loading');
        elements.submitButton.classList.remove('loading');
    }

    // エラーメッセージの表示/非表示
    if (appState.isError) {
        elements.errorMessage.textContent = appState.errorMessage;
        elements.errorMessage.classList.add('visible');
    } else {
        elements.errorMessage.classList.remove('visible');
    }

    // 問題と選択肢の表示
    if (appState.currentQuestion) {
        elements.questionText.textContent = appState.currentQuestion.question;
        elements.optionsContainer.innerHTML = appState.currentQuestion.options
            .map((option, index) => `
                <label class="radio-option">
                    <input type="radio" name="answer" value="${index}" 
                           ${appState.selectedAnswer === index ? 'checked' : ''}>
                    ${option}
                </label>
            `).join('');
    } else {
        elements.questionText.textContent = '問題を生成してください';
        elements.optionsContainer.innerHTML = '';
    }

    // フィードバックの表示
    if (appState.feedback) {
        elements.feedbackContainer.innerHTML = `
            <div class="feedback ${appState.feedback.isCorrect ? 'correct' : 'incorrect'}">
                ${appState.feedback.message}
            </div>
        `;
    } else {
        elements.feedbackContainer.innerHTML = '';
    }
};

// API呼び出し関数
const callApi = async (endpoint, data) => {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        throw new Error(`Network error: ${error.message}`);
    }
};

// 問題生成ハンドラ
const handleGenerate = async () => {
    try {
        updateState({ isLoading: true, isError: false, currentQuestion: null, feedback: null });

        const data = {
            topic: elements.topicSelect.value,
            system_prompt: elements.systemPrompt.value,
            knowledge_base: elements.knowledgeInput.value
        };

        const result = await callApi('/api/generate', data);
        updateState({ 
            currentQuestion: result,
            selectedAnswer: null
        });
    } catch (error) {
        updateState({ 
            isError: true, 
            errorMessage: `問題の生成中にエラーが発生しました: ${error.message}`
        });
    } finally {
        updateState({ isLoading: false });
    }
};

// 回答送信ハンドラ
const handleSubmit = async () => {
    if (!appState.currentQuestion || appState.selectedAnswer === null) {
        updateState({
            isError: true,
            errorMessage: '回答を選択してください'
        });
        return;
    }

    try {
        updateState({ isLoading: true, isError: false });

        const data = {
            question_id: appState.currentQuestion.id,
            selected_answer: appState.selectedAnswer,
            additional_answer: elements.additionalAnswer.value
        };

        const result = await callApi('/api/evaluate', data);
        updateState({ feedback: result });
    } catch (error) {
        updateState({
            isError: true,
            errorMessage: `回答の評価中にエラーが発生しました: ${error.message}`
        });
    } finally {
        updateState({ isLoading: false });
    }
};

// イベントリスナーの設定
const setupEventListeners = () => {
    elements.generateButton.addEventListener('click', handleGenerate);
    elements.submitButton.addEventListener('click', handleSubmit);
    elements.optionsContainer.addEventListener('change', (event) => {
        if (event.target.type === 'radio') {
            updateState({ selectedAnswer: parseInt(event.target.value) });
        }
    });
};

// アプリケーションの初期化
const init = () => {
    setupEventListeners();
    render();
};

// アプリケーションの起動
document.addEventListener('DOMContentLoaded', init); 
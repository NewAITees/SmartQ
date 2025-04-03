// アプリケーションの状態管理
const appState = {
    isLoading: false,
    isError: false,
    errorMessage: '',
    currentQuestion: null,  // QuizQuestion型
    selectedOptions: [],    // 選択されたオプションのインデックス配列
    feedback: null          // FeedbackResponse型
};

// DOM要素の参照
const elements = {
    topicSelect: document.getElementById('topicSelect'),
    generateButton: document.getElementById('generateButton'),
    submitButton: document.getElementById('submitButton'),
    nextButton: document.getElementById('nextButton'),
    questionText: document.getElementById('questionText'),
    optionsContainer: document.getElementById('optionsContainer'),
    additionalAnswer: document.getElementById('additionalAnswer'),
    feedbackContainer: document.getElementById('feedbackContainer'),
    errorMessage: document.getElementById('errorMessage'),
    systemPrompt: document.getElementById('systemPrompt'),
    knowledgeInput: document.getElementById('knowledgeInput'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    initialMessage: document.getElementById('initialMessage')
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
    elements.submitButton.disabled = appState.isLoading || 
                                    !appState.currentQuestion || 
                                    appState.selectedOptions.length === 0;
    
    if (appState.isLoading) {
        elements.loadingSpinner.classList.add('visible');
        elements.generateButton.classList.add('loading');
        elements.submitButton.classList.add('loading');
    } else {
        elements.loadingSpinner.classList.remove('visible');
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

    // 次の問題ボタンの状態
    if (elements.nextButton) {
        elements.nextButton.style.display = appState.feedback ? 'block' : 'none';
    }

    // 初期メッセージの表示/非表示
    if (elements.initialMessage) {
        elements.initialMessage.style.display = appState.currentQuestion ? 'none' : 'block';
    }

    // 問題と選択肢の表示
    if (appState.currentQuestion) {
        elements.questionText.textContent = appState.currentQuestion.question;
        elements.optionsContainer.innerHTML = appState.currentQuestion.options
            .map((option, index) => {
                const inputType = option.type === 'checkbox' ? 'checkbox' : 'radio';
                const name = inputType === 'checkbox' ? `answer_${index}` : 'answer';
                
                return `
                    <label class="option-label ${inputType}">
                        <input type="${inputType}" name="${name}" value="${index}" 
                               ${appState.selectedOptions.includes(index) ? 'checked' : ''}>
                        ${option.text}
                    </label>
                `;
            }).join('');
    } else {
        elements.questionText.textContent = '問題を生成してください';
        elements.optionsContainer.innerHTML = '';
    }

    // フィードバック表示の修正
    if (appState.feedback) {
        elements.feedbackContainer.innerHTML = `
            <div class="feedback ${appState.feedback.isCorrect ? 'correct' : 'incorrect'}">
                <h3>${appState.feedback.isCorrect ? '正解です！' : '不正解です。'}</h3>
                <p>${appState.feedback.feedback}</p>
                <div class="detailed-explanation">
                    <h4>詳細解説:</h4>
                    <p>${appState.feedback.detailedExplanation}</p>
                </div>
                ${appState.feedback.additionalResources ? `
                    <div class="additional-resources">
                        <h4>追加リソース:</h4>
                        <ul>
                            ${appState.feedback.additionalResources.map(resource => `
                                <li><strong>${resource.title}</strong>: ${resource.description}</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
                <div class="explanation">
                    <h4>問題解説:</h4>
                    <p>${appState.currentQuestion.explanation}</p>
                </div>
            </div>
        `;
        elements.feedbackContainer.classList.add('visible');
    } else {
        elements.feedbackContainer.innerHTML = '';
        elements.feedbackContainer.classList.remove('visible');
    }
};

// API呼び出し関数
const callApi = async (endpoint, data) => {
    try {
        console.log(`API Request to ${endpoint}:`, data);
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const responseData = await response.json();
        console.log(`API Response from ${endpoint}:`, responseData);

        if (!response.ok) {
            throw new Error(responseData.detail || `API error: ${response.status}`);
        }

        return responseData;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw new Error(`Network error: ${error.message}`);
    }
};

// 問題生成ハンドラ
const handleGenerate = async () => {
    try {
        updateState({ 
            isLoading: true, 
            isError: false, 
            currentQuestion: null, 
            selectedOptions: [], 
            feedback: null 
        });

        const data = {
            topic: elements.topicSelect.value,
            system_prompt: elements.systemPrompt.value,
            knowledge_base: elements.knowledgeInput.value
        };

        const result = await callApi('/api/generate', data);
        updateState({ 
            currentQuestion: result,
            selectedOptions: []
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

// 選択肢の処理ハンドラ
const handleOptionSelect = (event) => {
    if (event.target.type === 'radio') {
        // ラジオボタンの場合は単一選択
        updateState({ selectedOptions: [parseInt(event.target.value, 10)] });
    } else if (event.target.type === 'checkbox') {
        // チェックボックスの場合は複数選択可能
        const value = parseInt(event.target.value, 10);
        let selectedOptions = [...appState.selectedOptions];
        
        if (event.target.checked) {
            // 選択追加
            if (!selectedOptions.includes(value)) {
                selectedOptions.push(value);
            }
        } else {
            // 選択解除
            selectedOptions = selectedOptions.filter(item => item !== value);
        }
        
        updateState({ selectedOptions });
    }
};

// 回答送信ハンドラ
const handleSubmit = async () => {
    if (!appState.currentQuestion || appState.selectedOptions.length === 0) {
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
            selected_options: appState.selectedOptions.map(index => ({
                index,
                text: appState.currentQuestion.options[index].text
            })),
            additional_answer: elements.additionalAnswer.value,
            question: appState.currentQuestion.question,
            options: appState.currentQuestion.options
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

// 次の問題ハンドラ
const handleNext = () => {
    updateState({
        currentQuestion: null,
        selectedOptions: [],
        feedback: null,
        isError: false
    });
    
    // フォーカスを問題生成ボタンに移動
    elements.generateButton.focus();
};

// イベントリスナーの設定
const setupEventListeners = () => {
    elements.generateButton.addEventListener('click', handleGenerate);
    elements.submitButton.addEventListener('click', handleSubmit);
    elements.optionsContainer.addEventListener('change', handleOptionSelect);
    if (elements.nextButton) {
        elements.nextButton.addEventListener('click', handleNext);
    }
};

// アプリケーションの初期化
const init = () => {
    setupEventListeners();
    render();
};

// アプリケーションの起動
document.addEventListener('DOMContentLoaded', init); 
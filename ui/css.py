custom_css = """
    /* ============================================
       MAIN CONTAINER
       ============================================ */
    .progress-text,
    .progress-text.svelte-1uj8rng,
    .meta-text.svelte-1uj8rng {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: #9ca3af !important;
        font-size: 12px !important;
        margin-bottom: 4px !important;
    }

    /* FIX: show progress text during upload — more specific selector overrides above */
    .progress-text.meta-text {
        display: block !important;
        visibility: visible !important;
        color: #1a1d27 !important;
        font-size: 12px !important;
    }
    
    .gradio-container { 
        max-width: 1000px !important;
        width: 100% !important;
        margin: 0 auto !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        background: #ffffff !important;
    }
    
    /* ============================================
       TABS
       ============================================ */
    button[role="tab"] {
        color: #9ca3af !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        transition: all 0.2s ease !important;
        background: transparent !important;
    }
    
    button[role="tab"]:hover {
        color: #1a1d27 !important;

    }
    
    /* Selected tab - */
    button[role="tab"][aria-selected="true"] {
        color: #4f6ef7 !important;
        border-bottom: 2px solid #4f6ef7 !important;
        border-radius: 0 !important;
        background: transparent !important;
    }
    
    .tabs {
        border-bottom: none !important;
        border-radius: 0 !important;
    }
    
    .tab-nav {
        border-bottom: none !important;
        border-radius: 0 !important;
    }
    
    button[role="tab"]::before,
    button[role="tab"]::after,
    .tabs::before,
    .tabs::after,
    .tab-nav::before,
    .tab-nav::after {
        display: none !important;
        content: none !important;
        border-radius: 0 !important;
    }
    
    #doc-management-tab {
        max-width: 500px !important;
        margin: 0 auto !important;
    }
    
    /* ============================================
       BUTTONS
       ============================================ */
    button {
        font-size: 13px !important
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        background: #ffffff !important;
        color: #6b7280 !important;
        border: 1px solid #d0d4de !important;
        border-radius: 10px !important;
    }

    button:hover {
        border-color: #4f6ef7 !important;
        color: #4f6ef7 !important;
    }
    
    /* Primary button - indigo */
    .primary {
        background: #4f6ef7 !important;
        color: white !important;
    }
    
    .primary:hover {
        background: #6b82f8 !important;
        transform: translateY(-1px) !important;
        color: #ffffff !important;
    }
    
    /* Stop/danger button */
    .stop {
        background: rgba(239, 68, 68, 0.06) !important;
        color: #ef4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
    }
    
    .stop:hover {
        background: rgba(239, 68, 68, 0.12) !important;
        border-color: #ef4444 !important;
        transform: translateY(-1px) !important;
        color: #ef4444 !important;
    }
    
    /* ============================================
       CHAT INPUT BOX - PRESERVED EXACTLY AS ORIGINAL
       ============================================ */
    textarea[placeholder="Type a message..."],
    textarea[data-testid*="textbox"]:not(#file-list-box textarea) {
        background: #eef0f4 !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    textarea[placeholder="Type a message..."]:focus {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .gr-text-input:has(textarea[placeholder="Type a message..."]),
    [class*="chatbot"] + * [data-testid="textbox"],
    form:has(textarea[placeholder="Type a message..."]) > div {
        background: transparent !important;
        border: none !important;
        gap: 12px !important;
    }
    
    form:has(textarea[placeholder="Type a message..."]) button,
    [class*="chatbot"] ~ * button[type="submit"] {
        background: transparent !important;
        border: none !important;
        padding: 8px !important;
    }
    
    /* Submit button hover - indigo tint */
    form:has(textarea[placeholder="Type a message..."]) button:hover {
        background: rgba(99, 102, 241, 0.1) !important;
    }
    
    form:has(textarea[placeholder="Type a message..."]) {
        gap: 12px !important;
        display: flex !important;
    }

     /* Fix white background on chat input wrapper */
    .stretch,
    footer,
    .chatbot ~ *,
    .gr-group,
    [data-testid="chatbot"] ~ div,
    .svelte-1ed2p3z,
    .input-container,
    .chatinterface,
    .chatinterface > div,
    .chatinterface .input-row,
    .chatinterface footer {
        background: #eef0f4 !important;
        border-color: #e2e4ea !important;
    }

    /* Fix the textarea itself inside ChatInterface */
    .chatinterface textarea,
    .chatinterface input,
    footer textarea,
    footer input,
    .input-row textarea {
        background: #eef0f4 !important;
        color: #1a1d27 !important;
        border: 1px solid #e2e4ea !important;
        border-radius: 10px !important;
    }

    /* Placeholder text color */
    .chatinterface textarea::placeholder,
    footer textarea::placeholder,
    .input-row textarea::placeholder {
        color: #6b7280 !important;
        opacity: 1 !important;
    }
    
    /* ============================================
       FILE UPLOAD
       ============================================ */
    .file-preview, 
    [data-testid="file-upload"] {
        background: #eef0f4 !important;
        border: 1px solid #e2e4ea !important;
        border-radius: 5px !important;
        color: #1a1d27 !important;
        min-height: 200px !important;
        padding: 15px 30px !important;
    }
    
    .file-preview:hover, 
    [data-testid="file-upload"]:hover {
        border-color: #e2e4ea !important;
        background: #eef0f4 !important;
    }
    
    .file-preview *,
    [data-testid="file-upload"] * {
        color: #1a1d27 !important;
    }
    
    .file-preview .label,
    [data-testid="file-upload"] .label {
        display: none !important;
    }
    
    /* ============================================
       INPUTS & TEXTAREAS
       ============================================ */
    input, 
    textarea {
        background: #eef0f4 !important;
        border: 1px solid #e2e4ea !important;
        border-radius: 10px !important;
        color: #1a1d27 !important;
        transition: border-color 0.2s ease !important;
    }
    
    input:focus, 
    textarea:focus {
        border-color: #4f6ef7 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }
    
    textarea[readonly] {
        background: #eef0f4 !important;
        color: #9ca3af !important;
    }
    
    /* ============================================
       FILE LIST BOX
       ============================================ */
    #file-list-box {
        background: #eef0f4 !important;
        border: 1px solid #e2e4ea !important;
        border-radius: 5px !important;
        padding: 10px !important;
    }
    
    #file-list-box textarea {
        background: #eef0f4 !important;
        border: none !important;
        color: #1a1d27 !important;
        padding: 0 !important;
    }
    
    /* ============================================
       CHATBOT
       ============================================ */

    .chatbot,
    .chatbot > div,
    [data-testid="chatbot"],
    [data-testid="chatbot"] > div,
    .bubble-wrap,
    .wrap.svelte-byatnx {
        background: #ffffff !important;
        border: none !important;
    }

    .message.bot,
    .message-bubble-border,
    [data-testid="bot"],
    .bot.svelte-1s78gfg,
    div.bot {
        background: #ffffff !important;
        color: #0d0d0d !important;
    }

    .message.bot *,
    [data-testid="bot"] *,
    div.bot * {
        color: #0d0d0d !important;
    }

    .message.user,
    [data-testid="user"],
    div.user {
        background: #ffffff !important;
        color: #0d0d0d !important;
    }

    .message.user *,
    [data-testid="user"] *,
    div.user * {
        color: #0d0d0d !important;
    }

    .placeholder-content,
    .chatbot .placeholder,
    [data-testid="chatbot"] .placeholder,
    .empty.svelte-1s78gfg,
    .wrap > .placeholder-content {
        color: #6b7280 !important;
        opacity: 1 !important;
    }

    .placeholder-content *,
    .chatbot .placeholder * {
        color: #6b7280 !important;
        fill: #6b7280 !important;
    }

    .chatbot .scroll-hide,
    .chatbot .overflow-y-auto,
    .generating {
        background: #ffffff !important;
    }

    .generating span,
    .thinking span,
    .loader {
        background: #e2e4ea !important;
        color: #1a1d27 !important;
    }

    /* ============================================
       LOADING DOTS
       ============================================ */
    .dots,
    .dots.svelte-stpvyx {
        display: flex !important;
        gap: 4px !important;
        align-items: center !important;
        padding: 4px 2px !important;
    }

    .dot,
    .dot.svelte-stpvyx {
        width: 8px !important;
        height: 8px !important;
        border-radius: 50% !important;
        background: #4f6ef7 !important;
        opacity: 0.8 !important;
        animation: dot-pulse 1.4s ease-in-out infinite !important;
    }

    .dot:nth-child(1) { animation-delay: 0s !important; }
    .dot:nth-child(2) { animation-delay: 0.2s !important; }
    .dot:nth-child(3) { animation-delay: 0.4s !important; }

    @keyframes dot-pulse {
        0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
        40%            { opacity: 1;   transform: scale(1);   }
    }

    .sr-only {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        overflow: hidden !important;
        clip: rect(0,0,0,0) !important;
        white-space: nowrap !important;
    }

    .message-content,
    .message-content.svelte-stpvyx {
        display: flex !important;
        align-items: center !important;
        min-height: 32px !important;
        min-width: 48px !important;
    }
    
    /* ============================================
       PROGRESS BAR
       FIX: Gradio 6.x uses scoped svelte classes
       ============================================ */
    .progress-bar-wrap {
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #e2e4ea !important;
    }

    /* Progress level — contains label text */
    .progress-level,
    .progress-level.svelte-1uj8rng {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        overflow: visible !important;
        height: auto !important;
        background: transparent !important;
    }

    /* Progress description label */
    .progress-level-inner,
    .progress-level-inner.svelte-1uj8rng {
        display: block !important;
        visibility: visible !important;
        color: #1a1d27 !important;
        font-size: 14px !important;
        height: auto !important;
        background: transparent !important;
        margin-bottom: 6px !important;
        overflow: visible !important;
    }

    /* Progress bar track */
    .progress-bar-wrap,
    .progress-bar-wrap.svelte-1uj8rng,
    [data-testid="linear-progress"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #374151 !important;
        height: 6px !important;
        width: 100% !important;
    }

    .progress-bar,
    .progress-bar.svelte-1uj8rng,
    .progress-level-inner > div,
    [data-testid="linear-progress"] > div {
        background: #4f6ef7 !important;
        border-radius: 10px !important;
        height: 4px !important;
        min-width: 4px !important;
        transition: width 0.3s ease !important;
        display: block !important;
        visibility: visible !important;
    }

    .generating .progress-bar-wrap,
    .pending .progress-bar-wrap,
    .generating .progress-bar-wrap.svelte-1uj8rng {
        display: block !important;
        visibility: visible !important;
    }
    
    /* ============================================
       TYPOGRAPHY
       ============================================ */
    h1, h2, h3, h4, h5, h6 {
        color: #1a1d27 !important;
    }

    .gradio-container .prose p,
    .gradio-container p {
        color: #1a1d27 !important;
    }
    
    /* ============================================
       GLOBAL OVERRIDES
       ============================================ */
    * {
        box-shadow: none !important;
    }
    
    footer {
        visibility: hidden;
    }
"""
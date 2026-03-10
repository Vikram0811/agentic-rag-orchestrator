custom_css = """
    /* ============================================
       MAIN CONTAINER
       ============================================ */
    .progress-text { 
        display: none !important;
    }
    
    .gradio-container { 
        max-width: 1000px !important;
        width: 100% !important;
        margin: 0 auto !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        background: #0f0f0f !important;
    }
    
    /* ============================================
       TABS
       ============================================ */
    button[role="tab"] {
        color: #a3a3a3 !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        transition: all 0.2s ease !important;
        background: transparent !important;
    }
    
    button[role="tab"]:hover {
        color: #e5e5e5 !important;
    }
    
    /* Selected tab - orange text and orange underline */
    button[role="tab"][aria-selected="true"] {
        color: #D94F00 !important;
        border-bottom: 2px solid #D94F00 !important;
        border-radius: 0 !important;
        background: transparent !important;
    }
    
    .tabs {
        border-bottom: none !important;
        border-radius: 0 !important;
    }
    
    .tab-nav {
        border-bottom: 1px solid #3f3f3f !important;
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
        border-radius: 8px !important;
        border: none !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    
    /* Primary button - orange */
    .primary {
        background: #D94F00 !important;
        color: white !important;
    }
    
    .primary:hover {
        background: #B84200 !important;
        transform: translateY(-1px) !important;
    }
    
    /* Stop/danger button */
    .stop {
        background: #ef4444 !important;
        color: white !important;
    }
    
    .stop:hover {
        background: #dc2626 !important;
        transform: translateY(-1px) !important;
    }
    
    /* ============================================
       CHAT INPUT BOX - PRESERVED EXACTLY AS ORIGINAL
       ============================================ */
    textarea[placeholder="Type a message..."],
    textarea[data-testid*="textbox"]:not(#file-list-box textarea) {
        background: transparent !important;
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
    
    /* Submit button hover - orange tint */
    form:has(textarea[placeholder="Type a message..."]) button:hover {
        background: rgba(217, 79, 0, 0.1) !important;
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
        background: #1a1a1a !important;
        border-color: #3f3f3f !important;
    }

    /* Fix the textarea itself inside ChatInterface */
    .chatinterface textarea,
    .chatinterface input,
    footer textarea,
    footer input,
    .input-row textarea {
        background: #1a1a1a !important;
        color: #e5e5e5 !important;
        border: 1px solid #3f3f3f !important;
        border-radius: 10px !important;
    }

    /* Placeholder text color */
    .chatinterface textarea::placeholder,
    footer textarea::placeholder,
    .input-row textarea::placeholder {
        color: #6b6b6b !important;
        opacity: 1 !important;
    }
    
    /* ============================================
       FILE UPLOAD
       ============================================ */
    .file-preview, 
    [data-testid="file-upload"] {
        background: #1a1a1a !important;
        border: 1px solid #3f3f3f !important;
        border-radius: 5px !important;
        color: #ffffff !important;
        min-height: 200px !important;
    }
    
    .file-preview:hover, 
    [data-testid="file-upload"]:hover {
        border-color: #D94F00 !important;
        background: #1f1f1f !important;
    }
    
    .file-preview *,
    [data-testid="file-upload"] * {
        color: #ffffff !important;
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
        background: #1a1a1a !important;
        border: 1px solid #3f3f3f !important;
        border-radius: 10px !important;
        color: #e5e5e5 !important;
        transition: border-color 0.2s ease !important;
    }
    
    input:focus, 
    textarea:focus {
        border-color: #D94F00 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(217, 79, 0, 0.1) !important;
    }
    
    textarea[readonly] {
        background: #1a1a1a !important;
        color: #a3a3a3 !important;
    }
    
    /* ============================================
       FILE LIST BOX
       ============================================ */
    #file-list-box {
        background: #1a1a1a !important;
        border: 1px solid #3f3f3f !important;
        border-radius: 5px !important;
        padding: 10px !important;
    }
    
    #file-list-box textarea {
        background: transparent !important;
        border: none !important;
        color: #e5e5e5 !important;
        padding: 0 !important;
    }
    
    /* ============================================
       CHATBOT - FIXED SELECTORS FOR GRADIO 4.x
       ============================================ */

    /* Fix 1: Chatbot container background — prevents white flash */
    .chatbot,
    .chatbot > div,
    [data-testid="chatbot"],
    [data-testid="chatbot"] > div,
    .bubble-wrap,
    .wrap.svelte-byatnx {
        background: #1a1a1a !important;
        border: none !important;
    }

    /* Fix 2: Bot message bubble — Gradio 4.x uses different class names */
    .message.bot,
    .message-bubble-border,
    [data-testid="bot"],
    .bot.svelte-1s78gfg,
    div.bot {
        background: #1f1f1f !important;
        color: #e5e5e5 !important;
        border: 1px solid #3f3f3f !important;
    }

    /* Fix 3: All text inside bot bubble */
    .message.bot *,
    [data-testid="bot"] *,
    div.bot * {
        color: #e5e5e5 !important;
    }

    /* Fix 4: User message bubble */
    .message.user,
    [data-testid="user"],
    div.user {
        background: #D94F00 !important;
        color: #ffffff !important;
    }

    .message.user *,
    [data-testid="user"] *,
    div.user * {
        color: #ffffff !important;
    }

    /* Fix 5: Placeholder text visibility */
    .placeholder-content,
    .chatbot .placeholder,
    [data-testid="chatbot"] .placeholder,
    .empty.svelte-1s78gfg,
    .wrap > .placeholder-content {
        color: #a3a3a3 !important;
        opacity: 1 !important;
    }

    .placeholder-content *,
    .chatbot .placeholder * {
        color: #a3a3a3 !important;
        fill: #a3a3a3 !important;
    }

    /* Fix 6: Entire chatbot scroll area background */
    .chatbot .scroll-hide,
    .chatbot .overflow-y-auto,
    .generating {
        background: #1a1a1a !important;
    }

    /* Fix 7: Loader/thinking indicator visibility */
    .generating span,
    .thinking span,
    .loader {
        background: #3f3f3f !important;
        color: #e5e5e5 !important;
    }

    /* ============================================
       LOADING DOTS - BOT THINKING INDICATOR
       ============================================ */

    /* Dot container */
    .dots,
    .dots.svelte-stpvyx {
        display: flex !important;
        gap: 4px !important;
        align-items: center !important;
        padding: 4px 2px !important;
    }

    /* Individual dots - make them visible on dark background */
    .dot,
    .dot.svelte-stpvyx {
        width: 8px !important;
        height: 8px !important;
        border-radius: 50% !important;
        background: #D94F00 !important;
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

    /* Hide the sr-only "Loading content" text visually */
    .sr-only {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        overflow: hidden !important;
        clip: rect(0,0,0,0) !important;
        white-space: nowrap !important;
    }

    /* Bot bubble that contains the loader */
    .message-content,
    .message-content.svelte-stpvyx {
        display: flex !important;
        align-items: center !important;
        min-height: 32px !important;
        min-width: 48px !important;
    }
    
    /* ============================================
       PROGRESS BAR
       ============================================ */
    .progress-bar-wrap {
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #1a1a1a !important;
    }

    /* Progress bar fill - orange */
    .progress-bar {
        border-radius: 10px !important;
        background: #D94F00 !important;
    }

    /* Gradio 4.x hides progress differently */
    .progress-bar-wrap,
    .progress-level,
    .progress-level-inner,
    [data-testid="linear-progress"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #3f3f3f !important;
        height: 4px !important;
    }

    .progress-bar,
    .progress-level-inner > div,
    [data-testid="linear-progress"] > div {
        background: #D94F00 !important;
        border-radius: 10px !important;
        height: 4px !important;
        transition: width 0.3s ease !important;
    }

    /* Ensure progress container itself is not hidden */
    .generating .progress-bar-wrap,
    .pending .progress-bar-wrap {
        display: block !important;
        visibility: visible !important;
    }
    
    /* ============================================
       TYPOGRAPHY
       ============================================ */
    h1, h2, h3, h4, h5, h6 {
        color: #e5e5e5 !important;
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
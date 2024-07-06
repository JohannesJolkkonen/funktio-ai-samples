app_ui_css = """
.value-box-center {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}

@keyframes loading {
    0%, 80%, 100% {
        transform: scale(0);
    }
    40% {
        transform: scale(1.0);
    }
}

.loading-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: #333;
    margin-left: 5px;
    animation: loading 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
    animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
    animation-delay: -0.16s;
}
"""

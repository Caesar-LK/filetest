document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generateBtn');
    const feedback = document.getElementById('feedback');

    generateBtn.addEventListener('click', async () => {
        // 获取输入值
        const fileSize = document.getElementById('fileSize').value;
        const sizeUnit = document.getElementById('sizeUnit').value;
        const fileFormat = document.getElementById('fileFormat').value;
        const fileCount = document.getElementById('fileCount').value;

        // 输入验证
        if (!fileSize || !fileCount) {
            showFeedback('请填写所有必填字段', 'error');
            return;
        }

        if (fileSize <= 0 || fileCount <= 0) {
            showFeedback('文件大小和数量必须大于0', 'error');
            return;
        }

        // 显示加载状态
        generateBtn.disabled = true;
        generateBtn.textContent = '生成中...';
        showFeedback('文件生成中，请稍候...', 'info');

        try {
            // 发送请求到后端
            const response = await fetch('http://localhost:5001/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    fileSize,
                    sizeUnit,
                    fileFormat,
                    fileCount
                })
            });

            const data = await response.json();
            console.log('Server response:', data);

            if (response.ok) {
                showFeedback(`成功生成 ${fileCount} 个文件！`, 'success');
            } else {
                showFeedback(data.message || '生成失败，请重试', 'error');
            }
        } catch (error) {
            console.error('Error details:', error);
            showFeedback('服务器错误，请稍后重试: ' + error.message, 'error');
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = '生成文件';
        }
    });

    function showFeedback(message, type) {
        feedback.textContent = message;
        feedback.className = 'feedback ' + type;
    }
}); 
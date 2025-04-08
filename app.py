from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import random
import string
import traceback
from PIL import Image
import io
import cv2
import numpy as np

app = Flask(__name__, static_folder='.')
CORS(app)

# 添加路由来服务前端文件
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

def create_random_file(size_bytes, file_format, file_index):
    """创建指定大小和格式的随机文件"""
    # 将文件格式转换为小写以统一处理
    file_format = file_format.lower()
    
    # 处理视频格式的特殊情况
    if file_format in ['mp4', 'avi', 'mov', 'flv', 'wmv']:
        try:
            # 创建视频文件
            width = 640
            height = 480
            fps = 30
            duration = 5  # 5秒视频
            
            # 根据格式选择编码器
            fourcc = {
                'mp4': cv2.VideoWriter_fourcc(*'mp4v'),
                'avi': cv2.VideoWriter_fourcc(*'XVID'),
                'mov': cv2.VideoWriter_fourcc(*'mp4v'),
                'flv': cv2.VideoWriter_fourcc(*'FLV1'),
                'wmv': cv2.VideoWriter_fourcc(*'WMV2')
            }[file_format]
            
            filename = f"generated_file_{file_index}.{file_format}"
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(current_dir, 'generated_files')
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, filename)
            
            # 创建视频写入器
            out = cv2.VideoWriter(file_path, fourcc, fps, (width, height))
            
            # 生成随机颜色的帧
            for _ in range(fps * duration):
                frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
                out.write(frame)
            
            out.release()
            
            # 检查文件大小并调整
            current_size = os.path.getsize(file_path)
            if current_size < size_bytes:
                # 如果文件太小，添加随机数据
                with open(file_path, 'ab') as f:
                    f.write(os.urandom(size_bytes - current_size))
            elif current_size > size_bytes:
                # 如果文件太大，截取需要的部分
                with open(file_path, 'r+b') as f:
                    f.truncate(size_bytes)
            
            return True, filename
        except Exception as e:
            print(f"Error creating video file: {str(e)}")
            return False, str(e)
    
    # 处理图片格式的特殊情况
    elif file_format in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        # 对于图片格式，我们需要创建有效的图片文件
        # 创建一个随机颜色的图片
        width = 800
        height = 600
        image = Image.new('RGB', (width, height), color=(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        ))
        
        # 将图片保存到内存中
        img_byte_arr = io.BytesIO()
        # 处理 JPG 格式的特殊情况
        save_format = 'JPEG' if file_format in ['jpg', 'jpeg'] else file_format.upper()
        image.save(img_byte_arr, format=save_format)
        img_byte_arr = img_byte_arr.getvalue()
        
        # 如果生成的图片小于要求的大小，我们需要填充额外的随机数据
        if len(img_byte_arr) < size_bytes:
            remaining_bytes = size_bytes - len(img_byte_arr)
            extra_data = os.urandom(remaining_bytes)
            img_byte_arr = img_byte_arr + extra_data
        elif len(img_byte_arr) > size_bytes:
            # 如果生成的图片大于要求的大小，我们只取需要的部分
            img_byte_arr = img_byte_arr[:size_bytes]
            
        filename = f"generated_file_{file_index}.{file_format}"
    else:
        # 对于非图片格式，使用原来的方法
        filename = f"generated_file_{file_index}.{file_format}"
        img_byte_arr = None
    
    try:
        # 使用绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, 'generated_files')
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, filename)
        
        with open(file_path, 'wb') as f:
            if img_byte_arr:
                # 如果是图片格式，直接写入生成的图片数据
                f.write(img_byte_arr)
            else:
                # 对于非图片格式，使用原来的方法
                chunk_size = 1024 * 1024
                remaining_bytes = size_bytes
                
                while remaining_bytes > 0:
                    current_chunk_size = min(chunk_size, remaining_bytes)
                    data = os.urandom(current_chunk_size)
                    f.write(data)
                    remaining_bytes -= current_chunk_size
                
        return True, filename
    except Exception as e:
        print(f"Error creating file: {str(e)}")
        return False, str(e)

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def generate_files():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        print("Received request data:", request.get_data())
        data = request.json
        print("Parsed JSON data:", data)
        
        if not data:
            return jsonify({'message': '没有收到有效的JSON数据'}), 400
        
        # 获取参数并验证
        required_fields = ['fileSize', 'sizeUnit', 'fileFormat', 'fileCount']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'缺少必要的字段: {field}'}), 400
        
        try:
            file_size = int(data['fileSize'])
            file_count = int(data['fileCount'])
            print(f"Processing request: size={file_size}{data['sizeUnit']}, format={data['fileFormat']}, count={file_count}")
        except ValueError as ve:
            print(f"Value error: {str(ve)}")
            return jsonify({'message': '文件大小或数量必须是有效的数字'}), 400
        
        size_unit = data['sizeUnit']
        file_format = data['fileFormat']
        
        # 验证单位
        unit_multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        
        if size_unit not in unit_multipliers:
            return jsonify({'message': '无效的大小单位'}), 400
        
        # 计算字节大小
        size_bytes = file_size * unit_multipliers[size_unit]
        
        # 添加大小限制
        max_size = 1024 * 1024 * 1024  # 1GB
        if size_bytes > max_size:
            return jsonify({'message': '文件大小超过限制(最大1GB)'}), 400
        
        if file_count > 10:  # 限制文件数量
            return jsonify({'message': '文件数量超过限制(最大10个)'}), 400
        
        # 生成文件
        generated_files = []
        for i in range(file_count):
            success, result = create_random_file(size_bytes, file_format, i+1)
            if not success:
                return jsonify({'message': f'生成文件失败: {result}'}), 500
            generated_files.append(result)
        
        return jsonify({
            'message': f'成功生成 {file_count} 个文件',
            'files': generated_files
        })
        
    except Exception as e:
        print(f"Server error: {str(e)}")
        print("Traceback:", traceback.format_exc())
        return jsonify({'message': f'服务器错误: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='localhost') 
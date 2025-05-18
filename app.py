import os
from flask import Flask, request, render_template, jsonify, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads' 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# OCR 결과 저장용 
ocr_results = {} 

@app.route('/', methods=["GET", "POST"])
def main():
    return render_template('main.html', image_url=None)

@app.route('/upload_image', methods=["POST"])
def upload_image():
    if 'image' not in request.files:
         return jsonify({'error': '이미지 파일이 없습니다.'}), 400
    
    file = request.files['image']

    if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            image_url = url_for('static', filename=f'uploads/{filename}')
            return jsonify({'image_url': image_url})

@app.route('/send_ocr_result', methods=["POST"])
def send_ocr_result():
     data = request.get_json()
     text = data.get('text', '')
     # 임시 저장 (유저별로 관리하려면 세션 등을 추가 사용)
     ocr_results['text'] = text
     return jsonify({'status': 'success'})

@app.route('/ocr_result')
def ocr_result():
     text = ocr_results.get('text', '변환된 텍스트가 없습니다.')
     return render_template('ocr_result.html', ocr_text=text)

# @app.route("/all_sentences.json")
# def data():
#      return send_from_directory("static", "all_sentences.json")

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
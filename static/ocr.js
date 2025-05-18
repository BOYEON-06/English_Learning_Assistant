// 이미지 파일 처리하기
async function loadFile(input) {

    const file = input.files[0];
    const fileName = document.getElementById('fileName');
    fileName.textContent = file.name;

    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch('/upload_image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            console.log("업로드 성공!")

            // 이미지 미리보기
            const previewImage = document.createElement("img");
            previewImage.src = data.image_url;
            previewImage.style.maxWidth = "70%";
            previewImage.id = "preview-image";
            const container = document.getElementById('image-show');
            container.innerHTML = ""; // 기존 이미지 제거
            container.appendChild(previewImage);

        } else {
            alert('업로드 실패: ' + data.error);
        }
     } catch (error) {
        alert('업로드 중 오류 발생: ' + error.message);
     }

    

    // // 이미지 미리보기
    // const previewImage = document.createElement("img");
    // previewImage.src = URL.createObjectURL(file);
    // previewImage.style.maxWidth = "50%";
    // previewImage.id = "preview-image";

    // const container = document.getElementById('image-show');
    // container.innerHTML = ""; // 기존 이미지 제거
    // container.appendChild(previewImage);
}

// OCR 실행
document.getElementById('submitButton').addEventListener('click', async () => {
    const image = document.getElementById('preview-image');
    if (!image) return alert("이미지를 먼저 업로드해주세요.");

    image.style.visibility = 'visible';

    const resultContainer = document.createElement("div");
    resultContainer.style.marginTop = "20px";
    resultContainer.textContent = "변환 중...";

    const container = document.getElementById('image-show');
    container.appendChild(resultContainer);

    try {
        const result = await Tesseract.recognize(
            image.src, // 이미지 소스
            'eng',     
            {
                logger: m => {
                    console.log(m);
                }
            }
        );
        console.log(result.data.text);
        resultContainer.textContent = "성공적으로 변환되었습니다."

        // OCR 결과 서버에 보내기 
        await fetch('/send_ocr_result', {
            method: 'POST',
            headers: {'Content-Type' : 'application/json'},
            body: JSON.stringify({text: result.data.text})
        });

        // ocr_result.html로 이동 
        window.location.href = '/ocr_result';
        
    } catch (err) {
        resultContainer.textContent = "변환을 실패하였습니다. 오류 메세지: " + err.message;
    }
});

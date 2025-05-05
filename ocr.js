// 이미지 파일 처리하기
function loadFile(input) {
    const file = input.files[0];
    const fileName = document.getElementById('fileName');
    fileName.textContent = file.name;

    // 이미지 미리보기
    const previewImage = document.createElement("img");
    previewImage.src = URL.createObjectURL(file);
    previewImage.style.maxWidth = "50%";
    previewImage.style.visibility = "hidden";
    previewImage.id = "preview-image";

    const container = document.getElementById('image-show');
    container.innerHTML = ""; // 기존 이미지 제거
    container.appendChild(previewImage);
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
    } catch (err) {
        resultContainer.textContent = "변환을 실패하였습니다. 오류 메세지: " + err.message;
    }
});

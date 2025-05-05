const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

const server = http.createServer((req, res) => {
    if (req.url === '/' && req.method === 'GET') {
        const filePath = path.join(__dirname, 'main.html');

        fs.readFile(filePath, 'utf8', (err, data) => {
            if (err) {
                res.writeHead(500, { 'Content-Type' : 'text/plain'});
                res.end('서버 오류: HTML 파일을 읽을 수 없습니다.');
            } else {
                res.writeHead(200, { 'Content-Type' : 'text/html'});
                res.end(data);
            }
        }); 
    } else {
        // 404 처리 
        res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('404 Not Found');
  }
});

server.listen(PORT, () => {
  console.log(`서버 실행 중 입니다. : http://localhost:${PORT}`);
});

# main.py

import http.server
import socketserver
import cgi

PORT = 8000


class FileUploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve the HTML form for file upload
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'''
            <html>
            <head><title>File Upload</title></head>
            <body>
            <h2>Upload a File</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
            </form>
            </body>
            </html>
        ''')

    def do_POST(self):
        content_type, _ = cgi.parse_header(self.headers.get('content-type'))
        if content_type == 'multipart/form-data':
            form_data = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            uploaded_file = form_data['file']
            with open(uploaded_file.filename, 'wb') as f:
                f.write(uploaded_file.file.read())
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'File uploaded successfully')


def main():
    print(f"Server running at http://localhost:{PORT}/")

    # Start the HTTP server with our custom request handler
    with socketserver.TCPServer(("", PORT), FileUploadHandler) as httpd:
        httpd.serve_forever()


if __name__ == '__main__':
    main()

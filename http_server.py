import mimetypes
import os
import socket
import sys
import traceback

def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    response = [b"HTTP/1.1 200 OK",
                b"Content-Type: " + mimetype,
                b"",
                body]

    return b"\r\n".join(response)

def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""

    return b"HTTP/1.1 405 Method Not Allowed\r\n"


def response_not_found():
    """Returns a 404 Not Found response"""

    return b"HTTP/1.1 404 Not Found\r\n"


def parse_request(request):
    """
    Given the content of an HTTP request, returns the path of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """
    requested = request.split(' ')
    request_method = requested[0]

    if request_method == "POST":
        raise NotImplementedError()

    return requested[1]

def response_path(path):
    """
    This method should return appropriate content and a mime type.

    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the path is a file, it should return the contents of that file
    and its correct mimetype.

    If the path does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """

    current_dir = os.path.dirname(os.path.realpath(__file__))
    query = os.path.join(current_dir, "webroot", path[1:])

    if not os.path.exists(query):
        raise NameError(f"{path} not found.")
    
    content = b"not implemented"
    mime_type = b"not implemented"

    if os.path.isdir(query):
        mime_type = b"text/plain"
        dir_info = "\r\n".join(os.listdir(query))
        content = dir_info.encode()
    else:
        mime_type = mimetypes.guess_type(query)[0].encode()
        with open(query, "rb") as read_file:
            content = read_file.read()

    return content, mime_type

def handle_request(request):
    print("Request received:\n{}\n\n".format(request))

    path = parse_request(request)

    try:
        content, mime_type = response_path(path)
        response = response_ok(content, mime_type)
    except NameError:
        response = response_not_found()
    except NotImplementedError:
        response = response_method_not_allowed()

    return response

def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    # During debugging it appeared as though sometimes the
                    # browser would send an empty request or the
                    # conn.recv(1024) would somehow not get any request data
                    # and the connection would stay open and get stuck in this
                    # while loop trying to recieve data that never came.
                    # This will check if the length of the data is 0 and break
                    # the loop and let the next request resolve.
                    # 
                    # This bug reproduced on Windows 10 Pro x64 in both:
                    # Google Chrome Version 80.0.3987.149 (Official Build) (64-bit)
                    # Microsoft Edge Version 80.0.361.66 (Official build) (64-bit)
                    if '\r\n\r\n' in request or len(data) == 0:
                        break

                # To address the issue above, check to see if the request is
                # not empty.  If its not, handle the request as normal (logic
                # extract to handle_request()), otherwise print that an empty
                # request occured and allow the connection to close.
                if len(request) > 0:
                    response = handle_request(request)
                    conn.sendall(response)
                else:
                    print('An empty request was recieved.', file=log_buffer)

            except:
                traceback.print_exc()
            finally:
                print("Closing {0}:{1}".format(*addr), file=log_buffer)
                conn.close() 

    except KeyboardInterrupt:
        sock.close()
        return
    except:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)



# -*- coding: cp1252 -*-
import socket
import thread
import select

from HTTPRequest import *


__version__ = '0.1.0 Draft 1'
BUFLEN = 8192
VERSION = 'Python Proxy/' + __version__
HTTPVER = 'HTTP/1.1'


def p(obj, direction=''):
    msg = direction

    if isinstance(obj, HTTPRequest):
        msg += '%s %s %s\n' % (obj.method, obj.url, obj.protocol)

    if isinstance(obj, dict):
        msg += '{\n'
        for k, v in obj.iteritems():
            msg += (k + ' ' * 30)[:30] + ': '
            if k == 'Content-Length':
                size = float(v)
                if size < 1024:
                    msg += '%s (%.0f bytes)\n' % (repr(v), size)
                elif size < 1024 * 1024:
                    msg += '%s (%.0f kB)\n' % (repr(v), round(size / 1024, 0))
                else:
                    msg += '%s (%.0f MB)\n' % (repr(v), round(size / 1024 / 1024, 0))
            else:
                msg += '%s\n' % (repr(v), )
        msg += '}\n'
    elif obj is None:
        msg += 'None\n'
    else:
        msg += '2 %s\n' % (repr(obj), )

    print msg


class ConnectionHandler(object):
    def __init__(self, connection, timeout):
        self.client = connection
        self.timeout = timeout

        self.request = self.get_request()
        self.request_client = ''

        if self.request is not None:
            self.request = self.handle_request(self.request)

            if self.request is not None:
                # redirect
                if '&u=http://' in self.request.url:
                    i = self.request.url.find('&u=http://')
                    self._redirect(self.request.url[i + 3:])
                elif '&url=http://' in self.request.url:
                    i = self.request.url.find('&url=http://')
                    self._redirect(self.request.url[i + 5:])
                else:
                    # p(self.request)

                    if self.request.method == 'CONNECT':
                        self.method_connect()
                    elif self.request.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE'):
                        self.method_others()

        self.client.close()
        exit()

    @staticmethod
    def handle_request(request):
        # blacklist
        if request['User-Agent'].startswith('DropboxDesktopClient') or request['Host'] == 'd.dropbox.com':
            return None
        elif request.url.endswith('favicon.ico'):
            return None
        else:
            # modify request
            if request['User-Agent'].startswith('Mozilla/5.0'):
                request['User-Agent'] = 'Mozilla/5.0'

            return request

    def get_request(self):
        recv_buffer = ''
        while 1:
            recv_buffer += self.client.recv(BUFLEN)

            if len(recv_buffer) == 0:
                return None
            elif recv_buffer.find('\n') != -1:
                self.request_client = recv_buffer
                return HTTPRequest(recv_buffer)

    def method_connect(self):
        self.send_client('%s 200 Connection established\nProxy-agent: %s\n\n' % (HTTPVER, VERSION))
        self.send_target()

    def method_others(self):
        self.send_target(self.request)

    def _redirect(self, url):
        self.send_client('%s 301 Content redirected\nLocation: %s\n\n' % (HTTPVER, url))

    def send_client(self, msg):
        print "<" + msg
        self.client.send(msg)

    def send_target(self, request=None):
        (soc_family, _, _, _, address) = socket.getaddrinfo(self.request.host, self.request.port)[0]
        target = socket.socket(soc_family)
        target.connect(address)
        if request is not None:
            # print ">" + msg
            p(request, ">")
            target.send(str(request))
        self._read_write(target)
        try:
            target.shutdown(socket.SHUT_RDWR)
        except:
            pass
        target.close()

    def _read_write(self, target):
        time_out_max = self.timeout / 3
        socs = [self.client, target]
        count = 0
        while 1:
            count += 1
            (recv, _, error) = select.select(socs, [], socs, 3)
            if error:
                break
            if recv:
                for in_ in recv:
                    data = in_.recv(BUFLEN)
                    if in_ is self.client:
                        if data.startswith('POST') or data.startswith('GET'):
                            request = HTTPRequest(data)
                            request = self.handle_request(request)
                            if request is None:
                                data = ''
                            else:
                                data = str(request)
                            p(request, ">>")
                        out = target
                    else:
                        if data.startswith('HTTP'):
                            p(HTTPRequest(data), "<<")
                        out = self.client
                    if data:
                        out.send(data)
                        count = 0
            if count == time_out_max:
                break


def start_server(host='localhost', port=8080, ipv6=False, timeout=60):
    if ipv6:
        soc_type = socket.AF_INET6
    else:
        soc_type = socket.AF_INET
    soc = socket.socket(soc_type)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    soc.bind((host, port))
    print "Serving on %s:%d." % (host, port)  # debug
    soc.listen(0)
    while 1:
        try:
            conn, address = soc.accept()
            thread.start_new_thread(ConnectionHandler, (conn, timeout))
        except KeyboardInterrupt:
            soc.close()


if __name__ == '__main__':
    start_server()

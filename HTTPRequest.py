# -*- coding: cp1252 -*-
import urllib

class HTTPRequest(dict):
    def __init__(self, data):
        
        parts = data.split('\r\n\r\n')
        header_lines = parts[0].split('\r\n')
        
        if len(parts) > 1:
            self.data = parts[1]
        else:
            self.data = ''
        
        first_line = header_lines[0].split(' ', 2)
        self.method = first_line[0]
        self.url = urllib.unquote(first_line[1])
        self.protocol = first_line[2]
        self._order_ = []
        
        for line in header_lines[1:]:
            x = line.find(':')
            key = line[:x]
            value = line[x+1:].strip()
            
            if len(key) > 0:
                self._order_.append(key)
                self[key] = value
    
    def __setattr__(self, key, value):
        self.__dict__[key] = value

        if key == 'url':
            path = self.url[7:]
            i = path.find('/')
            self.host = path[:i]
            self.path = path[i:]

            i = self.host.find(':')
            if i!=-1:
                self.port = int(self.host[i+1:])
                self.host = self.host[:i]
            else:
                self.port = 80
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except:
            return ''
    
    def __repr__(self):
        return '<HTTP ' + self.method + ' ' + self.url + '>'
    
    def __str__(self):
        ret = self.method + ' ' + self.path + ' ' + self.protocol + '\r\n'
        
        for k in self._order_:
            ret += k + ': ' + self[k] + '\r\n'
        
        ret += '\r\n'
        ret += self.data
        return ret
class SoapController(object):
    def soap_header(self, url):
        """
        Soap header tag
        :param url: namespace url
        :return:
        """
        return f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:v1="{url}">
                <soapenv:Header/>
                <soapenv:Body>'''

    def soap_footer(self):
        return '''</soapenv:Body>
                </soapenv:Envelope>'''

    def _soap_full(self, id1, id2, close=None):
        if close:
            return f'</{id1}:{id2}>'
        else:
            return f'<{id1}:{id2}>'

    def soap(self, tag, close=None):
        return self._soap_full('v1', tag, close)

    def _soap_helper_full(self, id1, id2, data):
        return f'{self._soap_full(id1, id2)}{data}{self._soap_full(id1, id2, "close")}'

    def soap_helper(self, tag, data):
        return self._soap_helper_full("v1", tag, data)
